# QA Report: US008 — `syntek-graphql-crypto`: GraphQL Encryption Middleware

**Date:** 11/03/2026 **Analyst:** QA Agent ("The Breaker") **Story:** US008 —
`syntek-graphql-crypto` GraphQL Encryption Middleware **Status:** CRITICAL ISSUES FOUND

---

## Summary

The middleware implementation satisfies the acceptance criteria as literally stated and all 59
automated tests pass. However, a hostile code review exposes several security and reliability
vulnerabilities that the tests do not cover: a deliberate auth bypass in the `_is_authenticated`
method, a batch key derivation flaw that uses the wrong encryption key for every field after the
first in a group, information leakage through unredacted error messages, a monkey-patch that mutates
a third-party library's public namespace, and gaps in test coverage around edge cases that an
attacker or misconfigured deployment would exercise immediately.

---

## CRITICAL (Blocks deployment)

### C1 — Auth guard silently allows all requests when `execution_context.context` is absent

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:174-180`

```python
def _is_authenticated(self) -> bool:
    try:
        ctx = self.execution_context.context
        return bool(ctx.user.is_authenticated)
    except Exception:
        return True  # No context — allow (unit-test mode without context)
```

**Description:** Any exception raised while accessing
`execution_context.context.user.is_authenticated` causes `_is_authenticated` to return `True`. This
is not a narrow guard. A `None` context, a context object that does not have a `.user` attribute, an
`AttributeError` on `.is_authenticated`, or any runtime error in custom context middleware all
result in an unauthenticated request being treated as authenticated. The comment "unit-test mode
without context" is the stated justification, but it means the auth guard is trivially defeated in
any deployment where context is misconfigured.

**Attack/failure scenario:** A consumer configures a custom Strawberry context class that raises on
attribute access (e.g. a property that does a failed DB lookup). Every request, authenticated or
not, passes the auth guard. All ciphertext is decrypted and returned. The AC10 acceptance criterion
is met in tests because the mock context object has no errors, but production deployments with any
context error silently expose sensitive data.

**Recommended fix direction:** Narrow the exception handler to catch only `AttributeError` and
`TypeError` and treat all other exceptions as an unauthenticated state (fail-closed). Remove the
permissive fallback comment and replace it with an explicit check for the absence of a context
object before the try/except.

---

### C2 — Batch encryption and decryption use only the key for the first field in the group

**File:**
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:134,164,229,334`

**Description:** In every batch operation — both on the write path and the read path — a single key
is resolved from the first field in the batch group, and that single key is passed to
`encrypt_fields_batch` / `decrypt_fields_batch` for all fields in the group.

Write path (line 229):

```python
first_snake = (
    _camel_to_snake(batch_pairs[0][0])
    if batch_pairs
    else batch_group
)
key = _resolve_key(self._model, first_snake)
```

Read path (line 334):

```python
first_snake = batch_fields[0][1]
key = _resolve_key(self._model, first_snake)
```

The `process_batch_input` helper (line 134) and `process_batch_output` helper (line 164) are
identical in design.

**Description of impact:** The system key naming convention is `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>`,
meaning each field has its own dedicated 32-byte key. When `first_name` and `last_name` are in the
same batch group, the key for `first_name` is used to encrypt/decrypt `last_name` as well.
`last_name` was encrypted with its own key (per the convention) but is decrypted with the
`first_name` key. This will cause a GCM authentication tag mismatch, surfacing as a runtime
decryption error that nulls both fields — after data has been written. More critically, if
`syntek_pyo3.encrypt_fields_batch` accepts a single key and applies it to all fields in the batch,
then all batch-group fields are stored with the same key, violating the per-field key isolation that
the `SYNTEK_FIELD_KEY_*` naming convention implies.

**Attack/failure scenario:** After deployment, every batch-group read fails with a decryption error
because the key used for encryption (the first-field key) differs from the key the consumer
configured for the second and subsequent fields. If `encrypt_fields_batch` re-uses the first key,
all fields are readable but the per-field key rotation described in the README is impossible without
breaking existing ciphertexts.

**Recommended fix direction:** The story, the README, and the key naming convention all imply
per-field key isolation. The batch API design must be reconciled: either the Rust
`encrypt_fields_batch` / `decrypt_fields_batch` functions accept a separate key per field (a
`Vec<(field_name, value, key)>` signature), or the Python middleware must make a separate
`encrypt_field` call per field and only group them logically (one Rust call with all keys inline).
The current implementation has a fundamental mismatch between the stated key convention and the
batch call signature. This needs architectural clarification and a test that verifies each
individual field in a batch group was stored with its own key.

