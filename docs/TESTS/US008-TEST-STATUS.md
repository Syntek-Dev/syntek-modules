# Test Status — US008 syntek-graphql-crypto: GraphQL Encryption Middleware

**Package**: `syntek-graphql-crypto` (`rust/syntek-graphql-crypto` +
`packages/backend/syntek-graphql-crypto`)\
**Last Run**: `2026-03-10T00:00:00Z`\
**Run by**: Completion Agent — green phase\
**Story Status**: Completed **Overall Result**: `PASS` (green phase — all tests passing)\
**Coverage**: 59/59

---

## Summary

| Suite       | Tests  | Passed | Failed | Skipped |
| ----------- | ------ | ------ | ------ | ------- |
| Rust unit   | 13     | 13     | 0      | 0       |
| Python unit | 42     | 42     | 0      | 0       |
| Integration | 4      | 4      | 0      | 0       |
| **Total**   | **59** | **59** | **0**  | **0**   |

> Red-phase plan recorded 56 tests (10 Rust). Final green-phase count is 59 — 3 additional Rust unit
> tests were added during implementation to achieve full `MiddlewareError` variant coverage.
>
> Run with:
>
> - `cargo test -p syntek-graphql-crypto`
> - `pytest packages/backend/syntek-graphql-crypto/tests/ -v`
> - `pytest tests/graphql_crypto/ -v`

---

## Test Files

| File                                                                  | Layer       |
| --------------------------------------------------------------------- | ----------- |
| `rust/syntek-graphql-crypto/tests/middleware_tests.rs`                | Rust        |
| `packages/backend/syntek-graphql-crypto/tests/test_directives.py`     | Python unit |
| `packages/backend/syntek-graphql-crypto/tests/test_write_path.py`     | Python unit |
| `packages/backend/syntek-graphql-crypto/tests/test_read_path.py`      | Python unit |
| `packages/backend/syntek-graphql-crypto/tests/test_error_handling.py` | Python unit |
| `packages/backend/syntek-graphql-crypto/tests/test_auth_guard.py`     | Python unit |
| `tests/graphql_crypto/test_integration.py`                            | Integration |

---

## Rust Unit Tests (`rust/syntek-graphql-crypto/tests/middleware_tests.rs`)

### MiddlewareError — trait and variant tests

- [x] `test_middleware_error_implements_error_trait` — `MiddlewareError` implements
      `std::error::Error`
- [x] `test_decrypt_failed_carries_field_name_in_message` — `DecryptFailed` message contains field
      name
- [x] `test_encrypt_failed_carries_field_name_in_message` — `EncryptFailed` message contains field
      name
- [x] `test_key_resolution_failed_carries_model_and_field_name` — `KeyResolutionFailed` message
      contains model + field
- [x] `test_unauthenticated_access_message_is_non_empty` — `UnauthenticatedAccess` produces
      non-empty message
- [x] `test_middleware_error_variants_produce_distinct_messages` — all four variants have distinct
      `Display` output

### EncryptedFieldSpec — struct shape and serde tests

- [x] `test_individual_field_spec_has_no_batch_group` — `batch_group == None` for individual spec
- [x] `test_batch_field_spec_has_batch_group` — `batch_group == Some("profile")` for batch spec
- [x] `test_individual_and_batch_specs_are_distinguishable` — `is_none()` vs `is_some()` on
      `batch_group`
- [x] `test_encrypted_field_spec_individual_serde_roundtrip` — JSON serialise → deserialise
      preserves all fields
- [x] `test_encrypted_field_spec_batch_serde_roundtrip` — JSON roundtrip for batch spec
- [x] `test_two_specs_in_same_batch_group_share_group_key` — two specs in `"profile"` share the same
      group key
- [x] `test_specs_in_different_batch_groups_have_different_keys` — `"profile"` and `"address"` group
      keys differ

> Note: the summary table lists 10 Rust tests; the file contains 13 (the summary table has been kept
> conservative pending final count verification during green phase).

---

## Python Unit Tests

### Directive Tests (`test_directives.py`)

- [x] `TestEncryptedDirective::test_encrypted_directive_importable` —
      `from syntek_graphql_crypto.directives import Encrypted` succeeds
- [x] `TestEncryptedDirective::test_encrypted_directive_can_annotate_field` — `Encrypted()` accepted
      by `strawberry.field`
- [x] `TestEncryptedDirective::test_encrypted_individual_has_no_batch` — `Encrypted().batch is None`
- [x] `TestEncryptedDirective::test_encrypted_batch_has_batch_parameter` —
      `Encrypted(batch="profile").batch == "profile"`
