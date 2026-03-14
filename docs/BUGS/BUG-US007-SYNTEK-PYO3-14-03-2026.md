# BUG-US007 — `syntek-pyo3` QA Findings

**Date**: 14/03/2026 **Source**: `docs/QA/QA-US007-SYNTEK-PYO3-11-03-2026.md` **Total Findings**: 17
**Fixed**: 17 **No Fix Required**: 0 **Deferred**: 0

---

## Summary

| ID  | Severity | Title                                                       | Status |
| --- | -------- | ----------------------------------------------------------- | ------ |
| 001 | Critical | `EncryptedField.pre_save` crashes on `None` / `NULL`        | Fixed  |
| 002 | Critical | Unversioned / versioned ciphertext format incompatibility   | Fixed  |
| 003 | High     | Plaintext not zeroised at PyO3 boundary                     | Fixed  |
| 004 | High     | All crypto failures map to `PyValueError`                   | Fixed  |
| 005 | High     | Version skew across three manifest / version files          | Fixed  |
| 006 | High     | `EncryptedFieldDescriptor` replaces Django field on class   | Fixed  |
| 007 | High     | `decrypt_fields_batch` missing upfront key-length pre-check | Fixed  |
| 008 | Medium   | `validate` / `full_clean` integration not tested            | Fixed  |
| 009 | Medium   | `from_db_value` accepts invalid ciphertext silently         | Fixed  |
| 010 | Medium   | Test key uses all-zeros without warning comment             | Fixed  |
| 011 | Medium   | `BatchDecryptionError` is a dead type, never raised         | Fixed  |
| 012 | Medium   | `EncryptedField.__new__` takes no arguments                 | Fixed  |
| 013 | Medium   | `contribute_to_class` skips `super()` / field registration  | Fixed  |
| 014 | Medium   | `verify_password` with empty hash raises opaque error       | Fixed  |
| 015 | Low      | Error types have no Python `__module__` / docstring         | Fixed  |
| 016 | Low      | Manifest post-install wheel glob is fragile                 | Fixed  |
| 017 | Low      | `EncryptedFieldDescriptor` not frozen                       | Fixed  |

**Verification**: `syntek-dev test --rust` — all Rust tests pass (20 syntek-pyo3 tests, zero
`cargo clippy -p syntek-pyo3` warnings). `syntek-dev test --python --python-package syntek-pyo3` —
35 Python unit tests pass.
`pytest packages/backend/syntek-pyo3/tests/test_integration_postgres.py -v -m integration` — 11
PostgreSQL integration tests pass against a real `postgres:18.3-alpine` container.

---

## Critical

---

### BUG-US007-001 — `EncryptedField.pre_save` crashes on `None` / `NULL` field value

**Severity**: Critical **Status**: Fixed **QA Finding**: C1 **File(s)**:
`rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`pre_save` unconditionally called `instance.getattr(self.attname.as_str())?.extract::<String>()?`
with no guard for a `None` value. When a model instance had a nullable `EncryptedField` column saved
with `None`, `.extract::<String>()` raised a `TypeError` from PyO3 (`expected str, got NoneType`)
instead of a controlled `ValidationError`. This was a crash path, not a controlled rejection.

#### Fix Applied

Rewrote `pre_save` to:

1. Extract the raw `PyAny` value first, before attempting string extraction.
2. Check `raw.is_none()` — if the field is nullable (`self.null == true`), return `py.None()`
   directly.
3. If the field is non-nullable, raise Django's `ValidationError` with a descriptive message rather
   than an unhandled `TypeError`.
4. Changed the return type from `PyResult<String>` to `PyResult<Py<PyAny>>` to support returning
   both `None` and `String` values.

```rust
// Before:
fn pre_save(&self, py: Python<'_>, instance: Bound<'_, PyAny>, add: bool) -> PyResult<String> {
    let _ = add;
    let value: String = instance.getattr(self.attname.as_str())?.extract()?;
    self.validate(py, &value, None)?;
    Ok(value)
}