---

### C3 — Encrypt failure re-raises a bare `Exception` with the raw internal error message

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:239-240`

```python
except RuntimeError as exc:
    raise Exception(f"Encryption failed: {exc}") from exc
```

**Description:** When a `RuntimeError` is raised by `syntek_pyo3.encrypt_field` or
`encrypt_fields_batch`, the middleware wraps it in a plain `Exception` with the message from the
Rust layer prepended by `"Encryption failed: "`. Strawberry converts unhandled exceptions into
GraphQL errors and — depending on the `debug` mode of the schema — may include the full message in
the response sent to the client. The Rust error messages (e.g.
`"HSM unavailable — encryption failed"`) or key resolution errors (e.g.
`"Missing encryption key env var: SYNTEK_FIELD_KEY_USER_EMAIL"`) reveal internal infrastructure
details, key naming conventions, and model/field names to the caller.

**Attack/failure scenario:** A client submits a mutation against a field whose key has been unset or
rotated. The response `errors` array contains
`"Encryption failed: Missing encryption key env var: SYNTEK_FIELD_KEY_USER_EMAIL"`. An attacker now
knows the exact environment variable name, the model name (`USER`), and the field name (`EMAIL`).
This is an information disclosure vulnerability under OWASP A05:2021 (Security Misconfiguration).

**Recommended fix direction:** All error messages surfaced to GraphQL clients must be sanitised.
Internal Rust error detail must be logged server-side (at `ERROR` level with the full context) but
the client must receive only a generic, non-identifying message such as
`"An internal error occurred. Please contact support."`. The `MiddlewareError` enum in the Rust
crate already provides structured variants — the Python layer should map each variant to a safe
client-facing string and log the detail internally.

---

## HIGH (Must fix before sign-off)

### H1 — Monkey-patching `strawberry.annotated` in `__init__.py` is unsafe

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/__init__.py:6`

```python
strawberry.annotated = typing.Annotated  # type: ignore[attr-defined]
```

**Description:** The package `__init__.py` mutates the `strawberry` namespace at import time by
injecting `typing.Annotated` as `strawberry.annotated`. This is done so that test and consumer code
can write `strawberry.annotated[str, Encrypted()]` rather than `typing.Annotated[str, Encrypted()]`.
The Strawberry library does not define `strawberry.annotated` as a public API. This patch:

1. Will silently break if Strawberry adds its own `strawberry.annotated` in a future release.
2. Modifies a third-party module's state globally for the entire Python process, affecting any other
   code that imports `strawberry` in the same process after this package is imported.
3. Is not declared in the public API of this package, making it invisible to consumers who do not
   read the `__init__.py`.
4. Has no test verifying that the attribute did not previously exist (a forward-compatibility
   guard).

**Attack/failure scenario:** Strawberry `0.307.2` or later defines `strawberry.annotated` with
different semantics. The patch silently overwrites it at import time. All consumer schemas that rely
on `strawberry.annotated` from either source now use whichever was imported last, potentially
causing subtle type annotation failures or wrong encryption routing that passes all existing tests.

**Recommended fix direction:** Remove the monkey-patch. The correct approach is to export a
convenience alias from `syntek_graphql_crypto` itself (e.g.
`from syntek_graphql_crypto import annotated`) and document that consumers should use
`typing.Annotated` directly. Any test using `strawberry.annotated` should be updated to use
`typing.Annotated`.

---

### H2 — `_build_encrypted_map` is called on every field resolution, walking the entire schema type map each time

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:354-377`

**Description:** `_decrypt_object` calls `_build_encrypted_map(schema)` once per response object.
`_build_encrypted_map` iterates over every type in `graphql_schema.type_map` and every field in each
type to collect `@encrypted` directives. In a schema with many types (typical for a production
Syntek deployment with 21 backend modules registering types), this is an O(T×F) traversal on every
single read response. The result is not cached — not across requests, not across the execution of a
single query, and not even memoised for the duration of a single `on_execute` call.

**Attack/failure scenario:** A query that returns a list of 100 user objects (a pagination result)
will trigger `_build_encrypted_map` 100 times, each walking the entire schema type map. Under modest
load, this will cause measurable latency regression on all read operations. A schema with thousands
of fields (a realistic production schema) amplifies this. There is no test covering performance at
scale.

**Recommended fix direction:** Cache the result of `_build_encrypted_map` at schema initialisation
time (e.g. as a property computed once when the `SchemaExtension` is first used, or via
`functools.lru_cache` keyed on the schema object's identity). The schema's type map does not change
at runtime.

---

### H3 — Auth guard only checks the outer response object; nested encrypted fields on related objects are not guarded

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:262-265`

