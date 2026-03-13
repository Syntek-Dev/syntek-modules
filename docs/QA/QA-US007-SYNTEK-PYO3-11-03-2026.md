# QA Report: US007 — syntek-pyo3: PyO3 Django Bindings

**Date:** 11/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US007 — `syntek-pyo3`: PyO3
Django Bindings **Branch:** `us007/syntek-pyo3` **Status:** ISSUES FOUND

---

## Summary

The `syntek-pyo3` crate provides PyO3 bindings that expose `syntek-crypto` to Django and implements
the `EncryptedField` / `EncryptedFieldDescriptor` model types. The core Rust cryptographic
implementation is sound and the automated test suite is largely well-constructed. However, a number
of significant issues were found: a hard format-incompatibility between the unversioned
`encrypt_field` API and the versioned ciphertext format (US076) that will silently break future key
rotation; a missing `None`/`NULL` guard in `EncryptedField.pre_save` that would allow a null save to
bypass the plaintext guard; error-type confusion at the PyO3 boundary that conflates all crypto
failures with `PyValueError`; missing plaintext zeroisation in the Python binding layer; and a
meaningful gap in test coverage (no integration test with an actual PostgreSQL column). Version skew
across three manifest files is also a live consistency hazard.

---

## CRITICAL (Blocks deployment)

### C1 — `EncryptedField.pre_save` crashes on `None` / `NULL` field value

**File:** `rust/syntek-pyo3/src/lib.rs:207–212`

**Description:** `pre_save` unconditionally calls
`instance.getattr(self.attname.as_str())?.extract::<String>()?` with no guard for a `None` value.
When a model instance has a nullable `EncryptedField` column saved with a `None` / Python `None`
value (e.g. an optional email that has not been set), `.extract::<String>()` will raise a
`TypeError` from PyO3 (`expected str, got NoneType`), not a `ValidationError`. This is a crash path,
not a controlled rejection.

**Impact:** Any model that declares an optional encrypted field (e.g.
`EncryptedField(null=True, blank=True)`) will raise an unhandled `TypeError` on save rather than
either accepting `NULL` cleanly or raising a `ValidationError`. Depending on the Django version and
transaction state, this may also leave the database in a partially-saved state.

**Reproduce:** Create a Django model with `email = EncryptedField(null=True)`. Save an instance
without setting `email`. Django calls `pre_save` on the field. `instance.email` is `None`. PyO3
attempts to extract a `String`, fails with `TypeError`.

**Recommended fix direction:** `pre_save` must check whether the extracted value is `None` before
attempting the string extraction and validation. If the field is nullable and the value is `None`,
the method should return the Python `None` object directly without calling `validate`. If the field
is non-nullable, `None` should raise a `ValidationError` rather than a `TypeError`.

---

<!-- markdownlint-disable MD013 -->

### C2 — Format incompatibility: unversioned `encrypt_field` produces ciphertexts that are structurally indistinguishable from versioned ciphertexts, but are not

<!-- markdownlint-enable MD013 -->

**File:** `rust/syntek-crypto/src/lib.rs:90–122`, `rust/syntek-crypto/src/key_versioning.rs:144–181`

**Description:** `encrypt_field` (unversioned) produces:
`base64( nonce(12) || ciphertext || tag(16) )` — minimum 28 bytes decoded. `encrypt_versioned`
(US076 key-rotation API) produces: `base64( version(2) || nonce(12) || ciphertext || tag(16) )` —
minimum 30 bytes decoded.

`EncryptedField.is_valid_ciphertext_format` accepts any base64ct-encoded blob with decoded length

> = 28 bytes. It therefore accepts both formats. There is no discriminator in the stored ciphertext
> to indicate which format it is. When the system later introduces key rotation via
> `decrypt_versioned`, it will attempt to read bytes 0–1 as a key version and bytes 2–14 as a nonce
> from an unversioned ciphertext, resulting in silent GCM tag failure or, worse, accidental
> decryption of a ciphertext produced under a different key if the first two bytes of the nonce
> happen to match a valid version.

The PyO3 layer (US007) exposes only the unversioned API. US076 (key versioning) is already in the
codebase. Any data written through the unversioned API is permanently incompatible with the
versioned rotation path without a migration.