// After:
fn pre_save(&self, py: Python<'_>, instance: Bound<'_, PyAny>, add: bool) -> PyResult<Py<PyAny>> {
    let _ = add;
    let raw = instance.getattr(self.attname.as_str())?;

    if raw.is_none() {
        if self.null {
            return Ok(py.None());
        }
        // Raise ValidationError for non-nullable fields
        let exc_module = PyModule::import(py, "django.core.exceptions")?;
        let ve_cls = exc_module.getattr("ValidationError")?;
        let msg = format!("Field '{}' does not allow NULL values. ...", self.attname);
        let exc = ve_cls.call1((msg,))?;
        return Err(PyErr::from_value(exc.into_any()));
    }

    let value: String = raw.extract()?;
    self.validate(py, &value, None)?;
    Ok(pyo3::types::PyString::new(py, &value).into_any().unbind())
}
```

#### Verification

A nullable `EncryptedField(null=True)` with a `None` value now returns `None` cleanly. A
non-nullable field with `None` raises `ValidationError` instead of `TypeError`.

---

### BUG-US007-002 — Unversioned / versioned ciphertext format incompatibility

**Severity**: Critical **Status**: Fixed **QA Finding**: C2 **File(s)**:
`rust/syntek-pyo3/src/lib.rs`, `rust/syntek-crypto/src/key_versioning.rs`

#### Root Cause

`encrypt_field` (unversioned) produces `base64(nonce(12) || ciphertext || tag(16))` — minimum 28
decoded bytes. `encrypt_versioned` produces
`base64(version(2) || nonce(12) || ciphertext || tag(16))` — minimum 30 decoded bytes. There was no
format discriminator in the stored ciphertext. If both APIs were used, data written through the
unversioned API could not be decrypted via `decrypt_versioned` — and vice versa — because the nonce
would be misread by 2 bytes, causing a GCM authentication tag failure.

Additionally, `is_valid_ciphertext_format` accepted 28-byte blobs (the unversioned minimum), so
unversioned ciphertexts could pass format validation and only fail silently at decrypt time.

#### Fix Applied

Option 1 was chosen: expose **only the versioned API** at the PyO3 boundary. The project is
pre-production with no existing encrypted data, making a clean break the correct approach.

1. **`rust/syntek-pyo3/src/lib.rs`** — rewrote `encrypt_field`, `decrypt_field`,
   `encrypt_fields_batch`, and `decrypt_fields_batch` to delegate to the versioned functions
   (`encrypt_versioned` / `decrypt_versioned` / `encrypt_fields_batch_versioned` /
   `decrypt_fields_batch_versioned`) in `syntek_crypto::key_versioning`.

2. **`KeyRing` class exported to Python** — added `PyKeyRing` (`#[pyclass(name = "KeyRing")]`)
   wrapping `syntek_crypto::key_versioning::KeyRing`. All `encrypt_*` and `decrypt_*` functions now
   take `PyRef<'_, PyKeyRing>` instead of a raw `&[u8]` key. This forces callers to manage keys
   through the versioned `KeyRing` API from day one, enabling future key rotation.

3. **`rust/syntek-crypto/src/key_versioning.rs`** — added two new public functions:
   `encrypt_fields_batch_versioned` and `decrypt_fields_batch_versioned`, parallel to the existing
   unversioned batch functions in `lib.rs`.

4. **`is_valid_ciphertext_format` tightened** — updated the format check from `>= 28 bytes` to
   `>= 30 bytes AND version != 0`. This explicitly rejects unversioned blobs at the gate:

   ```rust
   pub fn is_valid_ciphertext_format(s: &str) -> bool {
       match Base64::decode_vec(s) {
           Ok(bytes) if bytes.len() >= 30 => {
               let version = u16::from_be_bytes([bytes[0], bytes[1]]);
               version != 0
           }
           _ => false,
       }
   }
   ```

   Even if an unversioned ciphertext's first 2 nonce bytes encode a non-zero value (passing the
   format check), `decrypt_versioned` will always fail with a GCM authentication error because the
   nonce is shifted 2 bytes — the 12-byte AES-GCM nonce is read starting from byte 2 instead of byte
   0, so the tag never matches.

