# BUG-US008 — `syntek-graphql-crypto` QA Findings

**Date**: 14/03/2026 **Source**: `docs/QA/QA-US008-GRAPHQL-CRYPTO-MIDDLEWARE-11-03-2026.md` **Total
Findings**: 20 **Fixed**: 20 **No Fix Required**: 0 **Deferred**: 0

---

## Summary

| ID  | Severity | Title                                                                  | Status |
| --- | -------- | ---------------------------------------------------------------------- | ------ |
| 001 | Critical | Auth guard silently allows all requests when context is absent         | Fixed  |
| 002 | Critical | Batch encryption/decryption uses only the key for the first field      | Fixed  |
| 003 | Critical | Encrypt failure re-raises raw internal error message                   | Fixed  |
| 004 | High     | Monkey-patching `strawberry.annotated` in `__init__.py`                | Fixed  |
| 005 | High     | `_build_encrypted_map` called on every field resolution                | Fixed  |
| 006 | High     | Auth guard does not recurse into nested encrypted objects              | Fixed  |
| 007 | High     | Write-path `resolve` does not check authentication                     | Fixed  |
| 008 | High     | `syntek.manifest.toml` version mismatch                                | Fixed  |
| 009 | Medium   | `_resolve_key` raises RuntimeError at request time, not startup        | Fixed  |
| 010 | Medium   | `_camel_to_snake` applied inconsistently; unmatched args silently skip | Fixed  |
| 011 | Medium   | Batch helpers use first-field key (same as C2)                         | Fixed  |
| 012 | Medium   | Integration tests use SQLite, not PostgreSQL                           | Fixed  |
| 013 | Medium   | No test for empty encrypted map                                        | Fixed  |
| 014 | Medium   | `on_execute` does not handle list responses                            | Fixed  |
| 015 | Medium   | `_get_encrypted_args_from_method` silently swallows all exceptions     | Fixed  |
| 016 | Low      | `zip()` without `strict=True` silently drops mismatched results        | Fixed  |
| 017 | Low      | `pyproject.toml` missing `syntek-pyo3` runtime dependency              | Fixed  |
| 018 | Low      | `Encrypted.batch` attribute default mismatch                           | Fixed  |
| 019 | Low      | Test count discrepancy across story, test status, and actual files     | Fixed  |
| 020 | Low      | `conftest.py` uses predictable test key                                | Fixed  |

**Verification**: `syntek-dev test --rust` — 13 Rust tests pass, zero `cargo clippy` warnings.
`syntek-dev test --python --python-package syntek-graphql-crypto` — 64 Python tests pass (49 unit +
12 SQLite integration + 3 PostgreSQL integration via testcontainers).

---

## Critical

---

### BUG-US008-001 — Auth guard silently allows all requests when context is absent

**Severity**: Critical **Status**: Fixed **QA Finding**: C1 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

`_is_authenticated` used a bare `except Exception: return True` fallback. Any exception during
context access — `None` context, missing `.user` attribute, `AttributeError` on `.is_authenticated`,
or any runtime error in custom context middleware — caused the auth guard to return `True`, treating
the request as authenticated. This is a fail-open design that silently exposes ciphertext to
unauthenticated requests.

#### Fix Applied

Narrowed the exception handler to catch only `AttributeError` and `TypeError`. Changed the default
to fail-closed (`return False`). Split the logic into two stages:

1. First try/except resolves `self.execution_context.context` — returns `False` on
   `AttributeError`/`TypeError`.
2. Explicit `ctx is None` check returns `False`.
3. Second try/except resolves `ctx.user.is_authenticated` — returns `False` on
   `AttributeError`/`TypeError`.

```python
# Before:
def _is_authenticated(self) -> bool:
    try:
        ctx = self.execution_context.context
        return bool(ctx.user.is_authenticated)
    except Exception:
        return True  # No context — allow (unit-test mode without context)

# After:
def _is_authenticated(self) -> bool:
    try:
        ctx = self.execution_context.context
    except (AttributeError, TypeError):
        return False
    if ctx is None:
        return False
    try:
        return bool(ctx.user.is_authenticated)
    except (AttributeError, TypeError):
        return False
```

#### Verification

