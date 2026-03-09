# Test Status — US007 syntek-pyo3: PyO3 Django Bindings

**Package**: `syntek-pyo3` (`rust/syntek-pyo3`)\
**Last Run**: `2026-03-09T00:00:00Z`\
**Run by**: Backend Agent — green phase\
**Story Status**: Completed **Overall Result**: `PASS` (green phase — all tests pass)\
**Coverage**: Full (65/65 tests)

---

## Summary

| Suite       | Tests  | Passed | Failed | Skipped |
| ----------- | ------ | ------ | ------ | ------- |
| Rust unit   | 12     | 12     | 0      | 0       |
| Python unit | 53     | 53     | 0      | 0       |
| Integration | 0      | 0      | 0      | 0       |
| E2E         | 0      | 0      | 0      | 0       |
| **Total**   | **65** | **65** | **0**  | **0**   |

> Run with `cargo test -p syntek-pyo3` (Rust) and
> `pytest tests/pyo3/ packages/backend/syntek-pyo3/tests/ -v` (Python, after `maturin develop`). All
> functions fully implemented.

---

## Test Files

| File                                                         | Layer  |
| ------------------------------------------------------------ | ------ |
| `rust/syntek-pyo3/tests/pyo3_module_tests.rs`                | Rust   |
| `tests/pyo3/test_pyo3_bindings.py`                           | Python |
| `packages/backend/syntek-pyo3/tests/test_encrypted_field.py` | Django |

---

## Rust Unit Tests (`rust/syntek-pyo3/tests/pyo3_module_tests.rs`)

### Ciphertext format validation — `is_valid_ciphertext_format`

- [x]`test_exactly_28_decoded_bytes_is_valid` — 28-byte blob (nonce + empty tag) passes
- [x]`test_30_decoded_bytes_is_valid` — typical short ciphertext passes
- [x]`test_100_decoded_bytes_is_valid` — larger ciphertext passes
- [x]`test_27_decoded_bytes_is_invalid` — one byte short of minimum is rejected
- [x]`test_0_decoded_bytes_is_invalid` — empty string is rejected
- [x]`test_plaintext_email_is_not_valid_ciphertext` — `user@example.com` is rejected
- [x]`test_plaintext_with_spaces_is_not_valid_ciphertext` — `hello world` is rejected
- [x]`test_invalid_base64_is_not_valid_ciphertext` — `not-valid-base64!!!` is rejected
- [x]`test_short_valid_base64_below_28_bytes_is_invalid` — 10 decoded bytes rejected
- [x]`test_real_ciphertext_from_syntek_crypto_passes_format_check` — `encrypt_field` output passes

### Error types compile-time tests

- [x]`test_decryption_error_implements_error_trait` — `DecryptionError` implements
  `std::error::Error`
- [x]`test_batch_decryption_error_carries_field_name` — `BatchDecryptionError` carries the field
  name

---

## Python Binding Tests (`tests/pyo3/test_pyo3_bindings.py`)

### AC1 — Module import

- [x]`TestModuleImport::test_import_encrypt_field`
- [x]`TestModuleImport::test_import_decrypt_field`
- [x]`TestModuleImport::test_import_encrypt_fields_batch`
- [x]`TestModuleImport::test_import_decrypt_fields_batch`
- [x]`TestModuleImport::test_import_hash_password`
- [x]`TestModuleImport::test_import_verify_password`
- [x]`TestModuleImport::test_all_six_symbols_importable_at_once`

### AC: encrypt_field

- [x]`TestEncryptField::test_returns_non_empty_string`
- [x]`TestEncryptField::test_two_calls_produce_different_ciphertexts` — nonce uniqueness
- [x]`TestEncryptField::test_invalid_key_length_raises`

### AC: decrypt_field

- [x]`TestDecryptField::test_roundtrip_recovers_original_plaintext`
- [x]`TestDecryptField::test_unicode_plaintext_round_trips`
- [x]`TestDecryptField::test_tampered_ciphertext_raises`
- [x]`TestDecryptField::test_invalid_base64_raises`
- [x]`TestDecryptField::test_wrong_key_raises`
- [x]`TestDecryptField::test_aad_model_mismatch_raises`
- [x]`TestDecryptField::test_aad_field_mismatch_raises`
- [x]`TestDecryptField::test_failure_raises_exception_not_returns_none`

### AC: encrypt_fields_batch

- [x]`TestEncryptFieldsBatch::test_returns_list_of_correct_length`
- [x]`TestEncryptFieldsBatch::test_preserves_field_order`
- [x]`TestEncryptFieldsBatch::test_empty_input_returns_empty_list`
- [x]`TestEncryptFieldsBatch::test_invalid_key_raises`

### AC: decrypt_fields_batch

- [x]`TestDecryptFieldsBatch::test_roundtrip_recovers_all_plaintexts`
- [x]`TestDecryptFieldsBatch::test_one_tampered_field_raises_for_entire_batch`
- [x]`TestDecryptFieldsBatch::test_empty_input_returns_empty_list`