```python
for _root_key, root_val in data.items():
    if not isinstance(root_val, dict):
        continue
    self._decrypt_object(root_val, is_auth, errors)
```

**Description:** `_process_data` iterates one level into `result.data` and calls `_decrypt_object`
on each top-level value. `_decrypt_object` does not recurse into nested objects. If a GraphQL
resolver returns a type that contains an `@encrypted` field nested inside a related object — e.g.
`user { profile { address { postcode } } }` — the middleware will not reach the nested
`_decrypt_object` call and the ciphertext will pass through to the client unchanged. Similarly, the
auth guard at line 278 will not fire for nested objects.

**Attack/failure scenario:** A query for `{ order { buyer { email } } }` returns raw ciphertext for
`email` because `_decrypt_object` is called on `order` but not recursively on `buyer`. No error is
appended. The client receives ciphertext that it cannot process. This is a functional failure that
also constitutes information leakage of the raw ciphertext format and nonce structure.

**Recommended fix direction:** `_decrypt_object` must recursively descend into all nested dict
values (and lists of dicts) after processing the current object's fields. The recursive call must
carry the same `is_auth` flag and `errors` list. Tests must cover a schema with at least two levels
of nesting.

---

<!-- markdownlint-disable MD013 -->

### H4 — `on_execute` auth guard checks authentication only once and applies it to the entire response, but write-path `resolve` does not check authentication at all

<!-- markdownlint-enable MD013 -->

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:182-242`

**Description:** The write-path `resolve` method intercepts mutation inputs and encrypts them
without any authentication check. An unauthenticated caller can submit mutations with plaintext
values; the middleware will encrypt them and pass ciphertext to the resolver, which will write it to
the database. The auth guard only applies to decryption (read path).

**Attack/failure scenario:** An anonymous client submits a `createUser` mutation. The middleware
encrypts the input and the resolver creates the database record. The unauthenticated write is not
blocked or logged by the middleware. This is a data integrity and access control issue — the
middleware's own auth guard is asymmetric.

**Note:** Whether unauthenticated mutations should be blocked is an architectural decision (Django
permissions or a separate auth middleware may handle this upstream). However, the AC10 acceptance
criterion states "Given an unauthenticated request attempts to resolve an `@encrypted` or
`@encrypted(batch: ...)` field" — which is schema-level agnostic about read vs write. The current
implementation does not enforce this on the write path, and no test covers an unauthenticated
mutation attempt. The discrepancy between the story spec and the implementation must be resolved
with an explicit architectural decision, not silence.

---

### H5 — `syntek.manifest.toml` version (`0.14.0`) does not match the root workspace version (`0.15.0`)

**File:** `rust/syntek-graphql-crypto/syntek.manifest.toml:8`

```toml
version = "0.14.0"
```

**Description:** The root workspace `VERSION` file is at `0.15.0` (per CLAUDE.md "Version: 0.15.0")
and `Cargo.toml` uses `version.workspace = true` to inherit the workspace version. The
`syntek.manifest.toml` hard-codes `0.14.0`. The manifest is what the `syntek add` CLI reads to
determine which crate version to pin in a consumer's `Cargo.toml`. A consumer running
`syntek add syntek-graphql-crypto` today would receive the `0.14.0` crate from the Forgejo registry
rather than the current `0.15.0` crate, pulling in a potentially outdated or non-existent version.

**Attack/failure scenario:** A new consumer installation pins `0.14.0` but the published registry
contains only `0.15.0`. The install fails with a registry resolution error. Alternatively, `0.14.0`
exists and contains an older, unpatched version of the middleware, silently installing a known-buggy
release.

**Recommended fix direction:** The `version` field in `syntek.manifest.toml` must either be kept in
sync with the workspace version (via a CI check or a version bump script) or the `syntek add` CLI
must derive the version from the workspace `Cargo.toml` rather than the manifest. The discrepancy
must be resolved before any publish to the Forgejo registry.

---

## MEDIUM (Fix soon, non-blocking)

### M1 — `_resolve_key` raises `RuntimeError` at request time, not at startup

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:33-42`