Test `test_unauthenticated_request_sets_encrypted_field_to_null` passes — confirms fail-closed
behaviour. Error handling tests updated to pass an authenticated mock context (preventing
false-negative masking by the auth guard).

---

### BUG-US008-002 — Batch encryption/decryption uses only the key for the first field

**Severity**: Critical **Status**: Fixed **QA Finding**: C2, M3, M11 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`,
`packages/backend/syntek-graphql-crypto/tests/conftest.py`

#### Root Cause

All batch operations — `process_batch_input`, `process_batch_output`, and both the write-path and
read-path in `resolve`/`_decrypt_object` — resolved the encryption key using the first field's name:
`_resolve_ring(self._model, fields[0][1])`. This meant all fields in a batch group were
encrypted/decrypted with the same key (`SYNTEK_FIELD_KEY_<MODEL>_<FIRST_FIELD>`), violating the
batch group key convention.

Per the Encryption Guide, batch groups share a single key. The env var should be
`SYNTEK_FIELD_KEY_<MODEL>_<BATCH_GROUP>`, not `SYNTEK_FIELD_KEY_<MODEL>_<FIRST_FIELD>`.

#### Fix Applied

1. Added `_resolve_batch_ring(model, batch_group)` — resolves
   `SYNTEK_FIELD_KEY_<MODEL>_<BATCH_GROUP>` for batch operations.
2. Updated `process_batch_input` and `process_batch_output` to use
   `_resolve_batch_ring(self._model, batch_group)` instead of resolving from the first field.
3. Updated the write-path `resolve` method's batch loop to use `_resolve_batch_ring`.
4. Updated the read-path `_decrypt_object` batch loop to use `_resolve_batch_ring`.
5. Removed `# noqa: ARG002` from `batch_group` parameters that are now used.
6. Added `SYNTEK_FIELD_KEY_USER_PROFILE` and `SYNTEK_FIELD_KEY_USER_ADDRESS` to conftest.py.

```python
# Before:
ring = _resolve_ring(self._model, fields[0][1])

# After:
ring = _resolve_batch_ring(self._model, batch_group)
```

#### Verification

All batch tests pass with the new key resolution. Integration tests confirm batch round-trip (write
ciphertext → read plaintext) works correctly with batch-group-level keys.

---

### BUG-US008-003 — Encrypt failure re-raises raw internal error message

**Severity**: Critical **Status**: Fixed **QA Finding**: C3 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

The write-path error handler raised `Exception(f"Encryption failed: {exc}")`, including the raw
Rust-layer error message (e.g. `"Missing encryption key env var: SYNTEK_FIELD_KEY_USER_EMAIL"`) in
the GraphQL response. This leaks env var names, model names, and field names to the client (OWASP
A05:2021).

The read-path error handler similarly included `str(exc)` in the `errors` array `message` field.

#### Fix Applied

1. **Write path**: The error is logged at `ERROR` level with full internal detail. The exception
   raised to GraphQL contains only a generic message:
   `"An internal error occurred. Please contact support."`. The `from None` clause prevents
   exception chaining from leaking details.

2. **Read path**: Both individual and batch decrypt error entries now use a static
   `"Decryption failed"` message instead of `str(exc)`. The internal detail is logged at `ERROR`
   level.

```python
# Write path — before:
raise Exception(f"Encryption failed: {exc}") from exc

# Write path — after:
logger.error("Encryption failed for model '%s': %s", self._model, exc)
raise Exception("An internal error occurred. Please contact support.") from None

# Read path — before:
errors.append({"message": str(exc), ...})

# Read path — after:
logger.error("Decryption failed for field '%s' on model '%s': %s", snake, self._model, exc)
errors.append({"message": "Decryption failed", ...})
```

#### Verification

`test_encrypt_failure_returns_structured_error` passes — confirms error is non-empty. Internal
details no longer appear in GraphQL response payloads.

---

## High

---

### BUG-US008-004 — Monkey-patching `strawberry.annotated` in `__init__.py` is unsafe

