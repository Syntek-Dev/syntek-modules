//! Shared AES-256-GCM primitive helpers used internally by `syntek-crypto`.
//!
//! All public-facing encrypt/decrypt functions delegate to these two helpers
//! so that the canonical AES-256-GCM implementation lives in one place.
//!
//! # Blob layout (produced by `aes_gcm_encrypt`)
//!
//! ```text
//! base64( nonce(12) || ciphertext || tag(16) )
//! ```
//!
//! Callers that need additional framing bytes (e.g. a key-version prefix) are
//! responsible for decoding the string, prepending their own bytes, and
//! re-encoding before storage.

use aes_gcm::{
    Aes256Gcm, Key, Nonce,
    aead::{Aead, AeadCore, KeyInit, Payload},
};
use base64ct::{Base64, Encoding};
use rand::rngs::OsRng;

use crate::CryptoError;

/// Encrypts `plaintext` with AES-256-GCM and returns a base64-encoded blob.
///
/// The `key` slice must be exactly 32 bytes; the caller is responsible for
/// validating length before calling this function (no re-validation is
/// performed here).
///
/// The `aad` slice is passed directly to the AEAD `Payload` as Additional
/// Authenticated Data.  Any mismatch between the bytes supplied at encrypt
/// time and those supplied at decrypt time will cause GCM tag verification
/// to fail, preventing silent cross-context ciphertext reuse.
///
/// # Return value
///
/// A base64-encoded string containing `nonce(12) || ciphertext || tag(16)`.
///
/// # Errors
///
/// Returns [`CryptoError::EncryptionError`] if the AES-256-GCM cipher
/// operation fails.
pub(crate) fn aes_gcm_encrypt(
    plaintext: &str,
    key: &[u8],
    aad: &[u8],
) -> Result<String, CryptoError> {
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key));
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);

    let ciphertext_and_tag = cipher
        .encrypt(
            &nonce,
            Payload {
                msg: plaintext.as_bytes(),
                aad,
            },
        )
        .map_err(|_| CryptoError::EncryptionError("AES-256-GCM encryption failed".to_string()))?;

    // Assemble: nonce(12) || ciphertext || tag(16)
    let mut blob = Vec::with_capacity(12 + ciphertext_and_tag.len());
    blob.extend_from_slice(&nonce);
    blob.extend_from_slice(&ciphertext_and_tag);

    Ok(Base64::encode_string(&blob))
}

/// Decrypts a base64-encoded blob produced by [`aes_gcm_encrypt`].
///
/// The `key` slice must be exactly 32 bytes; the caller is responsible for
/// validating length before calling this function (no re-validation is
/// performed here).
///
/// The `aad` slice must match the bytes used during encryption.  A mismatch
/// causes GCM tag verification to fail and returns
/// [`CryptoError::DecryptionError`] without exposing any plaintext.
///
/// # Errors
///
/// Returns [`CryptoError::DecryptionError`] on:
/// - invalid base64 encoding
/// - blob shorter than 12 bytes (cannot contain a nonce)
/// - GCM authentication tag failure
/// - non-UTF-8 plaintext bytes
pub(crate) fn aes_gcm_decrypt(
    ciphertext: &str,
    key: &[u8],
    aad: &[u8],
) -> Result<String, CryptoError> {
    let blob = Base64::decode_vec(ciphertext)
        .map_err(|_| CryptoError::DecryptionError("invalid base64 encoding".to_string()))?;

    if blob.len() < 12 {
        return Err(CryptoError::DecryptionError(
            "ciphertext too short to contain a nonce".to_string(),
        ));
    }

    let nonce = Nonce::from_slice(&blob[..12]);
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key));

    let plaintext_bytes = cipher
        .decrypt(
            nonce,
            Payload {
                msg: &blob[12..],
                aad,
            },
        )
        .map_err(|_| CryptoError::DecryptionError("AES-256-GCM decryption failed".to_string()))?;

    String::from_utf8(plaintext_bytes).map_err(|_| {
        CryptoError::DecryptionError("decrypted bytes are not valid UTF-8".to_string())
    })
}