**Description:** The README states "Missing keys raise a `RuntimeError` at execution time, not at
startup." This is by design, but it means a misconfigured deployment silently serves successful
responses for all non-encrypted fields and only fails — with a cryptic `RuntimeError` — when the
first request for an encrypted field arrives. In a production deployment with many encrypted fields
across many models, a missing key may go undetected until a specific user action exposes it.

**Recommended fix direction:** The `AppConfig.ready()` hook (referenced in CLAUDE.md as the
validation point for `SYNTEK_*` settings) should validate that all `SYNTEK_FIELD_KEY_*` env vars
referenced by the registered schema are present and correctly formatted at startup, failing loudly
before accepting any traffic. A test should verify that misconfigured startup raises
`ImproperlyConfigured` rather than a runtime error during a request.

---

### M2 — `_camel_to_snake` is applied inconsistently and silently swallows lookup mismatches

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:203-213`

**Description:** In the write-path `resolve` method, kwarg names from the GraphQL request are tried
in their original form, then converted with `_camel_to_snake`. If neither matches a key in
`arg_directives`, the field is silently skipped — it is not encrypted. A naming inconsistency
between the GraphQL camelCase field name and the Python snake_case method argument (e.g. a field
named `homeAddressLine1` resolving to `home_address_line_1` but annotated as `home_address_line1` in
the resolver) will cause the field to pass through as plaintext without any warning, error, or log
entry.

**Attack/failure scenario:** A developer annotates a mutation argument but makes a naming
inconsistency. The argument passes through unencrypted to the ORM. The DB stores plaintext. No error
is raised and no test fails because the existing tests use simple field names with straightforward
conversions.

**Recommended fix direction:** Any `@encrypted`-annotated field that is not successfully located in
`kwargs` during write-path processing should emit a `logger.warning` identifying the unmatched field
name. A test should cover a multi-word camelCase field name with a non-trivial conversion (e.g.
`phoneNumberExtension` → `phone_number_extension`).

---

<!-- markdownlint-disable MD013 -->

### M3 — `process_batch_input` and `process_batch_output` low-level helpers use the first-field key (see C2), and this is also the key used in the `resolve` write path

<!-- markdownlint-enable MD013 -->

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:223-238`

**Description:** This is the direct implementation path exercised by all write-path batch operations
in production (not just the test helpers). The write-path `resolve` method (the real Strawberry
hook) has the same one-key-for-all pattern as the `process_batch_input` helper. Both are affected by
the critical issue C2, but the `resolve` method is the production code path, not just a test helper.
It is called in the same critical path as C2 and is listed here as a separate observation to ensure
the fix addresses both the helpers and the main `resolve` method body.

---

### M4 — Integration tests use SQLite, not PostgreSQL; the story specifies PostgreSQL 18.3

**File:** `packages/backend/syntek-graphql-crypto/tests/test_integration.py:43-57` **File:**
`packages/backend/syntek-graphql-crypto/tests/conftest.py:41-57`

**Description:** The conftest configures Django with
`ENGINE: django.db.backends.sqlite3, NAME: ":memory:"`. The project stack specifies PostgreSQL 18.3
as the database. SQLite and PostgreSQL differ in text encoding, collation, and transaction isolation
behaviour. The integration tests pass in SQLite but are not authoritative evidence that the
middleware works correctly with PostgreSQL. In particular, the AES-256-GCM ciphertext is stored as a
raw `TextField` — PostgreSQL's handling of binary-safe strings in UTF-8 encoding must be verified. A
GCM ciphertext blob stored as base64 is safe; raw binary is not.

**Recommended fix direction:** Integration tests should use `testcontainers-python` with
`PostgreSQL 18.3` (as specified in MEMORY.md as the testing pattern). The in-memory SQLite variant
can remain for fast unit test runs, but at least one integration test suite must run against real
PostgreSQL.

---