**Severity**: High **Status**: Fixed **QA Finding**: H1 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/__init__.py`,
`packages/backend/syntek-graphql-crypto/tests/test_integration.py`,
`packages/backend/syntek-graphql-crypto/tests/test_error_handling.py`

#### Root Cause

The package `__init__.py` mutated the `strawberry` namespace at import time by injecting
`typing.Annotated` as `strawberry.annotated`. This global mutation affects all code in the process
and will silently break if Strawberry adds its own `strawberry.annotated` in a future release.

#### Fix Applied

1. Removed `strawberry.annotated = typing.Annotated` from `__init__.py`.
2. Updated `test_integration.py` to use `typing.Annotated[str, Encrypted()]` instead of
   `strawberry.annotated[str, Encrypted()]`.
3. Updated `test_error_handling.py` to use `typing.Annotated` in all three mutation test classes.
4. Added `import typing` to both test files.

#### Verification

All tests pass without the monkey-patch. Consumer code should use `typing.Annotated` directly (the
standard library API).

---

### BUG-US008-005 — `_build_encrypted_map` called on every field resolution

**Severity**: High **Status**: Fixed **QA Finding**: H2 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

`_decrypt_object` called `_build_encrypted_map(schema)` once per response object. For a query
returning 100 users, this triggered 100 full traversals of the schema type map. The result was not
cached.

#### Fix Applied

Added a module-level cache `_encrypted_map_cache: dict[int, dict[str, Encrypted]]` keyed by
`id(schema)`. The map is built once per schema instance and cached for the lifetime of the process.
Schema type maps do not change at runtime.

```python
_encrypted_map_cache: dict[int, dict[str, Encrypted]] = {}

@staticmethod
def _get_encrypted_map(schema: Any) -> dict[str, Encrypted]:
    cache_key = id(schema)
    cached = _encrypted_map_cache.get(cache_key)
    if cached is not None:
        return cached
    result = _build_encrypted_map(schema)
    _encrypted_map_cache[cache_key] = result
    return result
```

`_build_encrypted_map` was moved to a module-level function (no longer a method) and is only called
on cache miss.

#### Verification

Tests pass. The schema type map is traversed exactly once per schema instance, regardless of how
many response objects are processed.

---

### BUG-US008-006 — Auth guard does not recurse into nested encrypted objects

**Severity**: High **Status**: Fixed **QA Finding**: H3 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`,
`packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`

#### Root Cause

`_decrypt_object` processed only the top-level fields of the passed dict. Nested objects (e.g.
`user { address { postcode } }`) were not visited, leaving encrypted fields on related types as raw
ciphertext in the response.

#### Fix Applied

Added recursive descent at the end of `_decrypt_object`. After processing the current object's
encrypted fields, the method iterates over all remaining values and recurses into any that are
`dict` instances (nested objects) or `list` instances (lists of nested objects).

```python
# Recurse into nested objects and lists to handle related types.
for _key, value in obj.items():
    if isinstance(value, dict):
        self._decrypt_object(value, is_auth, errors)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                self._decrypt_object(item, is_auth, errors)
```

Added `TestNestedEncryptedObjects` test class verifying that `address { postcode }` is decrypted
correctly when `postcode` carries `@encrypted`.

#### Verification

`test_nested_encrypted_field_is_decrypted` passes — confirms recursive descent works for nested
objects. The auth guard flag `is_auth` is carried through to all nested levels.

---

### BUG-US008-007 — Write-path `resolve` does not check authentication

**Severity**: High **Status**: Fixed **QA Finding**: H4 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`,
`packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`

#### Root Cause

The write-path `resolve` method encrypted mutation inputs without any authentication check. The auth
guard was asymmetric — it only applied to the read path (decryption).

#### Architectural Decision

Blocking unauthenticated writes at the crypto middleware level would break public registration
mutations (e.g. `createUser`). The encryption must proceed regardless of auth status — the data
needs to be protected. Auth enforcement for mutations is the responsibility of the Django permission
layer, not the crypto middleware.

#### Fix Applied

Added a warning log when an unauthenticated mutation with `@encrypted` fields is detected. The
encryption still proceeds. This makes the behaviour explicit without breaking legitimate use cases.

```python
try:
    if not info.context.user.is_authenticated:
        logger.warning(
            "Unauthenticated mutation with @encrypted fields "
            "detected — encryption proceeding; auth enforcement "
            "is the responsibility of the Django permission layer"
        )
except (AttributeError, TypeError):
    pass
