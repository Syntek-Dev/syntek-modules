//! Key versioning support for AES-256-GCM field encryption — US076
//!
//! Every ciphertext produced by the versioned API is prefixed with a 2-byte
//! big-endian key version identifier before base64 encoding:
//!
//! ```text
//! stored value = base64( version_bytes(2) || nonce(12) || ciphertext || tag(16) )
//! ```
//!
//! This allows the [`KeyRing`] to select the correct key when decrypting a row
//! that was encrypted under an older version, enabling zero-downtime key rotation.
//!
//! # Rotation model
//!
//! - The active (current) key version is the highest version number in the ring.
//! - New writes always use the active version.
//! - Old ciphertexts remain readable as long as their version key is still held.
//! - Once all rows have been migrated, old versions are retired and removed.

use crate::CryptoError;

// ---------------------------------------------------------------------------
// KeyVersion newtype
// ---------------------------------------------------------------------------

/// A 2-byte key version identifier stored as a `u16`.
///
/// Version `0` is reserved; valid versioned keys start at `1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct KeyVersion(pub u16);

impl KeyVersion {
    /// Serialise to 2 big-endian bytes for prepending to a ciphertext blob.
    pub fn to_bytes(self) -> [u8; 2] {
        self.0.to_be_bytes()
    }

    /// Deserialise from the first 2 bytes of a decoded ciphertext blob.
    pub fn from_bytes(b: [u8; 2]) -> Self {
        Self(u16::from_be_bytes(b))
    }
}

// ---------------------------------------------------------------------------
// KeyRing
// ---------------------------------------------------------------------------

/// A versioned keyring mapping [`KeyVersion`] → 32-byte AES-256-GCM key.
///
/// The ring is immutable once constructed.  Add all required versions before
/// use; there is no runtime mutation API (by design — key material is loaded
/// once from environment variables at startup).
///
/// The *active* version is the highest version number stored in the ring.
#[derive(Debug)]
pub struct KeyRing {
    entries: Vec<(KeyVersion, [u8; 32])>,
}

impl KeyRing {
    /// Construct a new, empty keyring.  Use [`KeyRing::add`] to populate it.
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
        }
    }

    /// Add a key for `version` to the ring.
    ///
    /// # Errors
    ///
    /// Returns [`CryptoError::InvalidInput`] if `key` is not exactly 32 bytes.
    pub fn add(&mut self, version: KeyVersion, key: &[u8]) -> Result<(), CryptoError> {
        if key.len() != 32 {
            return Err(CryptoError::InvalidInput(format!(
                "key must be 32 bytes, got {}",
                key.len()
            )));
        }
        let mut bytes = [0u8; 32];
        bytes.copy_from_slice(key);
        self.entries.push((version, bytes));
        Ok(())
    }

    /// Return the active (highest-version) key version and key bytes.
    ///
    /// # Errors
    ///
    /// Returns [`CryptoError::InvalidInput`] when the ring is empty.
    pub fn active(&self) -> Result<(KeyVersion, &[u8; 32]), CryptoError> {
        self.entries
            .iter()
            .max_by_key(|(v, _)| *v)
            .map(|(v, k)| (*v, k))
            .ok_or_else(|| CryptoError::InvalidInput("keyring is empty".to_string()))
    }

    /// Resolve the key bytes for a specific `version`.
    ///
    /// # Errors
    ///
    /// Returns [`CryptoError::InvalidInput`] when `version` is not in the ring.
    pub fn get(&self, version: KeyVersion) -> Result<&[u8; 32], CryptoError> {
        self.entries
            .iter()
            .find(|(v, _)| *v == version)
            .map(|(_, k)| k)
            .ok_or_else(|| {
                CryptoError::InvalidInput(format!("key version {:?} not in ring", version))
            })
    }

    /// Return `true` if the ring contains no keys.
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Return the number of keys in the ring.
    pub fn len(&self) -> usize {
        self.entries.len()
    }
}

impl Default for KeyRing {
    fn default() -> Self {
        Self::new()
    }
}

// ---------------------------------------------------------------------------
// Versioned encrypt / decrypt
// ---------------------------------------------------------------------------