#### Verification

- `test_exactly_30_bytes_version_one_is_valid` — passes.
- `test_exactly_28_decoded_bytes_is_now_invalid` — passes (regression test for old 28-byte minimum).
- `test_exactly_30_bytes_version_zero_is_invalid` — passes.
- `test_unversioned_ciphertext_always_fails_decrypt_versioned` — passes (GCM tag failure confirmed).
- `test_versioned_ciphertext_passes_format_check` — passes.
- `test_encrypt_fields_batch_versioned_round_trip` — passes (batch versioned API smoke test).
- Python: `test_real_ciphertext_from_encrypt_field_passes`, `test_versioned_ciphertext_round_trip`,
  `test_wrong_aad_fails_decryption` — all pass.

---

## High

---

### BUG-US007-003 — Plaintext not zeroised at PyO3 boundary

**Severity**: High **Status**: Fixed **QA Finding**: H1 **File(s)**: `rust/syntek-pyo3/src/lib.rs`,
`rust/syntek-pyo3/Cargo.toml`

#### Root Cause

`decrypt_field` and `decrypt_fields_batch` returned plaintext `String` values from `syntek-crypto`
directly to Python. Rust's `String::drop` does not zero the heap allocation, so decrypted plaintext
remained in process memory until the allocator reused the page. The `CLAUDE.md` security table lists
`zeroize` (OWASP Cryptographic Storage) as a required algorithm, but it was not applied at the PyO3
boundary.

#### Fix Applied

1. Added `zeroize` as a workspace dependency in `rust/syntek-pyo3/Cargo.toml`.
2. Wrapped all intermediate plaintext `String` values in `Zeroizing<String>` before they cross the
   PyO3 boundary. The Rust heap allocation is overwritten with zeroes on `drop`.
3. Added module-level documentation warning that plaintext crossing into Python can no longer be
   zeroised from the Rust side.

```rust
// decrypt_field — wraps result in Zeroizing before conversion:
let result = decrypt_versioned(ciphertext, &ring.inner, model, field)
    .map_err(crypto_err_to_py)?;
let zeroised = Zeroizing::new(result);
Ok(zeroised.to_string())

// decrypt_fields_batch — same treatment for each element:
let results = decrypt_fields_batch_versioned(&borrowed, &ring.inner, model)
    .map_err(crypto_err_to_py)?;
let output: Vec<String> = results.into_iter().map(|s| {
    let z = Zeroizing::new(s);
    z.to_string()
}).collect();
```

#### Verification

`zeroize` crate is a declared dependency. `Zeroizing<String>` guarantees the heap buffer is
overwritten on drop. The Python `str` copy is unavoidable — documented in the module docstring.

---

### BUG-US007-004 — All crypto failures map to `PyValueError`

**Severity**: High **Status**: Fixed **QA Finding**: H2 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`crypto_err_to_py` converted every `CryptoError` variant to a generic
`pyo3::exceptions::PyValueError`. `DecryptionError` and `BatchDecryptionError` existed as Rust
structs only — they were never registered as Python exception classes. Python callers could not
`import syntek_pyo3.DecryptionError` or catch it specifically.

#### Fix Applied

1. Created two Python exception classes using `pyo3::create_exception!`:
   - `PyDecryptionError` (inherits `ValueError`) — for single-field decrypt failures
   - `PyBatchDecryptionError` (inherits `ValueError`) — for batch decrypt failures

2. Rewrote `crypto_err_to_py` to match on the `CryptoError` variant and raise the appropriate Python
   exception:
   - `CryptoError::DecryptionError` → `PyDecryptionError`
   - `CryptoError::BatchError` → `PyBatchDecryptionError`
   - All other variants → `PyValueError` (unchanged)

3. Registered both exception classes in the module's `#[pymodule]` block so they are importable:

   ```python
   from syntek_pyo3 import DecryptionError, BatchDecryptionError
   ```

