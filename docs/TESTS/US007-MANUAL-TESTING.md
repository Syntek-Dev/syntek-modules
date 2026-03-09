# Manual Testing Guide — US007: syntek-pyo3

**Package**: `syntek-pyo3` (`rust/syntek-pyo3/`)\
**Last Updated**: `2026-03-09`\
**Story Status**: Completed\
**Tested against**: Rust stable (edition 2024) / Python 3.14 / Django 6.0

---

## Overview

`syntek-pyo3` is the PyO3 bridge that exposes `syntek-crypto` to Django. It builds a native Python
extension module (`syntek_pyo3.so`) and provides the `EncryptedField` Django model field.

A tester should verify that: the extension imports without error after `maturin develop`; encryption
and decryption round-trips correctly via Python; the `EncryptedField` accepts real ciphertexts and
rejects plaintext before any DB write; `from_db_value` returns ciphertext as-is; batch operations
return results in input order; and tampered ciphertexts raise errors with no partial plaintext
leakage.

---

## Prerequisites

Before testing, ensure the following are in place:

- [x]Rust stable toolchain is installed: `rustup show` — confirm `stable` is active
- [x]Python 3.14 venv is active: `source .venv/bin/activate`
- [x]maturin is installed: `pip show maturin` or `uv pip show maturin`
- [x]You are in the repo root: `cd /path/to/syntek-modules`
- [x](Green phase only) `maturin develop` has been run in `rust/syntek-pyo3/`:
  `cd rust/syntek-pyo3 && maturin develop`
- [x](Red phase only) Tests are expected to FAIL — do not run `maturin develop`

---

## Test Scenarios

### Scenario 1 — Red phase: automated tests all fail (historical — red phase complete)

**What this tests**: Confirms the test suite is correctly written before implementation. Red phase
passed as expected on 09/03/2026 — all 65 tests failed prior to implementation, confirming correct
test construction.

#### Steps

```bash
# Rust tests — expect compilation failure (symbols do not exist)
cargo test -p syntek-pyo3

# Python binding tests — expect ImportError
pytest tests/pyo3/ -v

# Django field tests — expect ImportError
pytest packages/backend/syntek-pyo3/tests/ -v
```

#### Expected Result

- [x]`cargo test -p syntek-pyo3` fails to compile with "cannot find function
  `is_valid_ciphertext_format`" and similar errors
- [x]`pytest tests/pyo3/` — all tests FAIL with
  `ImportError: cannot import name 'encrypt_field' from 'syntek_pyo3'`
- [x]`pytest packages/backend/syntek-pyo3/tests/` — all tests FAIL with
  `ImportError: cannot import name 'EncryptedField' from 'syntek_pyo3'`
- [x]Total: 55 FAIL, 0 PASS

---

### Scenario 2 — Green phase: maturin develop and import check

**What this tests**: The compiled extension loads cleanly in the active `.venv`.

#### Setup

```bash
source .venv/bin/activate
cd rust/syntek-pyo3
maturin develop
cd ../..
```

#### Steps

```bash
python -c "
from syntek_pyo3 import (
    encrypt_field, decrypt_field,
    encrypt_fields_batch, decrypt_fields_batch,
    hash_password, verify_password,
    EncryptedField, EncryptedFieldDescriptor,
)
print('Import OK')
"
```

#### Expected Result

- [x]Command prints `Import OK` with no traceback
- [x]No `ImportError`, `AttributeError`, or segfault

---

### Scenario 3 — Encrypt/decrypt round-trip via Python

**What this tests**: `encrypt_field` and `decrypt_field` delegate to `syntek-crypto` correctly.

#### Steps

```python
from syntek_pyo3 import encrypt_field, decrypt_field

key = bytes(range(32))  # 32-byte key — not for production use
ct = encrypt_field("hello@example.com", key, "User", "email")
print(f"Ciphertext: {ct}")
print(f"Length: {len(ct)} chars")

recovered = decrypt_field(ct, key, "User", "email")
print(f"Recovered: {recovered}")
assert recovered == "hello@example.com", "Round-trip FAIL"
print("Round-trip: PASS")
```

#### Expected Result

- [x]Ciphertext is a non-empty base64 string
- [x]`Recovered: hello@example.com`
- [x]`Round-trip: PASS`

---

### Scenario 4 — Tampered ciphertext raises DecryptionError

**What this tests**: No partial plaintext is returned on GCM tag failure.

#### Steps

```python
from syntek_pyo3 import encrypt_field, decrypt_field

key = bytes(range(32))
ct = encrypt_field("secret", key, "User", "email")
corrupted = ct[:-1] + ("A" if ct[-1] != "A" else "B")

try:
    decrypt_field(corrupted, key, "User", "email")
    print("Tamper test: FAIL — no exception raised")
except Exception as e:
    print(f"Tamper test: PASS — raised {type(e).__name__}: {e}")
```

