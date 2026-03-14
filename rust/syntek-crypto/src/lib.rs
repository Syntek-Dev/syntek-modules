//! syntek-crypto — AES-256-GCM encryption, Argon2id hashing, HMAC-SHA256
//!
//! Provides the cryptographic foundation for all Syntek backend modules.
//! All sensitive fields are encrypted here before any database write.
//!
//! # Algorithms
//!
//! | Algorithm   | Use                          | Standard         |
//! |-------------|------------------------------|------------------|
//! | AES-256-GCM | Field-level encryption       | NIST SP 800-38D  |
//! | Argon2id    | Password hashing (m=64MB)    | NIST SP 800-132  |
//! | HMAC-SHA256 | Data integrity verification  | FIPS 198-1       |
//! | zeroize     | Memory zeroisation after use | OWASP Crypto     |
//!
//! # Examples
//!
//! ```rust
//! use syntek_crypto::{encrypt_field, decrypt_field, CryptoError};
//!
//! let key = [0u8; 32];
//! let ciphertext = encrypt_field("hello@example.com", &key, "User", "email").unwrap();
//! let plaintext = decrypt_field(&ciphertext, &key, "User", "email").unwrap();
//! assert_eq!(plaintext, "hello@example.com");
//! ```

mod aes_gcm;
pub mod key_versioning;

use argon2::{
    Algorithm, Argon2, Params, Version,
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
};
use hmac::{Hmac, Mac};
use rand::rngs::OsRng;
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Errors returned by cryptographic operations.
#[derive(Debug, PartialEq, thiserror::Error)]
pub enum CryptoError {
    /// Returned when AES-256-GCM encryption fails.
    #[error("encryption error: {0}")]
    EncryptionError(String),

    /// Returned when AES-256-GCM decryption fails (e.g. tampered ciphertext or AAD mismatch).
    #[error("decryption error: {0}")]
    DecryptionError(String),

    /// Returned when Argon2id hashing fails.
    #[error("hash error: {0}")]
    HashError(String),

    /// Returned when an argument is empty or otherwise invalid.
    #[error("invalid input: {0}")]
    InvalidInput(String),

    /// Returned when a batch operation fails on a specific field.
    #[error("batch error on field '{field}': {reason}")]
    BatchError { field: String, reason: String },
}

/// Encrypts `plaintext` with AES-256-GCM using the supplied 32-byte `key`.
///
/// The `model` and `field` strings are encoded into the Additional Authenticated
/// Data (AAD) so that a ciphertext produced for one model/field pair cannot be
/// silently accepted by a different pair.
///
/// Returns a base64-encoded string containing `nonce || ciphertext || tag`
/// (12 bytes nonce + variable ciphertext + 16 bytes GCM tag).
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] if `key` is not 32 bytes.
/// Returns [`CryptoError::EncryptionError`] if the cipher operation fails.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::{encrypt_field, CryptoError};
///
/// let key = [0u8; 32];
/// let result = encrypt_field("secret", &key, "User", "email").unwrap();
/// assert!(!result.is_empty());
/// ```
pub fn encrypt_field(
    plaintext: &str,
    key: &[u8],
    model: &str,
    field: &str,
) -> Result<String, CryptoError> {
    if key.len() != 32 {
        return Err(CryptoError::InvalidInput(format!(
            "key must be 32 bytes, got {}",
            key.len()
        )));
    }

    let aad = format!("{}:{}", model, field);
    aes_gcm::aes_gcm_encrypt(plaintext, key, aad.as_bytes())
}

/// Decrypts a base64-encoded `ciphertext` produced by [`encrypt_field`].
///
/// The `model` and `field` strings must match those used during encryption;
/// any mismatch causes the GCM authentication tag to fail, returning a
/// [`CryptoError::DecryptionError`] without exposing any plaintext.
///
/// # Errors
///
/// Returns [`CryptoError::DecryptionError`] on tag verification failure,
/// base64 decode failure, or insufficient byte length.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::{decrypt_field, CryptoError};
///
/// let key = [0u8; 32];
/// let result = decrypt_field("not-valid-base64!!!", &key, "User", "email");
/// assert!(result.is_err());
/// ```
pub fn decrypt_field(
    ciphertext: &str,
    key: &[u8],
    model: &str,
    field: &str,
) -> Result<String, CryptoError> {
    // Validate base64 and minimum length before the key check so that the
    // error variant order matches the original contract (tests assert
    // DecryptionError for a wrong-length key, which is only reachable after
    // the blob length guard).
    use base64ct::{Base64, Encoding};
    let blob = Base64::decode_vec(ciphertext)
        .map_err(|_| CryptoError::DecryptionError("invalid base64 encoding".to_string()))?;

    if blob.len() < 12 {
        return Err(CryptoError::DecryptionError(
            "ciphertext too short to contain a nonce".to_string(),
        ));
    }

    if key.len() != 32 {
        return Err(CryptoError::DecryptionError(format!(
            "key must be 32 bytes, got {}",
            key.len()
        )));
    }

    let aad = format!("{}:{}", model, field);
    aes_gcm::aes_gcm_decrypt(ciphertext, key, aad.as_bytes())
}