**Impact:** Data written through `encrypt_field` (US007 API) cannot be rotated using
`decrypt_versioned` without failing. If both APIs are used in production (which is very likely,
because US076 extends the same module), all unversioned rows silently fail decryption under the
key-rotation path. This is a data integrity and operational incident risk at scale.

**Reproduce:**

1. Call `encrypt_field("secret", key, "User", "email")` → stores unversioned ciphertext.
2. Later, call `decrypt_versioned(stored_ciphertext, ring, "User", "email")` — this reads bytes 0–1
   as a key version, finds no matching ring entry (or worse, an accidental match), and the GCM tag
   fails.

**Recommended fix direction:** Determine whether the PyO3 API should exclusively expose the
versioned path. If key rotation is in scope for the ecosystem (it clearly is, given
`key_versioning.rs`), the unversioned `encrypt_field` and `decrypt_field` should not be exposed to
Python at all, or should be explicitly documented as "migration-incompatible" with a clearly visible
deprecation notice in the manifests and post-install steps. The PyO3 layer should expose
`encrypt_versioned` / `decrypt_versioned` via a `KeyRing` Python object, or the two ciphertext
formats must be made distinguishable by a reliable prefix or magic bytes.

---

## HIGH (Must fix before sign-off)

### H1 — Plaintext is not zeroised after use at the PyO3 boundary

**File:** `rust/syntek-pyo3/src/lib.rs:74–81`

