//! US007 — Red phase: Rust-level integration tests for `syntek-pyo3`.
//!
//! These tests verify internal helper functions that the PyO3 bindings rely on.
//! All tests in this file FAIL during the red phase because the functions they
//! call (`is_valid_ciphertext_format`) do not yet exist in `syntek_pyo3`.
//!
//! Run with: `cargo test -p syntek-pyo3`

use base64ct::{Base64, Encoding};

// ---------------------------------------------------------------------------
// AC: Ciphertext format validation helper
//
// The implementation must expose `is_valid_ciphertext_format(s: &str) -> bool`
// which returns true iff `s` is valid base64ct-encoded data whose decoded byte
// length is >= 28 (12-byte nonce + at least 16-byte GCM tag).
// ---------------------------------------------------------------------------

use syntek_pyo3::is_valid_ciphertext_format;

/// Minimum valid ciphertext: 12-byte nonce + 0-byte plaintext + 16-byte GCM tag = 28 bytes.
fn make_blob(byte_count: usize) -> String {
    Base64::encode_string(&vec![0u8; byte_count])
}

#[test]
fn test_exactly_28_decoded_bytes_is_valid() {
    // 28 bytes is the absolute minimum: nonce(12) + tag(16).
    let ct = make_blob(28);
    assert!(is_valid_ciphertext_format(&ct));
}

#[test]
fn test_30_decoded_bytes_is_valid() {
    let ct = make_blob(30);
    assert!(is_valid_ciphertext_format(&ct));
}

#[test]
fn test_100_decoded_bytes_is_valid() {
    // Typical size for a short encrypted string.
    let ct = make_blob(100);
    assert!(is_valid_ciphertext_format(&ct));
}

#[test]
fn test_27_decoded_bytes_is_invalid() {
    // One byte short of the minimum — rejected.
    let ct = make_blob(27);
    assert!(!is_valid_ciphertext_format(&ct));
}

#[test]
fn test_0_decoded_bytes_is_invalid() {
    assert!(!is_valid_ciphertext_format(""));
}

#[test]
fn test_plaintext_email_is_not_valid_ciphertext() {
    assert!(!is_valid_ciphertext_format("user@example.com"));
}

#[test]
fn test_plaintext_with_spaces_is_not_valid_ciphertext() {
    assert!(!is_valid_ciphertext_format("hello world"));
}

#[test]
fn test_invalid_base64_is_not_valid_ciphertext() {
    // Non-base64 characters (!, @, etc.) must be rejected.
    assert!(!is_valid_ciphertext_format("not-valid-base64!!!"));
}

#[test]
fn test_short_valid_base64_below_28_bytes_is_invalid() {
    // 10 bytes of zeros — valid base64 but too short.
    let ct = make_blob(10);
    assert!(!is_valid_ciphertext_format(&ct));
}

#[test]
fn test_real_ciphertext_from_syntek_crypto_passes_format_check() {
    // A ciphertext produced by the real encrypt_field must always pass.
    let key = [0u8; 32];
    let ct = syntek_crypto::encrypt_field("hello@example.com", &key, "User", "email").unwrap();
    assert!(is_valid_ciphertext_format(&ct));
}

// ---------------------------------------------------------------------------
// AC: Error types are defined and convertible to Python exceptions
//
// The implementation must export `DecryptionError` and `BatchDecryptionError`
// as distinct error types (thiserror derives) that PyO3 can map to Python
// exceptions.  These compile-time tests confirm the types exist and impl
// `std::error::Error`.
// ---------------------------------------------------------------------------

use syntek_pyo3::{BatchDecryptionError, DecryptionError};

#[test]
fn test_decryption_error_implements_error_trait() {
    let e: Box<dyn std::error::Error> = Box::new(DecryptionError::new("tampered ciphertext"));
    assert!(!e.to_string().is_empty());
}

#[test]
fn test_batch_decryption_error_carries_field_name() {
    let e = BatchDecryptionError::new("email", "GCM tag mismatch");
    let msg = e.to_string();
    assert!(
        msg.contains("email"),
        "field name missing from BatchDecryptionError: {msg}"
    );
}