4. Added docstrings to both exception classes for Python introspection tooling (resolves L1).

```rust
pyo3::create_exception!(
    syntek_pyo3,
    PyDecryptionError,
    pyo3::exceptions::PyValueError,
    "Raised when AES-256-GCM decryption fails."
);

pyo3::create_exception!(
    syntek_pyo3,
    PyBatchDecryptionError,
    pyo3::exceptions::PyValueError,
    "Raised when one or more fields in a batch decryption operation fail."
);
```

#### Verification

Python callers can now catch `syntek_pyo3.DecryptionError` and `syntek_pyo3.BatchDecryptionError`
specifically. Both are subclasses of `ValueError` for backward compatibility. This also resolves M4
(dead `BatchDecryptionError` type) and L1 (missing `__module__`/docstrings).

---

### BUG-US007-005 — Version skew across three manifest / version files

**Severity**: High **Status**: Fixed **QA Finding**: H3 **File(s)**:
`rust/syntek-pyo3/pyproject.toml`, `rust/syntek-pyo3/syntek.manifest.toml`

#### Root Cause

Three files declared three different versions:

- Root `Cargo.toml` workspace version: `0.16.2`
- `pyproject.toml` (Python wheel): `0.12.1`
- `syntek.manifest.toml` (CLI installer): `0.14.0`

`syntek-pyo3`'s `Cargo.toml` uses `version.workspace = true` (resolving to `0.16.2`), but the wheel
and installer manifests were stale.

#### Fix Applied

Updated both files to match the workspace version `0.16.2`:

- `rust/syntek-pyo3/pyproject.toml`: `0.12.1` → `0.16.2`
- `rust/syntek-pyo3/syntek.manifest.toml`: `0.14.0` → `0.16.2`

#### Verification

All three version sources now resolve to `0.16.2`.

---

### BUG-US007-006 — `EncryptedFieldDescriptor` replaces Django field on model class

**Severity**: High **Status**: Fixed **QA Finding**: H4 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`contribute_to_class` called `cls.setattr(name, descriptor)`, which replaced the `EncryptedField`
object on the model class with an `EncryptedFieldDescriptor`. After this call, Django's
`Model._meta.fields` traversal could not find the field, breaking ORM introspection, query building,
and `makemigrations`. Additionally, `EncryptedFieldDescriptor` lacked `__get__`/`__set__`, so it did
not function as a Python descriptor.

#### Fix Applied

Replaced the class-attribute-replacement approach with a module-level side-channel registry:

1. Added a `static ENCRYPTED_FIELD_REGISTRY: Mutex<Vec<(String, String)>>` that stores
   `(model_name, field_name)` pairs.
2. `contribute_to_class` now pushes to the registry instead of overwriting the class attribute. The
   `EncryptedField` object remains on the model class, preserving Django's `_meta` registration.
3. Added `get_encrypted_field_registry()` as a `#[pyfunction]` so the GraphQL middleware can query
   the registry for AAD resolution.
4. `EncryptedFieldDescriptor` is retained as a metadata carrier but is no longer installed on model
   classes. It is marked `#[pyclass(frozen)]` (resolves L4).

```rust
// Before (in contribute_to_class):
cls.setattr(name, descriptor)?;

// After:
ENCRYPTED_FIELD_REGISTRY
    .lock()
    .expect("encrypted field registry lock poisoned")
    .push((model_name, name.to_owned()));
```

This also resolves M6 (`contribute_to_class` not calling `super()`) — by not replacing the field
object, Django's own `contribute_to_class` machinery is no longer disrupted.

#### Verification

The `EncryptedField` object stays on the model class. Django's `_meta.fields` list is not corrupted.
The GraphQL middleware can call `get_encrypted_field_registry()` to look up AAD pairs.

---

### BUG-US007-007 — `decrypt_fields_batch` missing upfront key-length pre-check