**Description:** `encrypt_field` receives a `&str` plaintext. In Rust, `&str` is a reference into
memory owned by the Python interpreter (via PyO3's string borrowing). After the function returns,
PyO3 releases the borrow but the Python `str` object continues to live on the Python heap, owned and
garbage-collected by CPython, and will not be overwritten. The `decrypt_field` return value is a
`String` constructed from UTF-8 bytes returned by the AES-GCM cipher. This `String` is returned to
Python as a new Python `str` object, and the Rust `String` is then dropped — but `String::drop` does
not zero the heap allocation. The recovered plaintext therefore lives in process memory (both on the
Rust heap briefly, and then on the CPython heap indefinitely) until the GC collects it.

The `CLAUDE.md` security table explicitly lists `zeroize` (OWASP Cryptographic Storage) as a
required algorithm. The Rust layer uses `zeroize` in `syntek-crypto` for key material, but the
plaintext returned through the PyO3 boundary is not zeroised before the Rust `String` is dropped.

**Impact:** In a long-running Django process (Gunicorn / uWSGI worker), decrypted plaintext values
may remain in the process heap for the duration of the worker's lifetime. A memory-inspection attack
(via a memory-safety vulnerability elsewhere, a core dump, or `ptrace`) could recover plaintext
values from memory.

**Recommended fix direction:** Use a `Zeroizing<String>` wrapper from the `zeroize` crate for the
intermediate Rust `String` holding the recovered plaintext before it is handed to PyO3. This zeroes
the heap allocation on `drop`. Document in the module that plaintext that crosses the PyO3 boundary
into Python can no longer be zeroised from the Rust side, and advise consumer teams not to hold
decrypted values in long-lived Python variables.

---

<!-- markdownlint-disable MD013 -->

### H2 — All crypto failures map to `PyValueError` — `DecryptionError` and `BatchDecryptionError` are Rust-only types, never raised in Python

<!-- markdownlint-enable MD013 -->

**File:** `rust/syntek-pyo3/src/lib.rs:65–67`, `lib.rs:79–81`

**Description:** `crypto_err_to_py` converts every `CryptoError` variant to a generic
`pyo3::exceptions::PyValueError`. The story defines and the completion verification lists
`DecryptionError` and `BatchDecryptionError` as types that "PyO3 can map to Python exceptions".
However, neither type is registered as a Python exception class (no `pyo3::create_exception!` macro,
no `PyErr::new::<DecryptionErrorClass, _>`) — they exist only as Rust structs exposed for Rust-level
integration tests (compile-time checks). Any Python caller that tries to catch
`syntek_pyo3.DecryptionError` will find it does not exist as a Python exception class. The Python
tests catch only `Exception` (the base class), masking this gap.

**Impact:** Callers (Django views, GraphQL middleware) that attempt specific exception handling of
`syntek_pyo3.DecryptionError` will fail with `AttributeError` (no such attribute) or catch the wrong
exception type. This removes the ability to distinguish decryption failures from other `ValueError`
conditions in error-handling logic.

**Reproduce:** After `maturin develop`:

```python
from syntek_pyo3 import DecryptionError
```

This will raise `ImportError` or `AttributeError` because `DecryptionError` is not added to the
module in the `#[pymodule]` block and is not a Python exception class.

**Recommended fix direction:** Either register `DecryptionError` and `BatchDecryptionError` as
genuine Python exception classes using PyO3's `pyo3::create_exception!` macro and add them to the
module's export list, or explicitly document in the story completion that these types are
Rust-internal only and remove the misleading completion-verification claim. Matching them to
`PyValueError` is acceptable only if that is the stated design, and the claim in the completion
checklist must be corrected.

---

### H3 — Version skew across three manifest / version files

**File:** `rust/syntek-pyo3/pyproject.toml:6`, `rust/syntek-pyo3/syntek.manifest.toml:9`,
`Cargo.toml:12`

**Description:** Three files declare three different versions for the same crate:

- Root `Cargo.toml` workspace version: `0.15.0`
- `rust/syntek-pyo3/pyproject.toml` (Python wheel): `0.12.1`
- `rust/syntek-pyo3/syntek.manifest.toml` (CLI installer): `0.14.0`

`syntek-pyo3`'s `Cargo.toml` uses `version.workspace = true` (resolves to `0.15.0`), yet the Python
wheel manifest (`pyproject.toml`) and the installer manifest record different, older versions. A
consumer running `syntek add syntek-pyo3` would pin `0.14.0` (from the manifest) in their
`Cargo.toml`, but the wheel produced by `maturin build` at that revision would be labelled `0.12.1`
in `pyproject.toml`. Neither matches the workspace version `0.15.0`.

**Impact:** Any consumer that follows the post-install steps will install a wheel whose metadata
version does not match the Cargo crate version they pinned. Dependency auditing tools (`pip audit`,
`cargo audit`) will report inconsistent version information. More critically, if a security patch
bumps the workspace version, the old manifest and pyproject versions create a false impression that
the installed wheel is out of date.

**Recommended fix direction:** Ensure `syntek.manifest.toml` and `pyproject.toml` are updated in
lockstep with the workspace version. The VERSIONING-GUIDE should mandate a check across all three
version locations as part of the version-bump procedure for any Rust crate that produces a Python
wheel.

---

### H4 — `EncryptedFieldDescriptor` does not implement `__get__` / `__set__` — it is not a real Python descriptor

**File:** `rust/syntek-pyo3/src/lib.rs:127–144`

**Description:** `EncryptedFieldDescriptor` is a `#[pyclass]` that records `model_name` and
`field_name`. The story states it is "installed on Django model classes" so the GraphQL middleware
can "resolve AAD without manual annotation". For a class attribute to function as a Python
descriptor (intercepting attribute access on instances), it must implement `__get__`, and optionally
`__set__` and `__delete__`. `EncryptedFieldDescriptor` has none of these. It is installed as a plain
class attribute via `cls.setattr(name, descriptor)`.

This means:

1. When Django creates a model instance and accesses `instance.email`, Python's descriptor protocol
   looks for `__get__` on the class attribute. Finding none, it falls back to the instance
   `__dict__`. If `instance.__dict__` has no `email` key, an `AttributeError` is raised. If it does
   have a key (because `pre_save` stored a value), the descriptor is bypassed entirely.

2. Critically, `contribute_to_class` calls `cls.setattr(name, descriptor)`, which replaces the
   `EncryptedField` object on the class with an `EncryptedFieldDescriptor` object. After
   `contribute_to_class` runs, `User.email` is the descriptor, not the `EncryptedField`. Django
   expects to find the field object on the class (via `Model._meta.fields` traversal) for query
   building. Replacing the field object with a non-field descriptor will break Django ORM
   introspection and query generation for any model using `EncryptedField`.

**Impact:** Models using `EncryptedField` will fail Django ORM migrations, `makemigrations`, and any
query that traverses model metadata. The descriptor, once installed, will not intercept
`instance.email` access because it lacks `__get__`, meaning the GraphQL middleware cannot rely on it
for AAD resolution via attribute lookup on model instances.

**Reproduce:** Define a real Django model with `email = EncryptedField()`. Run `makemigrations`.
Django calls `contribute_to_class` during model class construction, which replaces the field on the
class with a descriptor object that is not a `django.db.models.Field` subclass. Django's
`Options.contribute_to_class` and field registration machinery will either raise an `AttributeError`
or silently skip the field, corrupting the model's `_meta.fields` list.

**Recommended fix direction:** The `EncryptedFieldDescriptor` data (model name, field name) must be
stored in a way that does not replace the Django field object on the model class. Options include:
storing the metadata as attributes on the `EncryptedField` instance itself; using a separate
side-channel registry (a module-level dict keyed by `(model_name, field_name)`); or implementing a
proper Python data descriptor with `__get__` and `__set__` that wraps the field value transparently.
The `contribute_to_class` method must not overwrite the field entry on the model class.

---

<!-- markdownlint-disable MD013 -->

### H5 — `decrypt_fields_batch` does not validate the key length before iterating — partial state may be allocated before failure

<!-- markdownlint-enable MD013 -->

**File:** `rust/syntek-crypto/src/lib.rs:385–399`

**Description:** `decrypt_fields_batch` in `syntek-crypto` calls `decrypt_field` for each pair in
the input slice without first validating the key length. `decrypt_field` validates the key length
internally (line 159–163), returning a `CryptoError::DecryptionError`. However, the key-length check
in `decrypt_field` comes after the base64 decode and nonce extraction. This means the first field in
the batch is partially processed (base64-decoded, nonce extracted) before the key is found to be
invalid. While this does not leak data in the current implementation, it is an inconsistency with
`encrypt_fields_batch` (which validates key length first, line 344–349 in `lib.rs`) and creates a
divergence in the error type returned for an invalid key: `encrypt_fields_batch` returns
`InvalidInput`, while `decrypt_fields_batch` returns `DecryptionError` (from inside
`decrypt_field`), both mapped to `PyValueError` at the Python boundary. Consumer code that
differentiates the two will be broken.

**Recommended fix direction:** Add a key-length pre-check at the top of `decrypt_fields_batch`
(mirroring `encrypt_fields_batch`) so that invalid keys are rejected before any batch processing
begins and the error variant is `InvalidInput` in both directions.

---

## MEDIUM (Fix soon, non-blocking)

### M1 — `EncryptedField.validate` is not called by Django automatically — integration with `Model.full_clean` is not tested

**File:** `rust/syntek-pyo3/src/lib.rs:173–189`

**Description:** Django's field `validate` method is called by `Model.full_clean()`, which is called
by Django forms and the admin but is NOT called automatically by `Model.save()`. The
defence-in-depth guard described in the story is implemented in `pre_save`, which IS called on every
save. However, the `validate` method duplicates the same logic and is also tested in isolation.
There is no test or manual scenario that calls `model_instance.full_clean()` then `save()` on a real
Django model with a PostgreSQL backend to confirm the two code paths interact correctly.

The test fixture in `conftest.py` uses SQLite in-memory, not PostgreSQL. The story's completion
verification states "DB roundtrip confirming only ciphertext is stored" is covered in "green phase
manual scenarios", but no automated integration test with a real DB write exists
(`docs/TESTS/US007-TEST-STATUS.md:17` shows 0 integration tests).

**Impact:** There is no automated verification that the plaintext-rejection guard survives a full
Django ORM save cycle against a real PostgreSQL 18.3 database. A regression in how `pre_save` is
invoked (e.g. a Django version update changing the call order) would go undetected.

**Recommended fix direction:** Add at least one integration test using `testcontainers-python`
(already in the project's testing stack) that creates a real PostgreSQL container, defines a model
with `EncryptedField`, and asserts that a `save()` call with plaintext raises `ValidationError` and
that a `save()` with valid ciphertext writes the ciphertext unchanged.

---

### M2 — `from_db_value` accepts and returns invalid ciphertext from the database without raising

**File:** `rust/syntek-pyo3/src/lib.rs:196–204`

**Description:** `from_db_value` is a pure passthrough — by design, it performs no validation. This
is architecturally correct for the stated boundary (decryption is the GraphQL layer's
responsibility). However, if a database row contains a value that is not valid ciphertext (e.g. a
row written before `EncryptedField` was introduced, a failed partial migration, or a direct `UPDATE`
bypassing the ORM), `from_db_value` will silently return the raw value to the resolver. The GraphQL
middleware will then attempt to decrypt it, and `decrypt_field` will fail with a `DecryptionError`.
There is no test that verifies the GraphQL middleware's error handling for this scenario.

**Impact:** A data migration gap or direct database write that stores a non-ciphertext value in an
`EncryptedField` column will silently propagate to the GraphQL layer. Depending on the middleware
implementation, the error could result in a 500 response, a null field in the response, or (worst
case) partial plaintext leakage if the middleware does not handle the exception correctly.

**Recommended fix direction:** Document in the field's docstring that `from_db_value` may return
non-ciphertext values for rows written outside the ORM, and ensure the GraphQL middleware test suite
explicitly covers this case.

---

### M3 — `test_real_ciphertext_from_syntek_crypto_passes_format_check` uses an all-zeros key

**File:** `rust/syntek-pyo3/tests/pyo3_module_tests.rs:82–87`

**Description:**

```rust
let key = [0u8; 32];
```

This is a weak, all-zeros key used in a test that also passes through `syntek-crypto`'s real
`encrypt_field`. The concern is not that secrets are committed — zeros are clearly a test value —
but that this key pattern is copied verbatim in the Python binding tests (`_KEY = bytes(range(32)`)
and in every manual test scenario. Both key patterns (all-zeros, sequential bytes) are trivially
weak and appear in two different places. If either ever appears in production or staging environment
setup documentation, they are immediately exploitable.

The manifest's post-install step already carries the correct warning (`# not for production use`)
but the Rust test file and Python test file do not, creating a documentation gap that might lead an
inexperienced developer to cargo-cult these keys.

**Recommended fix direction:** Add a `// TEST KEY ONLY — NOT FOR PRODUCTION USE` comment alongside
the key constant in the Rust test file. Ensure the Python `_KEY` constant in `test_pyo3_bindings.py`
also carries a visible comment of the same kind (one already exists as a code comment on line 20,
but it should be a module-level docstring warning to be more visible).

---

### M4 — `BatchDecryptionError` is defined but never raised — it is a dead type

**File:** `rust/syntek-pyo3/src/lib.rs:44–59`

**Description:** `BatchDecryptionError` is defined in `lib.rs` with a `thiserror::Error` derive and
is verified by a Rust compile-time test. However, it is never constructed or returned from any
function in the codebase. `decrypt_fields_batch` (the natural site for its use) delegates directly
to `syntek_crypto::decrypt_fields_batch`, which returns a `CryptoError::BatchError`. The
`crypto_err_to_py` mapper converts that to `PyValueError`. `BatchDecryptionError` is referenced only
by the Rust integration test. The story's AC7 states: "raises `BatchDecryptionError` if any field
fails" — this is a spec requirement that is not implemented: no `BatchDecryptionError` is ever
raised, and it cannot be raised to Python because it is not a Python exception class.

**Impact:** The AC7 acceptance criterion is not met as specified. The error type raised is a generic
`PyValueError` wrapping a `CryptoError::BatchError` message string. The distinction between a
single-field `DecryptionError` and a `BatchDecryptionError` is lost.

**Recommended fix direction:** Either implement `BatchDecryptionError` as a Python exception class
(via `pyo3::create_exception!`) and raise it from `decrypt_fields_batch`, or revise the AC7 wording
to correctly state that a `ValueError` (with field name in the message) is raised, and remove the
`BatchDecryptionError` struct to avoid dead-code confusion.

---

### M5 — `EncryptedField.__new__` takes no arguments — consumers cannot set `null`, `blank`, `max_length`

**File:** `rust/syntek-pyo3/src/lib.rs:163–170`

**Description:** `EncryptedField::new()` takes no arguments. A real Django `TextField` subclass
constructor accepts keyword arguments such as `null=True`, `blank=True`, `max_length`, `db_column`,
etc. Without accepting and forwarding these arguments, any consumer who writes:

```python
email = EncryptedField(null=True, blank=True)
```

will receive a `TypeError` from PyO3 ("**new**() takes no arguments").

**Impact:** All real-world Django model definitions that use `EncryptedField` with any Django field
arguments will fail at class-definition time. This makes the field unusable in any model that
requires optional encrypted columns.

**Recommended fix direction:** The `#[new]` method should accept `**kwargs` (using PyO3's
`pyo3::types::PyDict`) and store at minimum `null` and `blank` as fields on the struct, forwarding
them for Django's field machinery to use. Alternatively, `EncryptedField` should be implemented in
Python (inheriting from `django.db.models.TextField`) with only the `validate` and `pre_save` logic
delegating to the Rust extension, which would automatically inherit Django's field constructor.

---

### M6 — `contribute_to_class` does not call `super().contribute_to_class()` — Django's field registration is skipped

**File:** `rust/syntek-pyo3/src/lib.rs:215–232`

**Description:** Django's `Field.contribute_to_class(cls, name)` base method is responsible for:

1. Calling `cls._meta.add_field(self, private_only=...)` to register the field with the model's
   `Options` (the `_meta` API).
2. Setting `self.name`, `self.attname`, `self.column`.
3. Connecting post-init signals.

The PyO3 implementation sets `self.attname` and calls `cls.setattr(name, descriptor)` but does not
call `super().contribute_to_class()` (nor can it easily, because the struct does not inherit from a
Django base class). The field will therefore never be added to `Model._meta.fields`, and Django will
have no knowledge of the column for migrations, query building, or `Model.from_db` rehydration.

**Impact:** Running `makemigrations` with a model that includes `EncryptedField` will produce an
empty migration (the field is unknown to `_meta`). The column will not be created in the database.
This is a fundamental blocker for any consumer attempting to use the field in a real migration.

**Recommended fix direction:** `EncryptedField` should be implemented as a Python class inheriting
from `django.db.models.TextField`, with the Rust extension providing only the cryptographic
validation logic. The Python subclass would override `validate` and `pre_save` to call into the Rust
functions, while inheriting Django's full field registration lifecycle. This is the canonical
pattern for custom Django field types.

---

### M7 — `verify_password` with an empty `hash` argument is not tested

**File:** `rust/syntek-crypto/src/lib.rs:242–253`

**Description:** `verify_password` checks `if password.is_empty()` and returns `Ok(false)`, but does
not check whether `hash` is empty or malformed before calling `PasswordHash::new(hash)`. Passing an
empty string for `hash` triggers `PasswordHash::new("")` which returns a `password_hash::Error`,
mapped to `CryptoError::HashError`. This raises a `PyValueError` in Python rather than returning
`false` or raising a more specific exception. There is no test for `verify_password("valid",  "")`.

**Impact:** A downstream caller that passes an empty or malformed hash (e.g. an uninitialised column
value) will receive an unexpected exception rather than a predictable `false`. This is a deviation
from the principle of least surprise for a verification function.

**Recommended fix direction:** Add a guard for `hash.is_empty()` that returns `Ok(false)` (matching
the behaviour for an empty password). Add a corresponding test in the Python binding suite for this
path.

---

## LOW / Observations

### L1 — `DecryptionError` and `BatchDecryptionError` have no Python `__module__` attribute

Even if these types were registered as Python exceptions in the future, they lack documentation
strings. By convention, Python exception classes carry a docstring used by introspection tooling and
documentation generators. This is low-priority but should be addressed if these types are promoted
to real Python exceptions.

---

### L2 — `syntek.manifest.toml` post-install glob for wheel install is fragile

**File:** `rust/syntek-pyo3/syntek.manifest.toml:27`

```bash
uv pip install target/wheels/syntek_pyo3-*.whl 2>/dev/null || pip install target/wheels/syntek_pyo3-*.whl
```

The glob `syntek_pyo3-*.whl` will match any version of the wheel in `target/wheels/`. If a developer
has previously built a different version (e.g. `0.12.1`) and then builds `0.15.0`, both wheels may
be present, and shell glob expansion order is filesystem-dependent. The consumer could install the
wrong version silently. Additionally, suppressing stderr from `uv pip install` with `2>/dev/null`
hides any installation errors before falling back to `pip`.

**Recommended fix direction:** Recommend
`uv pip install --find-links target/wheels syntek-pyo3==<version>` with an explicit version so the
correct wheel is always selected.

---

### L3 — No `maturin` version pin in CI for the native extension build

The `pyproject.toml` build requirement is `maturin>=1.7,<2`. There is no locked version for CI. A
new maturin release within the `1.x` range could silently change the ABI or wheel metadata format.
For a crate that produces a native extension loaded into a production Django process, the build tool
version should be pinned exactly in CI.

---

### L4 — `EncryptedFieldDescriptor` exposes `model_name` and `field_name` as public `get` attributes with no `set` guard

**File:** `rust/syntek-pyo3/src/lib.rs:129–130`

Both fields use `#[pyo3(get)]` only, meaning they are read-only from Python. However, because
`EncryptedFieldDescriptor` is not a frozen class (`#[pyclass(frozen)]`), it is technically possible
to bypass the Python property and set arbitrary attributes on an instance using
`object.__setattr__`. While this is an unlikely attack in a Django application context, it is worth
noting that the class should be declared `#[pyclass(frozen)]` if mutation is genuinely not intended.

---

### L5 — Red-phase test count discrepancy in manual testing guide

**File:** `docs/TESTS/US007-MANUAL-TESTING.md:66`

The manual testing guide states "Total: 55 FAIL, 0 PASS" for the red phase, but the automated test
status document reports 65 tests total in the green phase. The red phase count of 55 does not
account for the 10 additional tests added between the initial red phase and the final green phase.
This is a documentation inconsistency that could mislead future reviewers auditing the TDD
discipline of this story.

---

## Missing Test Scenarios

The following test scenarios are absent from the automated test suite and should be added:

1. **`EncryptedField` with `None` / `null=True` save** — verify that a nullable encrypted field
   saves `NULL` to the database without raising `TypeError`. Currently this path crashes (see C1).

2. **Real PostgreSQL integration roundtrip** — a `testcontainers-python` test that defines a model
   with `EncryptedField`, runs migrations, saves a model instance with valid ciphertext, and reads
   it back, asserting that the stored column value is the ciphertext (not plaintext). 0 integration
   tests currently exist.

3. **`EncryptedField` with `null=True, blank=True` constructor arguments** — verify that the field
   accepts Django's standard keyword arguments without raising `TypeError` (see M5).

4. **`contribute_to_class` registers the field with `_meta`** — verify that after
   `contribute_to_class`, the field appears in `Model._meta.fields` and `makemigrations` produces
   the correct schema. Currently this is entirely untested.

5. **Cross-format ciphertext rejection** — a test that passes a versioned ciphertext (prefixed with
   2 version bytes) to `decrypt_field` (unversioned) and asserts that the GCM tag fails rather than
   producing garbage plaintext. Confirms the two formats are not silently cross-compatible.

6. **`verify_password` with an empty or malformed hash argument** — verify behaviour is predictable
   (either `false` or a well-typed exception) rather than an opaque `ValueError` (see M7).

7. **`BatchDecryptionError` is raised as the correct Python exception type** — currently
   `pytest.raises(Exception)` is used in all batch failure tests, masking the fact that the specific
   error type (see M4) is never raised.

8. **`EncryptedField.validate` called via `Model.full_clean()`** — verify the Django validation
   pipeline invokes the field's `validate` method correctly in the context of a full model
   validation cycle.

9. **`EncryptedFieldDescriptor` is a read-only frozen class** — verify that attempting to set
   `model_name` or `field_name` on a descriptor instance raises `AttributeError`.

10. **Large plaintext throughput** — verify behaviour with a plaintext value at or above Django's
    default column size boundary (e.g. a 1 MB string) to confirm no silent truncation or memory
    panic occurs in the PyO3 layer.

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to address C1 (None guard in `pre_save`), H4 (descriptor
  protocol), H2 (Python exception types), M5 and M6 (field constructor and `contribute_to_class`).
  These are implementation corrections, not test changes.
- Run `/syntek-dev-suite:debug` to investigate C2 (versioned vs. unversioned ciphertext format
  compatibility with US076) — this requires a cross-story architectural decision before any code
  change.
- Run `/syntek-dev-suite:test-writer` to add the missing integration tests listed in the Missing
  Test Scenarios section, particularly scenarios 1, 2, 3, 4, 6, and 7.
- Run `/syntek-dev-suite:completion` to update the US007 story status — it should be moved from
  `Completed` to `Requires Rework` until at minimum C1, C2, H2, H4, M5, and M6 are resolved.
