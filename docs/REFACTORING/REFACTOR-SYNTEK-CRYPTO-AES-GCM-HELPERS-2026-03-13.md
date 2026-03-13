# Refactoring Plan: syntek-crypto — Extract Shared AES-256-GCM Helpers

**Date:** 13/03/2026 **Author:** Syntek Development Team **Branch:** us010/syntek-tenancy **Related
Bug:** BUG-US006-009 (Medium)

---

## Analysis

- **Files Affected:**
  - `rust/syntek-crypto/src/lib.rs`
  - `rust/syntek-crypto/src/key_versioning.rs`
  - `rust/syntek-crypto/src/aes_gcm.rs` (new)
- **Test Coverage:** Full — 80 tests (42 unit, 29 key-versioning, 9 doc-tests), all passing
- **Risk Level:** Low — pure structural extraction, no behavioural change

---

## Code Smells Identified

1. **Duplicated AES-256-GCM implementation:** The AES-256-GCM encrypt and decrypt routines existed
   in two places — `lib.rs` (`encrypt_field`, `decrypt_field`) and `key_versioning.rs`
   (`encrypt_versioned`, `decrypt_versioned`). Any future fix or algorithm change had to be applied
   in two locations.

2. **Repeated AAD pattern:** The expression `format!("{}:{}", model, field)` appeared in four
   function bodies across two files.

3. **Inline `use` statements in function bodies:** `encrypt_versioned` and `decrypt_versioned` each
   imported `aes_gcm`, `base64ct`, and `rand` via inline `use` blocks inside the function body
   rather than at module level.

---

## Proposed Changes

### Change 1: Extract `src/aes_gcm.rs` with two `pub(crate)` helpers

**New file:** `rust/syntek-crypto/src/aes_gcm.rs`

Two crate-internal helpers:

- `pub(crate) fn aes_gcm_encrypt(plaintext: &str, key: &[u8], aad: &[u8]) -> Result<String, CryptoError>`
  Encrypts `plaintext` with AES-256-GCM using a caller-supplied 32-byte `key` and `aad` slice.
  Returns `base64( nonce(12) || ciphertext || tag(16) )`.

- `pub(crate) fn aes_gcm_decrypt(ciphertext: &str, key: &[u8], aad: &[u8]) -> Result<String, CryptoError>`
  Decrypts a blob produced by `aes_gcm_encrypt`. Performs base64 decode, nonce extraction, GCM
  decrypt, and UTF-8 validation.

Both helpers accept `aad` as a `&[u8]` parameter. Callers construct the AAD string however they
require and pass `.as_bytes()`.

**Reason:** Single canonical implementation of AES-256-GCM. All future changes (algorithm
parameters, nonce size, error messages) need only be applied once.

---

### Change 2: Update `src/lib.rs`

- Registered the new module with `mod aes_gcm;`.
- Removed the `aes_gcm` crate imports (`Aes256Gcm`, `Key`, `Nonce`, `Aead`, `AeadCore`, `KeyInit`,
  `Payload`) that were used only by `encrypt_field` and `decrypt_field`.
- Removed the `base64ct` top-level import (no longer needed by `lib.rs` at module scope; it is
  re-imported locally inside `decrypt_field` to preserve the guard ordering).
- `encrypt_field` now validates the key length then delegates to `aes_gcm::aes_gcm_encrypt`.
- `decrypt_field` preserves the original guard order (base64 decode → length check → key-length
  check) before delegating to `aes_gcm::aes_gcm_decrypt`. The guard order is required because tests
  assert `DecryptionError` (not `InvalidInput`) for a wrong-length key, which is only reachable
  after the blob length guard.

---

### Change 3: Update `src/key_versioning.rs`

- Added module-level imports: `use base64ct::{Base64, Encoding}` and
  `use crate::aes_gcm::{aes_gcm_decrypt, aes_gcm_encrypt}`.
- Removed the inline `use` blocks that had been placed inside `encrypt_versioned` and
  `decrypt_versioned`.
- `encrypt_versioned` now:
  1. Calls `aes_gcm_encrypt` to obtain `base64( nonce || ciphertext || tag )`.
  2. Decodes the result, prepends the 2-byte version prefix, re-encodes.
- `decrypt_versioned` now:
  1. Decodes the full blob and checks the minimum length.
  2. Strips the 2-byte version prefix and re-encodes the remaining bytes as base64.
  3. Passes that re-encoded string to `aes_gcm_decrypt`.
- `reencrypt_to_active` had its inline `use base64ct` removed; the module-level import covers it.

---

## New Shared Code Created

- `/rust/syntek-crypto/src/aes_gcm.rs` — canonical AES-256-GCM encrypt/decrypt primitives for
  internal reuse within the `syntek-crypto` crate

---

## Verification

- All 80 tests pass: `cargo test -p syntek-crypto`
- Clippy clean: `cargo clippy -p syntek-crypto -- -D warnings`
- No public API surface added
- No behaviour changes — same inputs produce same outputs