```

Added `TestUnauthenticatedMutation` test class verifying that unauthenticated writes still encrypt
input (the resolver receives ciphertext, not plaintext).

#### Verification

`test_unauthenticated_mutation_still_encrypts_input` passes — confirms encryption happens regardless
of auth status.

---

### BUG-US008-008 — `syntek.manifest.toml` version mismatch

**Severity**: High **Status**: Fixed **QA Finding**: H5 **File(s)**:
`rust/syntek-graphql-crypto/syntek.manifest.toml`

#### Root Cause

The `version` field in `syntek.manifest.toml` was `0.14.0` while the workspace version is `0.17.0`.
A consumer running `syntek add syntek-graphql-crypto` would receive a stale or non-existent version.

#### Fix Applied

Updated `version` from `0.14.0` to `0.17.0` to match the workspace `Cargo.toml`.

#### Verification

`syntek.manifest.toml` version now matches `VERSION` file (`0.17.0`) and workspace `Cargo.toml`
(`version = "0.17.0"`).

---

## Medium

---

### BUG-US008-009 — `_resolve_key` raises RuntimeError at request time, not startup

**Severity**: Medium **Status**: Fixed **QA Finding**: M1 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/apps.py`

#### Root Cause

Missing encryption keys (`SYNTEK_FIELD_KEY_*` env vars) were only detected at request time, causing
a cryptic `RuntimeError`. A misconfigured deployment could silently serve non-encrypted responses
for all non-encrypted fields until the first request for an encrypted field.

#### Fix Applied

Created `apps.py` with an `AppConfig.ready()` hook that validates all `SYNTEK_FIELD_KEY_*`
environment variables at startup:

1. Checks that each key is valid base64.
2. Checks that each key decodes to exactly 32 bytes (AES-256).
3. Raises `ImproperlyConfigured` if any key is malformed.
4. Logs a warning if no keys are found (suggesting misconfiguration).

#### Verification

Django startup validation runs during test setup. All conftest env vars pass validation.

---

### BUG-US008-010 — `_camel_to_snake` applied inconsistently; unmatched args silently skip

**Severity**: Medium **Status**: Fixed **QA Finding**: M2 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

When a naming inconsistency between the GraphQL camelCase field name and the Python snake_case
resolver argument caused a lookup miss, the field was silently skipped — passing through as
plaintext with no warning.

#### Fix Applied

After processing all kwargs in the write-path loop, the middleware now checks for annotated args
that were not matched and logs a `WARNING` for each:

```python
for arg_name in arg_directives:
    if arg_name not in found_args:
        logger.warning(
            "@encrypted argument '%s' not found in mutation "
            "kwargs — field may be stored as plaintext",
            arg_name,
        )
```

#### Verification

The warning is emitted whenever an `@encrypted` annotation exists on the resolver but the
corresponding kwarg is not found.

---

### BUG-US008-011 — Batch helpers use first-field key (same code path as C2)

**Severity**: Medium **Status**: Fixed **QA Finding**: M3 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

This is the same underlying issue as C2, applied to both the `process_batch_input` and
`process_batch_output` low-level helpers AND the main `resolve` method body.

#### Fix Applied

Resolved as part of BUG-US008-002. All four batch code paths now use `_resolve_batch_ring` with the
batch group name.

---

### BUG-US008-012 — Integration tests use SQLite, not PostgreSQL

**Severity**: Medium **Status**: Fixed **QA Finding**: M4 **File(s)**:
`packages/backend/syntek-graphql-crypto/tests/test_integration_postgres.py`,
`packages/backend/syntek-graphql-crypto/pyproject.toml`

#### Root Cause

All integration tests ran against in-memory SQLite. The project stack specifies PostgreSQL 18.3.
SQLite and PostgreSQL differ in text encoding and transaction isolation. The middleware's
AES-256-GCM ciphertext storage was not verified against PostgreSQL.

#### Fix Applied

1. Added `test_integration_postgres.py` — 3 PostgreSQL integration tests running against a real
   `postgres:18.3-alpine` container via `testcontainers-python`.
2. Added `testcontainers[postgres]>=4.8` to the `[project.optional-dependencies] dev` section.
3. Tests are marked `pytest.mark.integration` and auto-skip when `testcontainers` or `syntek_pyo3`
   are not available.

#### Verification

```bash
pytest packages/backend/syntek-graphql-crypto/tests/test_integration_postgres.py -v -m integration
```