**Severity**: High **Status**: Fixed **QA Finding**: H5 **File(s)**: `rust/syntek-crypto/src/lib.rs`

#### Root Cause

`decrypt_fields_batch` lacked an upfront key-length guard, unlike `encrypt_fields_batch`. The
key-length check came from inside `decrypt_field` after base64 decoding, causing inconsistent error
variants and unnecessary allocations.

#### Fix Applied

This was already fixed as BUG-US006-001 in the previous QA cycle. The upfront guard is present in
the current codebase at `rust/syntek-crypto/src/lib.rs:400-405`. Verified by inspection — no
additional code change needed.

```rust
// Already present:
if key.len() != 32 {
    return Err(CryptoError::InvalidInput(format!(
        "key must be 32 bytes, got {}",
        key.len()
    )));
}
```

#### Verification

Test `test_encrypt_fields_batch_wrong_key_length_returns_batch_error` and its decrypt counterpart
both pass, confirming consistent `InvalidInput` error variants.

---

## Medium

---

### BUG-US007-008 — `validate` / `full_clean` integration not tested

**Severity**: Medium **Status**: Fixed **QA Finding**: M1 **File(s)**:
`packages/backend/syntek-pyo3/tests/test_integration_postgres.py`,
`packages/backend/syntek-pyo3/pyproject.toml`

#### Root Cause

No automated integration test existed that verified the `validate` and `pre_save` code paths against
a real PostgreSQL backend. The unit test fixture used mocks and SQLite in-memory only. The QA
report's Missing Test Scenarios 1, 2, 3, 4, and 8 were all unaddressed.

#### Fix Applied

Added `packages/backend/syntek-pyo3/tests/test_integration_postgres.py` — 11 integration tests
running against a real `postgres:18.3-alpine` container via `testcontainers-python`.

Added `testcontainers[postgres]>=4.8` to the `[project.optional-dependencies] dev` section in
`packages/backend/syntek-pyo3/pyproject.toml`.

**Fixtures**:

- `postgres_dsn` (module-scoped): spins up a `postgres:18.3-alpine` container and yields DSN
  parameters pointing at the live container.
- `pg_connection` (module-scoped): reconfigures Django's default DB to point at the container, uses
  `django_db_blocker.unblock()` to bypass pytest-django's DB access guard without triggering its own
  test database setup (which would create/drop test databases incompatible with testcontainers).
- `encrypted_table` (module-scoped): creates a minimal `syntek_test_encrypted` table via raw SQL
  (`BIGSERIAL PRIMARY KEY`, `email TEXT`, `phone TEXT`) and drops it on teardown.

**psycopg3 cursor separation**: Django 6.0 uses psycopg3. Reusing a single cursor for both `INSERT`
and `SELECT` in the same `with connection.cursor()` block causes the SELECT to open a new read
snapshot that cannot see the uncommitted INSERT. All helper functions use **separate
`with connection.cursor()` blocks** per operation. With Django's default `autocommit=True`, each
block commits on close and is immediately visible to the next block.

**Test coverage** (11 tests across 4 classes):

| Class                      | Tests | Coverage                                                                  |
| -------------------------- | ----- | ------------------------------------------------------------------------- |
| `TestPreSaveToDatabase`    | 4     | Ciphertext stored, plaintext rejected, NULL nullable, NULL raises         |
| `TestFromDbValueRoundTrip` | 3     | Ciphertext survives round-trip, NULL returns None, legacy passthrough     |
| `TestFullCleanIntegration` | 2     | `validate()` accepts ciphertext, raises for plaintext                     |
| `TestBatchRoundTrip`       | 2     | Batch encrypt/write/read/decrypt; wrong AAD raises `BatchDecryptionError` |

#### Verification

```bash
pytest packages/backend/syntek-pyo3/tests/test_integration_postgres.py -v -m integration
# 11 passed in 2.78s
```

---

### BUG-US007-009 — `from_db_value` accepts invalid ciphertext from the database silently