#### Expected Result

- [x]An exception is raised (not `None` returned)
- [x]The exception message does not contain the original plaintext
- [x]`Tamper test: PASS`

---

### Scenario 5 — EncryptedField accepts ciphertext, rejects plaintext

**What this tests**: The Django field's defence-in-depth guard.

#### Steps

```python
import django
from django.conf import settings
settings.configure(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}, INSTALLED_APPS=[])
django.setup()

import base64
from django.core.exceptions import ValidationError
from syntek_pyo3 import EncryptedField, encrypt_field

field = EncryptedField()
key = bytes(range(32))

# Should pass — real ciphertext
ct = encrypt_field("hello@example.com", key, "User", "email")
field.validate(ct, model_instance=None)
print("Ciphertext accepted: PASS")

# Should fail — plaintext
try:
    field.validate("hello@example.com", model_instance=None)
    print("Plaintext accepted: FAIL")
except ValidationError:
    print("Plaintext rejected: PASS")
```

#### Expected Result

- [x]`Ciphertext accepted: PASS`
- [x]`Plaintext rejected: PASS`

---

### Scenario 6 — from_db_value passthrough (no decryption)

**What this tests**: The ORM layer does not decrypt — that is the GraphQL middleware's job.

#### Steps

```python
import base64
from syntek_pyo3 import EncryptedField

field = EncryptedField()
ct = base64.b64encode(b"\x00" * 30).decode()

result = field.from_db_value(ct, expression=None, connection=None)
assert result == ct, f"from_db_value changed the value: {result!r}"
print("from_db_value passthrough: PASS")

null_result = field.from_db_value(None, expression=None, connection=None)
assert null_result is None
print("from_db_value None passthrough: PASS")
```

#### Expected Result

- [x]`from_db_value passthrough: PASS`
- [x]`from_db_value None passthrough: PASS`

---

### Scenario 7 — Batch encrypt/decrypt via Python

**What this tests**: Batch operations return results in input order; one failure aborts the batch.

#### Steps

```python
from syntek_pyo3 import encrypt_fields_batch, decrypt_fields_batch

key = bytes(range(32))
fields = [("email", "a@example.com"), ("phone", "+441234567890")]

encrypted = encrypt_fields_batch(fields, key, "User")
assert len(encrypted) == 2
print(f"Batch encrypt count: {len(encrypted)} — PASS")

pairs = [("email", encrypted[0]), ("phone", encrypted[1])]
decrypted = decrypt_fields_batch(pairs, key, "User")
assert decrypted == ["a@example.com", "+441234567890"]
print("Batch decrypt order preserved: PASS")

# One tampered field aborts the whole batch
try:
    decrypt_fields_batch([("email", encrypted[0]), ("phone", "bad!!!")], key, "User")
    print("Batch tamper: FAIL — no exception")
except Exception as e:
    print(f"Batch tamper rejected: PASS — {type(e).__name__}")
```

#### Expected Result

- [x]`Batch encrypt count: 2 — PASS`
- [x]`Batch decrypt order preserved: PASS`
- [x]`Batch tamper rejected: PASS`

---

### Scenario 8 — EncryptedFieldDescriptor records model + field name

**What this tests**: The GraphQL middleware can resolve AAD automatically.

#### Steps

```python
from syntek_pyo3 import EncryptedField, EncryptedFieldDescriptor

class User:
    pass

field = EncryptedField()
field.contribute_to_class(User, "email")

descriptor = User.__dict__["email"]
assert isinstance(descriptor, EncryptedFieldDescriptor), f"Got {type(descriptor)}"
assert descriptor.model_name == "User"
assert descriptor.field_name == "email"
print(f"Descriptor: model={descriptor.model_name}, field={descriptor.field_name} — PASS")
```

#### Expected Result

- [x]`Descriptor: model=User, field=email — PASS`

---

## Regression Checklist

Run before marking the US007 PR ready for review:

- [x] All 65 automated tests pass: `cargo test -p syntek-pyo3` +
      `pytest tests/pyo3/ packages/backend/syntek-pyo3/tests/ -v`
- [x]Clippy is clean: `cargo clippy -p syntek-pyo3 -- -D warnings`
- [x]Code is formatted: `cargo fmt -p syntek-pyo3 -- --check`
- [x]Scenario 2 (maturin import) passes
- [x]Scenario 3 (round-trip) passes
- [x]Scenario 4 (tamper rejection) passes
- [x]Scenario 5 (EncryptedField accept/reject) passes
- [x]Scenario 6 (from_db_value passthrough) passes
- [x]Scenario 7 (batch ops) passes
- [x]Scenario 8 (descriptor) passes
- [x]No `unsafe` blocks: `grep -r "unsafe" rust/syntek-pyo3/src/` — none
- [x]No secrets or test keys committed to source

---

## Known Issues

_None. All scenarios passed on 09/03/2026 (green phase)._