### M5 — No test covers the `_build_encrypted_map` returning an empty result (schema without any `@encrypted` fields)

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:354-377`

**Description:** If `_build_encrypted_map` returns an empty dict (e.g. the middleware is installed
on a schema that has no `@encrypted` annotations, or the schema introspection mechanism fails
silently), `_decrypt_object` does nothing. This is the correct behaviour, but there is no test that
verifies the middleware does not error or degrade when applied to a schema with zero encrypted
fields. A consumer who mistakenly removes all annotations will get silent passthrough, not a startup
warning.

---

### M6 — The `on_execute` hook processes `result.data` but does not handle list responses (queries returning lists)

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:262-265`

**Description:** `_process_data` iterates over `data.items()` and only processes values that are
`isinstance(root_val, dict)`. If a top-level query returns a list (e.g. `{ users { email } }` where
`users` resolves to a `list`), the middleware skips it entirely and no decryption occurs. The
frontend receives raw ciphertext for every item in the list.

**Attack/failure scenario:** A query for `{ users { email firstName lastName } }` returns all rows
with ciphertext in every encrypted field. The frontend cannot display the data. Additionally, the
client now has access to ciphertext for multiple users' encrypted fields — not a direct security
breach, but a data quality failure and a ciphertext exposure.

**Recommended fix direction:** `_process_data` must handle both `dict` and `list` top-level values.
When a value is a list, each element must be passed through `_decrypt_object`. Tests must cover a
query that returns a list of objects with encrypted fields.

---

### M7 — `_get_encrypted_args_from_method` silently swallows all exceptions

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:63-88`

```python
    except Exception:
        return {}