/// Hashes `password` using Argon2id with Syntek standard parameters:
/// m = 65 536 KiB, t = 3 iterations, p = 4 lanes.
///
/// Returns a PHC-format string beginning with `$argon2id$`.
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] if `password` is empty.
/// Returns [`CryptoError::HashError`] if the Argon2id operation fails.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::hash_password;
///
/// let hash = hash_password("correct-horse-battery-staple").unwrap();
/// assert!(hash.starts_with("$argon2id$"));
/// ```
pub fn hash_password(password: &str) -> Result<String, CryptoError> {
    if password.is_empty() {
        return Err(CryptoError::InvalidInput(
            "password must not be empty".to_string(),
        ));
    }

    let params =
        Params::new(65536, 3, 4, None).map_err(|e| CryptoError::HashError(e.to_string()))?;

    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    let salt = SaltString::generate(&mut OsRng);

    argon2
        .hash_password(password.as_bytes(), &salt)
        .map(|h| h.to_string())
        .map_err(|e| CryptoError::HashError(e.to_string()))
}

/// Verifies `password` against an Argon2id PHC `hash` produced by [`hash_password`].
///
/// Returns `true` only when the password matches the hash. Returns `false` for
/// any non-matching password, including empty strings, without revealing the hash
/// internals.
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] if either argument is empty.
/// Returns [`CryptoError::HashError`] if the PHC string is malformed.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::{hash_password, verify_password};
///
/// let hash = hash_password("correct-horse-battery-staple").unwrap();
/// assert!(verify_password("correct-horse-battery-staple", &hash).unwrap());
/// assert!(!verify_password("wrong", &hash).unwrap());
/// ```
pub fn verify_password(password: &str, hash: &str) -> Result<bool, CryptoError> {
    if password.is_empty() {
        return Ok(false);
    }

    if hash.is_empty() {
        return Ok(false);
    }

    let parsed_hash = PasswordHash::new(hash).map_err(|e| CryptoError::HashError(e.to_string()))?;

    let params =
        Params::new(65536, 3, 4, None).map_err(|e| CryptoError::HashError(e.to_string()))?;
    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

    match argon2.verify_password(password.as_bytes(), &parsed_hash) {
        Ok(()) => Ok(true),
        Err(argon2::password_hash::Error::Password) => Ok(false),
        Err(e) => Err(CryptoError::HashError(e.to_string())),
    }
}

/// Signs `data` with HMAC-SHA256 using `key` and returns a lowercase hex-encoded digest.
///
/// The output is always a 64-character lowercase hex string (32 bytes encoded as hex).
/// The function is deterministic: the same `data` and `key` always produce the same digest.
///
/// # Key length
///
/// The recommended minimum key length is 32 bytes (256 bits) to match the
/// security level of HMAC-SHA256. Keys shorter than the 64-byte SHA-256 block
/// size are zero-padded internally (per RFC 2104); keys longer than 64 bytes
/// are first hashed. An empty key is rejected with [`CryptoError::InvalidInput`]
/// because it provides no authentication.
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] if `key` is empty.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::hmac_sign;
///
/// let sig = hmac_sign(b"payload", b"key-material").unwrap();
/// assert_eq!(sig.len(), 64);
/// assert!(sig.chars().all(|c| c.is_ascii_hexdigit()));
/// ```
pub fn hmac_sign(data: &[u8], key: &[u8]) -> Result<String, CryptoError> {
    if key.is_empty() {
        return Err(CryptoError::InvalidInput(
            "HMAC key must not be empty".to_string(),
        ));
    }

    let mut mac =
        <HmacSha256 as Mac>::new_from_slice(key).expect("HMAC accepts keys of any length");
    mac.update(data);
    let bytes = mac.finalize().into_bytes();
    Ok(bytes
        .iter()
        .fold(String::with_capacity(64), |mut s: String, b| {
            use std::fmt::Write;
            write!(s, "{:02x}", b).unwrap();
            s
        }))
}