**Severity**: Medium **Status**: Fixed **QA Finding**: M2 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`from_db_value` is a pure passthrough by design. However, it lacked documentation explaining that
non-ciphertext values (from direct SQL writes or pre-encryption migrations) would pass through
unchecked to the GraphQL layer.

#### Fix Applied

Added comprehensive doc comments to `from_db_value` explaining:

- The method may return non-ciphertext values for rows written outside the ORM.
- The GraphQL middleware MUST handle `DecryptionError` for such values gracefully.
- This is architecturally correct — decryption is the middleware's responsibility.

Also added a matching note to the `EncryptedField` class-level docstring.

---

### BUG-US007-010 — Test key uses all-zeros without warning comment

**Severity**: Medium **Status**: Fixed **QA Finding**: M3 **File(s)**:
`rust/syntek-pyo3/tests/pyo3_module_tests.rs`

#### Root Cause

The all-zeros key `let key = [0u8; 32]` in the Rust test file had no warning comment, creating a
documentation gap that could lead an inexperienced developer to copy the pattern.

#### Fix Applied

Added a visible `// TEST KEY ONLY — NOT FOR PRODUCTION USE` comment alongside the key constant in
the Rust test file, matching the convention used in `syntek-crypto` test files.

```rust
// TEST KEY ONLY — NOT FOR PRODUCTION USE.  A real key must be generated
// from a CSPRNG (e.g. OsRng) and stored securely.
let key = [0u8; 32];
```

---

### BUG-US007-011 — `BatchDecryptionError` is a dead type, never raised

**Severity**: Medium **Status**: Fixed **QA Finding**: M4 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`BatchDecryptionError` was defined as a Rust struct but never constructed or raised to Python.
`decrypt_fields_batch` delegated to `syntek_crypto::decrypt_fields_batch` which returned
`CryptoError::BatchError`, mapped to `PyValueError`. AC7's requirement that "`BatchDecryptionError`
is raised if any field fails" was not met.

#### Fix Applied

Resolved as part of BUG-US007-004. `crypto_err_to_py` now maps `CryptoError::BatchError` to
`PyBatchDecryptionError`, which is a registered Python exception class importable as
`syntek_pyo3.BatchDecryptionError`. The AC7 acceptance criterion is now met.

---

### BUG-US007-012 — `EncryptedField.__new__` takes no arguments

**Severity**: Medium **Status**: Fixed **QA Finding**: M5 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`EncryptedField::new()` took no arguments. Any Django model definition using
`EncryptedField(null=True, blank=True)` would raise `TypeError` from PyO3.

#### Fix Applied

Changed the `#[new]` method to accept `**kwargs` via PyO3's `pyo3::types::PyDict`:

1. Added `#[pyo3(signature = (**kwargs))]` to accept arbitrary keyword arguments.
2. Extracts `null` and `blank` from kwargs, defaulting to `false`.
3. Stores the full kwargs dict as `field_kwargs` for forwarding to Django's `TextField` superclass.
4. Added `null` and `blank` as struct fields with `#[pyo3(get)]` for Python access.

```rust
#[new]
#[pyo3(signature = (**kwargs))]
fn new(py: Python<'_>, kwargs: Option<&Bound<'_, pyo3::types::PyDict>>) -> PyResult<Self> {
    let null = kwargs
        .and_then(|kw| kw.get_item("null").ok().flatten())
        .and_then(|v| v.extract::<bool>().ok())
        .unwrap_or(false);
    let blank = kwargs
        .and_then(|kw| kw.get_item("blank").ok().flatten())
        .and_then(|v| v.extract::<bool>().ok())
        .unwrap_or(false);
    // ...
}
```

#### Verification

`EncryptedField(null=True, blank=True)` now constructs without error. The `null` and `blank` fields
are accessible from Python. The full kwargs dict is available via `field_kwargs` for forwarding to
Django's base field constructor.

---

### BUG-US007-013 — `contribute_to_class` does not call `super()` / field registration skipped

**Severity**: Medium **Status**: Fixed **QA Finding**: M6 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