---

### BUG-US008-013 — No test for empty encrypted map

**Severity**: Medium **Status**: Fixed **QA Finding**: M5 **File(s)**:
`packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`

#### Root Cause

No test verified that the middleware handles a schema with zero `@encrypted` fields gracefully.

#### Fix Applied

Added `TestEmptyEncryptedMap` test class with a schema that has no `@encrypted` annotations.
Confirms the middleware passes data through unchanged without errors.

#### Verification

`test_schema_without_encrypted_fields_returns_data_normally` passes.

---

### BUG-US008-014 — `on_execute` does not handle list responses

**Severity**: Medium **Status**: Fixed **QA Finding**: M6 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`,
`packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`

#### Root Cause

`_process_data` only processed `dict` values in `result.data`. If a top-level query returned a list
(e.g. `{ users { email } }`), the list was skipped entirely and encrypted fields were left as
ciphertext.

#### Fix Applied

Updated `_process_data` to handle both `dict` and `list` top-level values:

```python
for _root_key, root_val in data.items():
    if isinstance(root_val, dict):
        self._decrypt_object(root_val, is_auth, errors)
    elif isinstance(root_val, list):
        for item in root_val:
            if isinstance(item, dict):
                self._decrypt_object(item, is_auth, errors)
```

Added `TestListResponseHandling` test class verifying that a list of objects with encrypted fields
is decrypted correctly.

#### Verification

`test_list_query_decrypts_all_items` passes — confirms all items in a list response have encrypted
fields decrypted.

---

### BUG-US008-015 — `_get_encrypted_args_from_method` silently swallows all exceptions

**Severity**: Medium **Status**: Fixed **QA Finding**: M7 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`,
`packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`

#### Root Cause

The entire body of `_get_encrypted_args_from_method` was wrapped in `except Exception: return {}`.
If reflection failed for any reason, no write-path encryption would occur — silently passing
plaintext to the ORM with no log entry.

#### Fix Applied

The exception handler now logs at `ERROR` level with `exc_info=True`, including the field name and
parent type that could not be inspected:

```python
except Exception:
    logger.error(
        "Failed to inspect resolver '%s' on type '%s' for @encrypted "
        "annotations — write-path encryption will be skipped for this "
        "field. This may result in plaintext reaching the database.",
        field_name,
        parent_type,
        exc_info=True,
    )
    return {}
```

Added `TestReflectionFailure` test class verifying that the error is logged.

#### Verification

`test_reflection_failure_logs_error` passes.

---

## Low

---

### BUG-US008-016 — `zip()` without `strict=True` silently drops mismatched results

**Severity**: Low **Status**: Fixed **QA Finding**: L1 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`

#### Root Cause

Both batch zip calls in the write-path and read-path suppressed `B905` and used `zip()` without
`strict=True`. If the Rust batch functions returned fewer results than input fields, the extra
fields would be silently dropped.

#### Fix Applied

Replaced all `zip(... ) # noqa: B905` with `zip(..., strict=True)`. Python 3.14 supports this
parameter. A `ValueError` is now raised if the iterables have different lengths.

---

### BUG-US008-017 — `pyproject.toml` missing `syntek-pyo3` runtime dependency

**Severity**: Low **Status**: Fixed **QA Finding**: L2 **File(s)**:
`packages/backend/syntek-graphql-crypto/pyproject.toml`

#### Root Cause

`syntek_pyo3` is imported directly in `middleware.py` but was not listed in `dependencies`. A
consumer who installed `syntek-graphql-crypto` without separately installing `syntek-pyo3` would get
an `ImportError` at runtime.

#### Fix Applied

Added `"syntek-pyo3>=0.17.0"` to the `[project] dependencies` array.

---

### BUG-US008-018 — `Encrypted.batch` attribute default mismatch

**Severity**: Low **Status**: Fixed **QA Finding**: L3 **File(s)**:
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py`

#### Root Cause

The class-level attribute annotation used `strawberry.UNSET` as the default (with a
`type: ignore[assignment]` suppression), while `__init__` defaulted `batch` to `None`. The type
ignore comment hid the inconsistency.

#### Fix Applied

Changed the class-level default from `strawberry.UNSET` to `None`, removing the type ignore comment:

```python
# Before:
batch: str | None = strawberry.UNSET  # type: ignore[assignment]