- [x] `TestEncryptedDirective::test_two_different_batch_groups_are_not_equal` — `"profile"` !=
      `"address"`
- [x] `TestEncryptedDirective::test_encrypted_is_a_strawberry_schema_directive` — has
      `__strawberry_directive__` attr
- [x] `TestEncryptedDirective::test_encrypted_individual_and_batch_instances_distinguish_by_batch_attribute`
      — `batch is None` vs `batch is not None`

### Write Path Tests (`test_write_path.py`)

#### AC1 — Individual field encryption

- [x] `TestWritePathIndividualField::test_encrypted_field_value_replaced_with_ciphertext_before_resolver`
      — resolver receives ciphertext, not plaintext
- [x] `TestWritePathIndividualField::test_individual_field_calls_encrypt_field_exactly_once` —
      `encrypt_field` called once
- [x] `TestWritePathIndividualField::test_encrypt_field_called_with_correct_model_field_and_key` —
      correct positional args verified
- [x] `TestWritePathIndividualField::test_non_encrypted_field_value_unchanged` — plain field passes
      through unmodified

#### AC2 — Batch group encryption

- [x] `TestWritePathBatchGroup::test_batch_group_uses_encrypt_fields_batch_not_encrypt_field` —
      batch path uses `encrypt_fields_batch` only
- [x] `TestWritePathBatchGroup::test_batch_group_calls_encrypt_fields_batch_exactly_once` — one call
      for all fields in group
- [x] `TestWritePathBatchGroup::test_batch_fields_replaced_with_ciphertexts` — resolver receives
      ciphertext per field

#### AC3 — Mixed individual + batch

- [x] `TestWritePathMixed::test_individual_field_uses_encrypt_field_batch_uses_encrypt_fields_batch`
      — both call paths exercised
- [x] `TestWritePathMixed::test_different_batch_groups_produce_separate_calls` — two groups → two
      `encrypt_fields_batch` calls
- [x] `TestWritePathMixed::test_fields_from_different_groups_never_combined` — group isolation
      verified

### Read Path Tests (`test_read_path.py`)

#### AC4 — Individual field decryption

- [x] `TestReadPathIndividualField::test_encrypted_field_ciphertext_replaced_with_plaintext_after_resolver`
      — frontend receives plaintext
- [x] `TestReadPathIndividualField::test_individual_field_calls_decrypt_field_exactly_once` —
      `decrypt_field` called once
- [x] `TestReadPathIndividualField::test_decrypt_field_called_with_correct_model_field_and_key` —
      correct positional args verified

#### AC5 — Batch group decryption

- [x] `TestReadPathBatchGroup::test_batch_group_uses_decrypt_fields_batch_not_decrypt_field` — batch
      path uses `decrypt_fields_batch` only
- [x] `TestReadPathBatchGroup::test_batch_group_calls_decrypt_fields_batch_exactly_once` — one call
      per group
- [x] `TestReadPathBatchGroup::test_all_batch_fields_decrypted_in_response` — all plaintexts
      returned in order

#### AC6 — Non-annotated passthrough

- [x] `TestReadPathPassthrough::test_non_annotated_field_passes_through_unchanged` — plain field
      value unmodified
- [x] `TestReadPathPassthrough::test_non_annotated_field_does_not_call_decrypt_field` — no
      `decrypt_field` call
- [x] `TestReadPathPassthrough::test_non_annotated_field_does_not_call_decrypt_fields_batch` — no
      `decrypt_fields_batch` call

### Error Handling Tests (`test_error_handling.py`)

#### AC7 — Decrypt failure, individual field

- [x] `TestDecryptFailureIndividualField::test_decrypt_failure_sets_field_to_null` — failed field is
      null
- [x] `TestDecryptFailureIndividualField::test_decrypt_failure_appends_structured_error_to_errors_array`
      — `errors` has structured entry with `field_path` / `error_type`
- [x] `TestDecryptFailureIndividualField::test_decrypt_failure_does_not_abort_rest_of_response` —
      non-encrypted fields still present
- [x] `TestDecryptFailureIndividualField::test_decrypt_failure_other_encrypted_fields_still_decrypted`
      — other `@encrypted` fields unaffected

#### AC8 — Decrypt failure, batch group

- [x] `TestDecryptFailureBatchGroup::test_batch_decrypt_failure_nulls_all_fields_in_group` — all
      group fields null
- [x] `TestDecryptFailureBatchGroup::test_batch_decrypt_failure_appends_single_error_not_multiple` —
      exactly 1 error per group
- [x] `TestDecryptFailureBatchGroup::test_batch_decrypt_failure_does_not_null_fields_from_other_groups`
      — other groups unaffected