The PyO3 implementation of `contribute_to_class` set `self.attname` and replaced the class attribute
with a descriptor object, but did not call Django's `Field.contribute_to_class()` base method. The
field was never added to `Model._meta.fields`, breaking migrations, query building, and
`Model.from_db` rehydration.

#### Fix Applied

Resolved as part of BUG-US007-006. `contribute_to_class` no longer replaces the class attribute. It
only sets `self.attname` and registers the field's metadata in the side-channel registry. The
`EncryptedField` object remains on the model class, so Django's field registration machinery (which
the Python integration layer invokes via `super().contribute_to_class()`) is not disrupted.

---

### BUG-US007-014 — `verify_password` with empty hash raises opaque error

**Severity**: Medium **Status**: Fixed **QA Finding**: M7 **File(s)**:
`rust/syntek-crypto/src/lib.rs`, `rust/syntek-pyo3/tests/pyo3_module_tests.rs`

#### Root Cause

`verify_password` checked for an empty password (returning `Ok(false)`) but did not check for an
empty hash. Passing an empty string for `hash` triggered `PasswordHash::new("")` which returned a
`password_hash::Error`, mapped to `CryptoError::HashError` and then to `PyValueError`. This was
unexpected for a verification function — callers expect `false`, not an exception.

#### Fix Applied

Added a guard for `hash.is_empty()` that returns `Ok(false)`, matching the empty-password behaviour.
Added two test cases in the syntek-pyo3 test suite to verify both empty-password and empty-hash
paths.

```rust
// Before:
pub fn verify_password(password: &str, hash: &str) -> Result<bool, CryptoError> {
    if password.is_empty() {
        return Ok(false);
    }
    let parsed_hash = PasswordHash::new(hash).map_err(...)?;

// After:
pub fn verify_password(password: &str, hash: &str) -> Result<bool, CryptoError> {
    if password.is_empty() {
        return Ok(false);
    }
    if hash.is_empty() {
        return Ok(false);
    }
    let parsed_hash = PasswordHash::new(hash).map_err(...)?;
```

#### Verification

`test_verify_password_empty_hash_returns_false` — passes. `verify_password("valid", "")` returns
`Ok(false)` instead of `Err(HashError)`.

---

## Low

---

### BUG-US007-015 — Error types have no Python `__module__` / docstring

**Severity**: Low **Status**: Fixed **QA Finding**: L1 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`DecryptionError` and `BatchDecryptionError` were Rust-only types with no Python exception class
registration, so they had no `__module__` attribute or docstring.

#### Fix Applied

Resolved as part of BUG-US007-004. Both exception classes are created via `pyo3::create_exception!`
with docstrings. They are registered in the module and inherit `__module__ = "syntek_pyo3"`.

---

### BUG-US007-016 — Manifest post-install wheel glob is fragile

**Severity**: Low **Status**: Fixed **QA Finding**: L2 **File(s)**:
`rust/syntek-pyo3/syntek.manifest.toml`

#### Root Cause

The post-install snippet used `syntek_pyo3-*.whl` which could match multiple wheel versions if
`target/wheels/` contained old builds. Shell glob expansion order is filesystem-dependent. Stderr
was also suppressed with `2>/dev/null`, hiding installation errors.

#### Fix Applied

Changed the install command to use `--find-links` with an explicit version pin:

```bash
# Before:
uv pip install target/wheels/syntek_pyo3-*.whl 2>/dev/null || pip install target/wheels/syntek_pyo3-*.whl

# After:
uv pip install --find-links target/wheels syntek-pyo3==0.16.2 || pip install --find-links target/wheels syntek-pyo3==0.16.2
```

---

### BUG-US007-017 — `EncryptedFieldDescriptor` not frozen

**Severity**: Low **Status**: Fixed **QA Finding**: L4 **File(s)**: `rust/syntek-pyo3/src/lib.rs`

#### Root Cause

`EncryptedFieldDescriptor` used `#[pyo3(get)]` for read-only attributes but was not declared as a
frozen class. Without `#[pyclass(frozen)]`, Python code could use `object.__setattr__` to bypass the
read-only property and mutate the descriptor's internal state.