```

**Description:** The entire body of `_get_encrypted_args_from_method` is wrapped in a bare
`except Exception: return {}`. If reflection fails for any reason (e.g. the Strawberry internal API
for `"strawberry-definition"` changes in a future version), the method returns an empty dict,
meaning no write-path encryption occurs for any field. The failure is completely invisible — no log,
no error, no indication that all mutations are silently passing plaintext to the ORM.

**Recommended fix direction:** The exception handler must at minimum log a `logger.error` or
`logger.warning` message when it fires, including the field name and parent type that could not be
inspected. Silent no-op on reflection failure is one of the most dangerous patterns in a security
boundary.

---

## LOW / OBSERVATIONS

### L1 — `zip(...) # noqa: B905` suppresses a legitimate warning about unequal-length iterables

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py:235,338`

Both batch zip calls suppress `B905` (`zip` without `strict=True`). If `encrypt_fields_batch` or
`decrypt_fields_batch` returns fewer results than input fields (a bug in the Rust layer), the extra
fields are silently dropped. `zip(strict=True)` (Python 3.10+) would raise a `ValueError` instead of
silently truncating. Given Python 3.14 is in use, `strict=True` should be used and the noqa
suppression removed.

---

### L2 — `pyproject.toml` is missing `syntek-pyo3` as a runtime dependency

**File:** `packages/backend/syntek-graphql-crypto/pyproject.toml`

`syntek_pyo3` is imported directly in `middleware.py` at line 22, but it is not listed in the
`dependencies` array in `pyproject.toml`. A consumer who installs `syntek-graphql-crypto` without
separately installing `syntek-pyo3` will receive an `ImportError` at runtime, not at install time.
The `syntek.manifest.toml` post-install steps do not mention the Rust crate dependency relationship
to the Python package explicitly.

---

### L3 — The `Encrypted.batch` attribute uses `strawberry.UNSET` as the type annotation default but `None` in `__init__`

**File:** `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py:17-20`

```python
batch: str | None = strawberry.UNSET  # type: ignore[assignment]
class-level default: strawberry.UNSET
__init__ default: None
```

The class-level attribute annotation uses `strawberry.UNSET` as the default (with a type ignore
comment to suppress the type mismatch). The `__init__` always sets `self.batch = batch` with a
default of `None`. The class-level attribute is therefore only relevant to Strawberry's directive
introspection machinery, not to the actual value. If Strawberry introspects the class attribute
before calling `__init__`, it sees `UNSET`, not `None`. The `type: ignore[assignment]` comment
suppresses the basedpyright warning that would otherwise flag this inconsistency. A future
Strawberry version that relies on the class-level default for directive argument defaulting could
behave unexpectedly.

---

### L4 — Test count discrepancy between story completion notes, test status file, and actual file

**Story (US008.md line 196):** "55 tests pass ... 56 tests in the test plan; 55 in the green-phase
run — discrepancy in `test_directives.py` split noted in test status file"

**Test status file (US008-TEST-STATUS.md line 8):** "Coverage: 59/59"

**Actual test count analysis:** The test status file summary table shows 13 Rust + 42 Python unit +
4 integration = 59 total, but states "Note: the summary table lists 10 Rust tests; the file contains
13". The story completion notes reference 55 passing tests; the test status shows 59. There are
three separate counts and none agree. While the discrepancy may be explained by tests added during
the green phase, the inconsistency means no authoritative test count exists and the "missing" test
noted in the directives file has not been explicitly resolved.

---

### L5 — `conftest.py` uses `bytes(range(32))` as a test key — a predictable, sequential byte sequence

**File:** `packages/backend/syntek-graphql-crypto/tests/conftest.py:25`

```python
_TEST_KEY_BYTES: bytes = bytes(range(32))  # 32 bytes: 0x00 … 0x1f
```

This key (all bytes `0x00` through `0x1f`) is trivially predictable and violates AES-256 key
strength requirements. While acceptable in tests, if this key were accidentally used in a staging
environment (e.g. seeded via `db seed`), it would provide no security. The comment "Never use a
predictable key in production" is the only guard. A runtime check that the key has sufficient
entropy (e.g. not all-zero, not sequential) should exist in `_resolve_key`, not just in a comment.

---

## Missing Test Scenarios

The following test scenarios are absent from all test files and represent real gaps that could
conceal production failures:

1. **Nested encrypted objects** — a query for `{ user { address { postcode } } }` where `postcode`
   carries `@encrypted`. Current tests only cover one level of nesting.

2. **List-returning queries** — a query for `{ users { email } }` where the resolver returns a list.
   Current tests only cover single-object responses.

3. **Unauthenticated mutation** — a mutation submitted without authentication. The write path has no
   auth guard and no test exercises this path.

4. **Missing key at request time (read path)** — a query where `SYNTEK_FIELD_KEY_*` is unset for a
   field that is being read. The current error handling tests cover Rust-level decryption failures
   but not Python-level key resolution failures during reads.

5. **Batch group with only one field** — a batch group where only one field is present (a degenerate
   batch). The assumption that `batch_fields[0]` exists is not tested for the empty case.

6. **`_get_encrypted_args_from_method` reflection failure** — a resolver where
   `typing.get_type_hints` raises (e.g. a forward reference that cannot be resolved). The silent
   `except Exception: return {}` path is never exercised by any test.

7. **Very large plaintext values** — plaintext inputs larger than expected (e.g. a 10,000-character
   string submitted as an encrypted field value). AES-256-GCM has no practical length limit, but the
   middleware has no size validation and an attacker could use oversized inputs to probe for memory
   or timeout issues.

8. **Same plaintext encrypted twice** — verifying that AES-256-GCM with random nonces produces
   distinct ciphertexts for the same plaintext on repeated writes. The integration test
   `test_different_plaintexts_produce_different_ciphertexts` covers different plaintexts but not the
   same plaintext written twice.

9. **Key rotation scenario** — writing data with key version A, then querying with key version B.
   There is no key versioning mechanism and no test for the failure mode. A consumer rotating a
   `SYNTEK_FIELD_KEY_*` value will immediately break all existing ciphertexts.

10. **Concurrent mutations** — two simultaneous mutations encrypting the same field on the same
    record. The middleware provides no transaction-level isolation guarantees; a race condition
    between encryption and ORM write is not tested.

11. **`@encrypted` on a non-string field** — annotating an `Int` or `Boolean` field with
    `@encrypted`. The middleware assumes string ciphertext values. There is no schema-level
    validation that `@encrypted` is only applied to `String` fields, and no test covers the type
    mismatch.

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to implement fixes for C1 (fail-closed auth guard), C2 (batch key
  resolution), C3 (error message sanitisation), H3 (recursive nested object decryption), H4 (auth
  guard on write path), and M6 (list response handling).
- Run `/syntek-dev-suite:debug` to investigate C2 (batch key usage) — specifically whether
  `syntek_pyo3.encrypt_fields_batch` accepts one key for all fields or one key per field, as the
  Rust-level API contract is not visible in the Python tests.
- Run `/syntek-dev-suite:test-writer` to add tests covering the scenarios listed in the Missing Test
  Scenarios section, particularly items 1 (nested objects), 2 (list responses), 3 (unauthenticated
  mutations), 6 (reflection failure path), and 11 (non-string `@encrypted` field).
- Run `/syntek-dev-suite:completion` to update QA status for US008 once critical issues are
  resolved.