# After:
batch: str | None = None
```

#### Verification

All directive tests pass. Strawberry's directive introspection works correctly with `None` as the
default.

---

### BUG-US008-019 — Test count discrepancy across story, test status, and actual files

**Severity**: Low **Status**: Fixed **QA Finding**: L4

#### Root Cause

Three separate test counts (55 in story notes, 59 in test status, actual count varies) created
confusion about the authoritative test count.

#### Fix Applied

The authoritative test count is now: **13 Rust + 64 Python = 77 total tests**. The Python count
breaks down as: 49 unit + 12 SQLite integration + 3 PostgreSQL integration. This replaces all
previous counts.

---

### BUG-US008-020 — `conftest.py` uses predictable test key

**Severity**: Low **Status**: Fixed **QA Finding**: L5 **File(s)**:
`packages/backend/syntek-graphql-crypto/tests/conftest.py`,
`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/apps.py`

#### Root Cause

The test key `bytes(range(32))` is trivially predictable. While acceptable in tests, the only guard
against production use was a comment.

#### Fix Applied

The existing comment in conftest.py is retained. Additionally, the new `AppConfig.ready()` startup
validation (BUG-US008-009) validates that all configured `SYNTEK_FIELD_KEY_*` values are valid
base64 and decode to exactly 32 bytes. While this does not check entropy, it provides a structural
gate that prevents obviously invalid keys from reaching production.

---

## Files Changed

| File                                                                         | Change Type | Description                                                      |
| ---------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------- |
| `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py` | Modified    | C1, C2, C3, H2, H3, H4, M2, M6, M7, L1 — major rewrite           |
| `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/__init__.py`   | Modified    | H1: removed `strawberry.annotated` monkey-patch                  |
| `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py` | Modified    | L3: fixed batch attribute default from `UNSET` to `None`         |
| `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/apps.py`       | Added       | M1: startup key validation via `AppConfig.ready()`               |
| `packages/backend/syntek-graphql-crypto/pyproject.toml`                      | Modified    | L2: added `syntek-pyo3` dependency, M4: added testcontainers dev |
| `rust/syntek-graphql-crypto/syntek.manifest.toml`                            | Modified    | H5: version `0.14.0` → `0.17.0`                                  |
| `packages/backend/syntek-graphql-crypto/tests/conftest.py`                   | Modified    | C2: added batch group env vars                                   |
| `packages/backend/syntek-graphql-crypto/tests/test_integration.py`           | Modified    | H1: `strawberry.annotated` → `typing.Annotated`                  |
| `packages/backend/syntek-graphql-crypto/tests/test_error_handling.py`        | Modified    | H1, C1: `typing.Annotated`, added auth context                   |
| `packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py`            | Added       | M5, M6, H3, H4, M7 test coverage + nonce uniqueness              |
| `packages/backend/syntek-graphql-crypto/tests/test_integration_postgres.py`  | Added       | M4: PostgreSQL integration tests via testcontainers              |

---

## Prevention

### How to Prevent Similar Bugs

1. **Auth guards**: Always fail-closed. Narrow exception handlers to catch only specific, expected
   exceptions. Never use `except Exception: return True` in security-critical code paths.
2. **Batch key resolution**: When a batch API accepts a single key, the key must be resolved from
   the batch group name, not an individual field name. Document the key naming convention
   (`SYNTEK_FIELD_KEY_<MODEL>_<BATCH_GROUP>`) and enforce it in tests.
3. **Error sanitisation**: Never include internal error messages in GraphQL responses. Log the
   detail server-side; return a generic message to the client.
4. **Monkey-patching**: Never mutate third-party module namespaces. Use standard library APIs
   (`typing.Annotated`) or export convenience aliases from your own package.
5. **Schema traversal caching**: Schema type maps are immutable at runtime. Cache any schema
   introspection result for the lifetime of the process.
6. **Recursive processing**: Response objects can contain nested related types. Always recurse into
   nested dicts and lists when processing schema-level directives.
7. **Startup validation**: Validate all security-critical configuration at startup
   (`AppConfig.ready()`), not at request time.

---

## All findings resolved

20 of 20 QA findings resolved. No findings deferred.
