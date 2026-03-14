//! US007 — Rust-level integration tests for `syntek-pyo3`.
//!
//! These tests verify the `is_valid_ciphertext_format` helper, the error-type
//! exports, and the cross-format incompatibility between the unversioned and
//! versioned ciphertext layouts (C2 fix).
//!
//! Run with: `cargo test -p syntek-pyo3`

use base64ct::{Base64, Encoding};
use syntek_pyo3::is_valid_ciphertext_format;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Encode `byte_count` zero-bytes as base64.
fn make_blob(byte_count: usize) -> String {
    Base64::encode_string(&vec![0u8; byte_count])
}

/// Make a synthetic versioned blob: version(2, big-endian) || zeros(rest).
/// `version` must be >= 1.  Total decoded length = `2 + rest_len`.
fn make_versioned_blob(version: u16, rest_len: usize) -> String {
    let mut buf = Vec::with_capacity(2 + rest_len);
    buf.extend_from_slice(&version.to_be_bytes());
    buf.extend(std::iter::repeat_n(0u8, rest_len));
    Base64::encode_string(&buf)
}

// ---------------------------------------------------------------------------
// AC: Ciphertext format validation helper
//
// Versioned layout: base64( version(2) || nonce(12) || ciphertext || tag(16) )
// Minimum decoded length: 30 bytes.  Version must be >= 1.
// ---------------------------------------------------------------------------

#[test]
fn test_exactly_30_bytes_version_one_is_valid() {
    // 30 bytes is the minimum: version(2) + nonce(12) + tag(16).
    let ct = make_versioned_blob(1, 28);
    assert!(is_valid_ciphertext_format(&ct));
}

#[test]
fn test_exactly_30_bytes_high_version_is_valid() {
    let ct = make_versioned_blob(65535, 28);
    assert!(is_valid_ciphertext_format(&ct));
}

#[test]
fn test_100_decoded_bytes_version_one_is_valid() {
    let ct = make_versioned_blob(1, 98);
    assert!(is_valid_ciphertext_format(&ct));
}

// Regressions — these were previously accepted under the 28-byte check.

#[test]
fn test_exactly_28_decoded_bytes_is_now_invalid() {
    // 28 bytes is the OLD minimum (unversioned layout).
    // Under the new versioned-only check it is too short.
    let ct = make_blob(28);
    assert!(!is_valid_ciphertext_format(&ct));
}

#[test]
fn test_29_decoded_bytes_is_invalid() {
    let ct = make_blob(29);
    assert!(!is_valid_ciphertext_format(&ct));
}

#[test]
fn test_exactly_30_bytes_version_zero_is_invalid() {
    // version 0 is reserved — must be rejected even if length is >= 30.
    let ct = make_blob(30); // all zeros → version = 0x0000 = 0
    assert!(!is_valid_ciphertext_format(&ct));
}

#[test]
fn test_27_decoded_bytes_is_invalid() {
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
    assert!(!is_valid_ciphertext_format("not-valid-base64!!!"));
}

#[test]
fn test_short_valid_base64_below_30_bytes_is_invalid() {
    let ct = make_blob(10);
    assert!(!is_valid_ciphertext_format(&ct));
}

// ---------------------------------------------------------------------------
// C2 fix: versioned ciphertext from encrypt_versioned passes format check
// ---------------------------------------------------------------------------

#[test]
fn test_versioned_ciphertext_passes_format_check() {
    // TEST KEY ONLY — NOT FOR PRODUCTION USE.
    let key = [0u8; 32];
    let mut ring = syntek_crypto::key_versioning::KeyRing::new();
    ring.add(syntek_crypto::key_versioning::KeyVersion(1), &key)
        .unwrap();
    let ct = syntek_crypto::key_versioning::encrypt_versioned(
        "hello@example.com",
        &ring,
        "User",
        "email",
    )
    .unwrap();
    assert!(is_valid_ciphertext_format(&ct));
}

// ---------------------------------------------------------------------------
// C2 fix: unversioned ciphertexts are rejected or fail GCM authentication
//
// The unversioned `encrypt_field` from syntek-crypto produces:
//   base64( nonce(12) || ciphertext || tag(16) )
//
// The new format check requires:
//   base64( version(2, >= 1) || nonce(12) || ciphertext || tag(16) )
//
// An unversioned ciphertext's first 2 bytes are random nonce bytes.
// If those happen to encode version=0 (0x0000), the format check rejects it.
// If they happen to encode a non-zero version, the format check passes BUT
// `decrypt_versioned` will always fail: decryption strips the 2 "version"
// bytes (shifting the nonce), so the GCM authentication tag never matches.
// ---------------------------------------------------------------------------