### AC: hash_password

- [x]`TestHashPassword::test_returns_argon2id_phc_string`
- [x]`TestHashPassword::test_empty_password_raises`
- [x]`TestHashPassword::test_two_calls_produce_different_hashes`

### AC: verify_password

- [x]`TestVerifyPassword::test_correct_password_returns_true`
- [x]`TestVerifyPassword::test_wrong_password_returns_false`
- [x]`TestVerifyPassword::test_empty_candidate_returns_false`

---

## Django EncryptedField Tests (`packages/backend/syntek-pyo3/tests/test_encrypted_field.py`)

### AC1 — Import

- [x]`TestEncryptedFieldImport::test_encrypted_field_importable`
- [x]`TestEncryptedFieldImport::test_encrypted_field_descriptor_importable`

### AC2 — Accepts valid ciphertext

- [x]`TestEncryptedFieldAcceptsCiphertext::test_valid_ciphertext_fixture_passes_validation`
- [x]`TestEncryptedFieldAcceptsCiphertext::test_real_ciphertext_from_encrypt_field_passes`
- [x]`TestEncryptedFieldAcceptsCiphertext::test_pre_save_returns_ciphertext_unchanged`

### AC3 — Rejects plaintext (6 × 2 parametrised = 12 tests)

- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[hello@example.com]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[plaintext value]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[short]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[not-base64!!!]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_validate_raises_validation_error_for_plaintext[ ]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[hello@example.com]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[plaintext value]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[short]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[not-base64!!!]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[]`
- [x]`TestEncryptedFieldRejectsPlaintext::test_pre_save_raises_validation_error_for_plaintext[ ]`

### AC4 — from_db_value passthrough

- [x]`TestFromDbValue::test_returns_ciphertext_unchanged`
- [x]`TestFromDbValue::test_returns_none_for_null_db_value`
- [x]`TestFromDbValue::test_does_not_call_decrypt_field`

### EncryptedFieldDescriptor

- [x]`TestEncryptedFieldDescriptor::test_contribute_to_class_sets_descriptor_with_model_and_field_name`
- [x]`TestEncryptedFieldDescriptor::test_descriptor_is_instance_of_encrypted_field_descriptor`

---

## Integration Tests

> Not applicable at this layer — integration with the full Django ORM roundtrip (DB read/write) is
> covered in the green phase manual scenarios.

---

## E2E Tests

> Not applicable — no UI or HTTP boundary is exercised by this crate.

---

## AC Coverage Map

| AC  | Tests                                                                        | Status |
| --- | ---------------------------------------------------------------------------- | ------ |
| AC1 | `TestModuleImport` (7 tests), `TestEncryptedFieldImport` (2 tests)           | GREEN  |
| AC2 | `TestEncryptedFieldAcceptsCiphertext` (3 tests)                              | GREEN  |
| AC3 | `TestEncryptedFieldRejectsPlaintext` (12 parametrised tests)                 | GREEN  |
| AC4 | `TestFromDbValue` (3 tests)                                                  | GREEN  |
| AC5 | `TestDecryptField::test_tampered_ciphertext_raises`, `test_wrong_key_raises` | GREEN  |
| AC6 | `TestEncryptFieldsBatch` (4 tests)                                           | GREEN  |
| AC7 | `TestDecryptFieldsBatch` (3 tests)                                           | GREEN  |
| AC8 | Covered by `maturin develop` manual scenario — no automated test             | —      |

---

## Notes

- Red phase written on branch `us007/syntek-pyo3` — 09/03/2026.
- Green phase completed on branch `us007/syntek-pyo3` — 09/03/2026.
- Implementation: `syntek_pyo3` native extension built with PyO3 0.28 + maturin 1.8, delegating all
  crypto to `syntek-crypto`. `EncryptedField` and `EncryptedFieldDescriptor` implemented as
  `#[pyclass]` types.
- Ciphertext format validation: valid base64ct AND decoded length >= 28 bytes.
- Django's `ValidationError` raised directly from Rust via
  `PyModule::import(py, "django.core.exceptions")`.
- `from_db_value` is a pure passthrough — decryption is the GraphQL middleware's responsibility.
- Root `conftest.py` added at repo root to ensure `sys.path` includes the repo root for all pytest
  invocations.
- Rust integration tests require `crate-type = ["cdylib", "lib"]` — added to
  `rust/syntek-pyo3/Cargo.toml`.
- Python binding tests live in `tests/pyo3/` (global scope — the extension is cross-cutting).
- Django EncryptedField tests live in `packages/backend/syntek-pyo3/tests/` (module scope).
- The `_VALID_CIPHERTEXT` fixture (`base64(b'\x00' * 30)`) has 30 decoded bytes ≥ 28 minimum; it is
  not a real AES-GCM ciphertext — EncryptedField validates format only, not decryptability.
- Password tests are not covered by `EncryptedField` — passwords use Argon2id one-way hashing, not
  AES-256-GCM encryption.