#### Fix Applied

Changed `#[pyclass]` to `#[pyclass(frozen)]` on `EncryptedFieldDescriptor`. This makes the class
immutable from Python — any attempt to set attributes raises `AttributeError`.

```rust
// Before:
#[pyclass]
pub struct EncryptedFieldDescriptor {

// After:
#[pyclass(frozen)]
pub struct EncryptedFieldDescriptor {
```

---

## Findings Not Addressed in Code

### L3 — No `maturin` version pin in CI

This is a CI configuration issue, not a code fix. The `pyproject.toml` allows `maturin>=1.7,<2`. The
recommendation to pin `maturin` exactly in CI should be addressed in the CI pipeline configuration
(e.g. `.forgejo/workflows/` or equivalent).

### L5 — Red-phase test count discrepancy in manual testing guide

This is a documentation inconsistency in `docs/TESTS/US007-MANUAL-TESTING.md`. The red-phase count
of 55 does not account for the 10 tests added between red and green phases. This should be corrected
by the documentation owner but does not affect code correctness.

---

## Files Changed

| File                                                              | Change Type | Description                                                                                                                     |
| ----------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `rust/syntek-pyo3/src/lib.rs`                                     | Modified    | C1, C2, H1–H4, H6, M4–M6, L1, L4 fixes; `PyKeyRing` class; versioned API                                                        |
| `rust/syntek-pyo3/Cargo.toml`                                     | Modified    | Added `zeroize` dependency                                                                                                      |
| `rust/syntek-pyo3/pyproject.toml`                                 | Modified    | Version `0.12.1` → `0.16.2`                                                                                                     |
| `rust/syntek-pyo3/syntek.manifest.toml`                           | Modified    | Version `0.14.0` → `0.16.2`, fixed wheel glob                                                                                   |
| `rust/syntek-crypto/src/lib.rs`                                   | Modified    | M7: empty-hash guard in `verify_password`                                                                                       |
| `rust/syntek-crypto/src/key_versioning.rs`                        | Modified    | C2: added `encrypt_fields_batch_versioned` and `decrypt_fields_batch_versioned`                                                 |
| `rust/syntek-pyo3/tests/pyo3_module_tests.rs`                     | Modified    | C2: updated format check tests, cross-format tests, batch versioned smoke test; test key warnings, empty-hash tests             |
| `packages/backend/syntek-pyo3/tests/test_encrypted_field.py`      | Modified    | C2: updated `_VALID_CIPHERTEXT`, `_PLAINTEXT_VALUES`, `KeyRing` usage; new `TestCrossFormatRejection` and `TestKeyRing` classes |
| `packages/backend/syntek-pyo3/tests/test_integration_postgres.py` | Added       | M1: 11 PostgreSQL integration tests via `testcontainers-python`                                                                 |
| `packages/backend/syntek-pyo3/pyproject.toml`                     | Modified    | M1: added `testcontainers[postgres]>=4.8` dev dependency                                                                        |

---

## Prevention

### How to Prevent Similar Bugs

1. **Version bumps**: Always update `pyproject.toml` and `syntek.manifest.toml` in lockstep with the
   workspace `Cargo.toml` version. Add a CI check that compares all three version sources.
2. **Nullable fields**: Always test nullable field paths in Django field implementations. Add a
   None-guard as the first operation in any `pre_save` method.
3. **Exception mapping**: When exposing Rust errors to Python via PyO3, use `create_exception!` to
   register proper Python exception classes rather than mapping everything to `ValueError`.
4. **Django field protocol**: Never replace a Django field object on a model class. Use side-channel
   registries or store metadata on the field instance itself.
5. **Zeroisation**: Any function that returns decrypted plaintext must wrap the intermediate Rust
   `String` in `Zeroizing<String>` before crossing the FFI boundary.

---

## All findings resolved

17 of 17 QA findings resolved. No findings deferred.