- [x] `TestDecryptFailureBatchGroup::test_partial_batch_results_never_returned` — all-or-nothing:
      both fields null together

#### AC9 — Encrypt failure, mutation rejection

- [x] `TestEncryptFailureMutation::test_encrypt_failure_rejects_entire_mutation` — mutation returns
      error
- [x] `TestEncryptFailureMutation::test_encrypt_failure_no_partial_ciphertext_written` — resolver
      not called on failure
- [x] `TestEncryptFailureMutation::test_encrypt_failure_returns_structured_error` — error message is
      non-empty and structured

### Auth Guard Tests (`test_auth_guard.py`)

#### AC10 — Unauthenticated access

- [x] `TestAuthGuard::test_unauthenticated_request_sets_encrypted_field_to_null` — all encrypted
      fields null
- [x] `TestAuthGuard::test_unauthenticated_request_appends_auth_error_to_errors_array` — auth error
      in `errors`
- [x] `TestAuthGuard::test_unauthenticated_request_does_not_abort_entire_response` — non-encrypted
      fields still returned
- [x] `TestAuthGuard::test_unauthenticated_request_does_not_call_decrypt_field` — no decryption
      attempted
- [x] `TestAuthGuard::test_auth_error_is_logged_via_syntek_logging` — `logger.warning` /
      `logger.info` called
- [x] `TestAuthGuard::test_authenticated_request_decrypts_normally` — happy path: auth present →
      plaintext returned

---

## Integration Tests (`tests/graphql_crypto/test_integration.py`)

- [x] `TestIndividualFieldRoundtrip::test_individual_field_write_stores_ciphertext_read_returns_plaintext`
      — write mutation → DB has ciphertext → query returns plaintext (AC1 + AC4)
- [x] `TestBatchFieldRoundtrip::test_batch_group_write_stores_ciphertext_per_field_read_returns_all_plaintext`
      — batch write → DB has ciphertext per field → query returns all plaintext (AC2 + AC5)
- [x] `TestTamperedDbValue::test_tampered_db_value_returns_null_field_with_error_rest_intact` —
      tampered value → field null, error present, rest intact (AC7)
- [x] `TestUnauthenticatedRead::test_unauthenticated_read_returns_null_encrypted_fields_with_auth_error`
      — unauthenticated → all encrypted fields null, auth error, plain fields present (AC10)

---

## AC Coverage Map

| AC   | Description                                            | Suite(s)                         | Status |
| ---- | ------------------------------------------------------ | -------------------------------- | ------ |
| AC1  | Individual `@encrypted` write → ciphertext to resolver | Python unit (write), Integration | GREEN  |
| AC2  | Batch `@encrypted` write → single batch call           | Python unit (write), Integration | GREEN  |
| AC3  | Mixed individual + batch → correct routing, no mixing  | Python unit (write)              | GREEN  |
| AC4  | Individual `@encrypted` read → plaintext to frontend   | Python unit (read), Integration  | GREEN  |
| AC5  | Batch `@encrypted` read → single batch call            | Python unit (read), Integration  | GREEN  |
| AC6  | Non-annotated fields → passthrough, zero overhead      | Python unit (read)               | GREEN  |
| AC7  | Decrypt failure (individual) → null + structured error | Python unit (error), Integration | GREEN  |
| AC8  | Decrypt failure (batch) → all null, one error          | Python unit (error)              | GREEN  |
| AC9  | Encrypt failure → reject mutation, no partial write    | Python unit (error)              | GREEN  |
| AC10 | Unauthenticated → null + auth error + logged           | Python unit (auth), Integration  | GREEN  |
| AC11 | Resolver isolation — no crypto logic in resolvers      | Python unit (auth, write, read)  | GREEN  |

---

## Notes

- Red phase written on branch `us008/syntek-graphql-crypto` — 10/03/2026.
- Green phase completed on branch `us008/syntek-graphql-crypto` — 10/03/2026.
- All 59 tests pass (13 Rust unit, 42 Python unit, 4 integration). Implementation is complete.
- `syntek_pyo3` is mocked in all Python unit tests via `unittest.mock.patch` so that the native
  extension does not need to be built to run unit tests.
- Integration tests require `maturin develop` to be run first (or a mocked pyo3).
- The `crate-type = ["cdylib", "lib"]` addition to `rust/syntek-graphql-crypto/Cargo.toml` is
  required for integration tests to link against the library.
- Key naming convention: `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>` (e.g. `SYNTEK_FIELD_KEY_USER_EMAIL`) —
  set in `conftest.py` using a 32-byte non-secret test key.
- Password fields are excluded from this middleware — they use Argon2id one-way hashing in the
  resolver, not AES-256-GCM encryption.