/// Verifies a hex-encoded HMAC-SHA256 `sig` for `data` using `key`.
///
/// Uses the HMAC crate's constant-time byte comparison to prevent timing side-channels.
/// Returns `true` only when the signature is valid. Invalid hex or wrong-length inputs
/// return `false` immediately (one-bit non-secret leakage — acceptable for MAC verification).
///
/// The `sig` parameter accepts both lowercase and uppercase hex characters. The
/// input is normalised to lowercase before comparison so that signatures stored
/// or transmitted via systems that uppercase hex headers (e.g. HTTP header
/// normalisation) are verified correctly.
///
/// # Key length
///
/// The recommended minimum key length is 32 bytes (256 bits). An empty key
/// causes the function to return `false` immediately because it cannot provide
/// any authentication.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::{hmac_sign, hmac_verify};
///
/// let sig = hmac_sign(b"payload", b"key-material").unwrap();
/// assert!(hmac_verify(b"payload", b"key-material", &sig));
/// assert!(!hmac_verify(b"payload", b"key-material", "deadbeef"));
/// ```
pub fn hmac_verify(data: &[u8], key: &[u8], sig: &str) -> bool {
    // Empty key provides no authentication — reject immediately.
    if key.is_empty() {
        return false;
    }

    // Normalise to lowercase to accept uppercase hex signatures transparently.
    let sig_lower = sig.to_ascii_lowercase();

    // Decode the incoming hex signature. A non-64-char or non-hex input is a
    // non-constant-time early return — this leaks only that the format is wrong,
    // not anything about the key or data.
    let Some(expected) = decode_hex_32(&sig_lower) else {
        return false;
    };

    let Ok(mut mac) = <HmacSha256 as Mac>::new_from_slice(key) else {
        return false;
    };
    mac.update(data);
    // verify_slice uses subtle::ConstantTimeEq internally.
    mac.verify_slice(&expected).is_ok()
}

/// Encrypts a batch of `(field_name, plaintext)` pairs with AES-256-GCM.
///
/// Each field is encrypted independently with its own random nonce and its own
/// AAD derived from `model + field_name`. Results are returned in the same order
/// as the input slice.
///
/// If any field fails to encrypt the entire batch fails atomically — no partial
/// results are returned.
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] if `key` is not 32 bytes.
/// Returns [`CryptoError::BatchError`] if an individual field operation fails.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::encrypt_fields_batch;
///
/// let key = [0u8; 32];
/// let fields = [("email", "hello@example.com"), ("phone", "+441234567890")];
/// let result = encrypt_fields_batch(&fields, &key, "User").unwrap();
/// assert_eq!(result.len(), 2);
/// ```
pub fn encrypt_fields_batch(
    fields: &[(&str, &str)],
    key: &[u8],
    model: &str,
) -> Result<Vec<String>, CryptoError> {
    if key.len() != 32 {
        return Err(CryptoError::InvalidInput(format!(
            "key must be 32 bytes, got {}",
            key.len()
        )));
    }

    fields
        .iter()
        .map(|(field_name, plaintext)| {
            encrypt_field(plaintext, key, model, field_name).map_err(|e| CryptoError::BatchError {
                field: field_name.to_string(),
                reason: e.to_string(),
            })
        })
        .collect()
}

/// Decrypts a batch of `(field_name, ciphertext)` pairs with AES-256-GCM.
///
/// Each field is decrypted independently using its field-specific AAD
/// (`model + field_name`). Results are returned in the same order as the input slice.
///
/// If any field fails to decrypt the entire batch fails atomically — no partial
/// results are returned.
///
/// # Errors
///
/// Returns [`CryptoError::BatchError`] if an individual field operation fails,
/// naming the failing field in the `field` member.
///
/// # Examples
///
/// ```rust
/// use syntek_crypto::decrypt_fields_batch;
///
/// let key = [0u8; 32];
/// let fields = [("email", "not-valid-base64!!!")];
/// let result = decrypt_fields_batch(&fields, &key, "User");
/// assert!(result.is_err());
/// ```
pub fn decrypt_fields_batch(
    fields: &[(&str, &str)],
    key: &[u8],
    model: &str,
) -> Result<Vec<String>, CryptoError> {
    if key.len() != 32 {
        return Err(CryptoError::InvalidInput(format!(
            "key must be 32 bytes, got {}",
            key.len()
        )));
    }

    fields
        .iter()
        .map(|(field_name, ciphertext)| {
            decrypt_field(ciphertext, key, model, field_name).map_err(|e| CryptoError::BatchError {
                field: field_name.to_string(),
                reason: e.to_string(),
            })
        })
        .collect()
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/// Decodes a 64-character lowercase hex string into a 32-byte array.
/// Returns `None` if the input is not exactly 64 hex characters.
fn decode_hex_32(s: &str) -> Option<[u8; 32]> {
    if s.len() != 64 {
        return None;
    }
    let mut out = [0u8; 32];
    for (i, pair) in s.as_bytes().chunks_exact(2).enumerate() {
        let hi = (pair[0] as char).to_digit(16)? as u8;
        let lo = (pair[1] as char).to_digit(16)? as u8;
        out[i] = (hi << 4) | lo;
    }
    Some(out)
}