#[test]
fn test_unversioned_ciphertext_version_zero_blob_fails_format_check() {
    // Synthetic: 30 bytes all zeros → first 2 bytes = version 0 (reserved).
    // Simulates the case where an unversioned nonce starts with 0x0000.
    let blob = make_blob(30);
    assert!(!is_valid_ciphertext_format(&blob));
}

#[test]
fn test_unversioned_ciphertext_always_fails_decrypt_versioned() {
    // Even if an unversioned ciphertext's first 2 bytes happen to form a
    // non-zero version number, decrypt_versioned must still fail because the
    // nonce is shifted by 2 bytes, causing a GCM authentication tag failure.
    // TEST KEY ONLY — NOT FOR PRODUCTION USE.
    let key = [0u8; 32];

    // Produce a real unversioned ciphertext via the lower-level Rust API.
    let unversioned_ct = syntek_crypto::encrypt_field("secret", &key, "User", "email").unwrap();

    // Build a ring with the same key so the version lookup cannot be blamed
    // for the failure — we want to confirm the GCM tag fails.
    let mut ring = syntek_crypto::key_versioning::KeyRing::new();
    // The unversioned nonce is 12 random bytes. Bytes 0-1 (the "version")
    // are decoded to a u16. We insert that exact version so the ring lookup
    // succeeds, ensuring the test isolates the GCM tag failure.
    let inner = base64ct::Base64::decode_vec(&unversioned_ct).unwrap();
    let nonce_version = u16::from_be_bytes([inner[0], inner[1]]);
    if nonce_version == 0 {
        // Version 0 is reserved — the ring cannot hold it. The format check
        // already rejects this ciphertext, so we skip the ring-based path.
        assert!(!is_valid_ciphertext_format(&unversioned_ct));
        return;
    }
    ring.add(
        syntek_crypto::key_versioning::KeyVersion(nonce_version),
        &key,
    )
    .unwrap();

    let result =
        syntek_crypto::key_versioning::decrypt_versioned(&unversioned_ct, &ring, "User", "email");
    assert!(
        result.is_err(),
        "Unversioned ciphertext must always fail decrypt_versioned (GCM tag mismatch)"
    );
}

// ---------------------------------------------------------------------------
// AC: Error types are defined and convertible to Python exceptions
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

// ---------------------------------------------------------------------------
// M7: verify_password with an empty hash returns false
// ---------------------------------------------------------------------------

#[test]
fn test_verify_password_empty_hash_returns_false() {
    let result = syntek_crypto::verify_password("some-password", "");
    assert!(!result.unwrap());
}

#[test]
fn test_verify_password_empty_password_returns_false() {
    let result = syntek_crypto::verify_password("", "$argon2id$v=19$m=65536,t=3,p=4$...");
    assert!(!result.unwrap());
}

// ---------------------------------------------------------------------------
// Versioned batch functions smoke test
// ---------------------------------------------------------------------------

#[test]
fn test_encrypt_fields_batch_versioned_round_trip() {
    // TEST KEY ONLY — NOT FOR PRODUCTION USE.
    let key = [1u8; 32];
    let mut ring = syntek_crypto::key_versioning::KeyRing::new();
    ring.add(syntek_crypto::key_versioning::KeyVersion(1), &key)
        .unwrap();

    let fields = [("email", "user@example.com"), ("phone", "+441234567890")];

    let encrypted =
        syntek_crypto::key_versioning::encrypt_fields_batch_versioned(&fields, &ring, "User")
            .unwrap();
    assert_eq!(encrypted.len(), 2);

    let to_decrypt: Vec<(&str, &str)> = fields
        .iter()
        .zip(encrypted.iter())
        .map(|((name, _), ct)| (*name, ct.as_str()))
        .collect();

    let decrypted =
        syntek_crypto::key_versioning::decrypt_fields_batch_versioned(&to_decrypt, &ring, "User")
            .unwrap();

    assert_eq!(decrypted[0], "user@example.com");
    assert_eq!(decrypted[1], "+441234567890");
}