/// Encrypt `plaintext` using the active key from `ring`, prepending the 2-byte
/// key version to the blob before base64 encoding.
///
/// Layout: `base64( version(2) || nonce(12) || ciphertext || tag(16) )`
///
/// # Errors
///
/// Returns [`CryptoError::InvalidInput`] when the ring is empty.
/// Returns [`CryptoError::EncryptionError`] if the AES-256-GCM cipher fails.
pub fn encrypt_versioned(
    plaintext: &str,
    ring: &KeyRing,
    model: &str,
    field: &str,
) -> Result<String, CryptoError> {
    use aes_gcm::{
        Aes256Gcm, Key,
        aead::{Aead, AeadCore, KeyInit, Payload},
    };
    use base64ct::{Base64, Encoding};
    use rand::rngs::OsRng;

    let (active_version, key_bytes) = ring.active()?;

    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key_bytes));
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let aad = format!("{}:{}", model, field);

    let ciphertext_and_tag = cipher
        .encrypt(
            &nonce,
            Payload {
                msg: plaintext.as_bytes(),
                aad: aad.as_bytes(),
            },
        )
        .map_err(|_| CryptoError::EncryptionError("AES-256-GCM encryption failed".to_string()))?;

    // Layout: version(2) || nonce(12) || ciphertext || tag(16)
    let version_bytes = active_version.to_bytes();
    let mut blob = Vec::with_capacity(2 + 12 + ciphertext_and_tag.len());
    blob.extend_from_slice(&version_bytes);
    blob.extend_from_slice(&nonce);
    blob.extend_from_slice(&ciphertext_and_tag);

    Ok(Base64::encode_string(&blob))
}

/// Decrypt a ciphertext produced by [`encrypt_versioned`].
///
/// Strips the 2-byte version prefix, resolves the key from `ring`, then
/// delegates to the standard AES-256-GCM decrypt path.
///
/// # Errors
///
/// Returns [`CryptoError::DecryptionError`] for invalid base64, insufficient
/// byte length, unknown key version, or GCM tag failure.
pub fn decrypt_versioned(
    ciphertext: &str,
    ring: &KeyRing,
    model: &str,
    field: &str,
) -> Result<String, CryptoError> {
    use aes_gcm::{
        Aes256Gcm, Key, Nonce,
        aead::{Aead, KeyInit, Payload},
    };
    use base64ct::{Base64, Encoding};

    let blob = Base64::decode_vec(ciphertext)
        .map_err(|_| CryptoError::DecryptionError("invalid base64 encoding".to_string()))?;

    // Minimum: 2 (version) + 12 (nonce) + 16 (tag) = 30 bytes
    if blob.len() < 30 {
        return Err(CryptoError::DecryptionError(
            "ciphertext blob too short".to_string(),
        ));
    }

    let version = KeyVersion::from_bytes([blob[0], blob[1]]);

    let key_bytes = ring.get(version).map_err(|_| {
        CryptoError::DecryptionError(format!("key version {:?} not found in ring", version))
    })?;

    let nonce = Nonce::from_slice(&blob[2..14]);
    let aad = format!("{}:{}", model, field);

    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key_bytes));
    let plaintext_bytes = cipher
        .decrypt(
            nonce,
            Payload {
                msg: &blob[14..],
                aad: aad.as_bytes(),
            },
        )
        .map_err(|_| CryptoError::DecryptionError("AES-256-GCM decryption failed".to_string()))?;

    String::from_utf8(plaintext_bytes).map_err(|_| {
        CryptoError::DecryptionError("decrypted bytes are not valid UTF-8".to_string())
    })
}

/// Re-encrypt a ciphertext that was produced under an older key version so
/// that it uses the current active key.
///
/// This is the primitive used by the lazy background migration task.
///
/// The function decrypts with the version indicated in the ciphertext prefix,
/// then immediately re-encrypts under the active key.  If the ciphertext is
/// already at the active version the original ciphertext is returned unchanged.
///
/// # Errors
///
/// Returns [`CryptoError::DecryptionError`] if the original ciphertext cannot
/// be decrypted with the key held for its version.
/// Returns [`CryptoError::EncryptionError`] if re-encryption fails.
pub fn reencrypt_to_active(
    ciphertext: &str,
    ring: &KeyRing,
    model: &str,
    field: &str,
) -> Result<String, CryptoError> {
    use base64ct::{Base64, Encoding};

    // Decode to check the version prefix without a full decrypt round-trip.
    let blob = Base64::decode_vec(ciphertext)
        .map_err(|_| CryptoError::DecryptionError("invalid base64 encoding".to_string()))?;

    if blob.len() < 2 {
        return Err(CryptoError::DecryptionError(
            "ciphertext blob too short to read version".to_string(),
        ));
    }

    let ciphertext_version = KeyVersion::from_bytes([blob[0], blob[1]]);
    let (active_version, _) = ring.active()?;

    // No-op: already at the active version.
    if ciphertext_version == active_version {
        return Ok(ciphertext.to_string());
    }

    // Decrypt under the old key, then re-encrypt under the active key.
    let plaintext = decrypt_versioned(ciphertext, ring, model, field)?;
    encrypt_versioned(&plaintext, ring, model, field)
}
