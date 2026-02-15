//! Key versioning support for field-level encryption
//!
//! This module provides encryption/decryption with key rotation support.
//! It allows encrypting data with a versioned format that includes a key ID,
//! enabling seamless key rotation without breaking existing encrypted data.
//!
//! # Format
//!
//! Versioned format: `version (1 byte) || key_id (4 bytes) || nonce (12 bytes) || ciphertext`
//!
//! # Security Features
//!
//! - Supports key rotation: encrypt with new key, decrypt with multiple keys
//! - Version byte enables future format changes without breaking compatibility
//! - Key ID allows lookup of correct decryption key
//! - Uses cryptographically secure random nonce generation
//! - Backward compatible with legacy (non-versioned) format

use aes_gcm::{
    aead::{Aead as AesAead, KeyInit as AesKeyInit},
    Aes256Gcm, Nonce as AesNonce,
};
use anyhow::Result;
use chacha20poly1305::{ChaCha20Poly1305, Nonce};
use ring::rand::{SecureRandom, SystemRandom};
use std::collections::HashMap;
use zeroize::Zeroize;

use crate::field_level::{EncryptionAlgorithm, MAX_CIPHERTEXT_SIZE, MAX_PLAINTEXT_SIZE};

/// Encrypted data format version
///
/// Version 1: version (1 byte) || key_id (4 bytes) || nonce (12 bytes) || ciphertext
/// Version 0: Legacy format without versioning (nonce (12 bytes) || ciphertext)
const FORMAT_VERSION: u8 = 1;

/// Encrypt a single field value with key versioning
///
/// # Arguments
///
/// * `plaintext` - The plaintext string to encrypt
/// * `key` - 32-byte encryption key
/// * `key_id` - Key identifier (u32) for key rotation support
/// * `algo` - Encryption algorithm (AES256GCM or ChaCha20Poly1305)
///
/// # Returns
///
/// Returns a Vec<u8> containing: version (1 byte) || key_id (4 bytes) || nonce (12 bytes) || ciphertext
///
/// # Security
///
/// - Supports key rotation: encrypt with new key, decrypt with multiple keys
/// - Version byte enables future format changes without breaking compatibility
/// - Key ID allows lookup of correct decryption key
/// - Uses cryptographically secure random nonce generation
///
/// # Format
///
/// ```text
/// +--------+--------+--------+-------+------------+
/// | Byte 0 | 1-4    | 5-16   | 17+   |            |
/// +--------+--------+--------+-------+------------+
/// | Ver=1  | Key ID | Nonce  | Tag   | Ciphertext |
/// +--------+--------+--------+-------+------------+
/// ```
///
/// # Example
///
/// ```rust,ignore
/// use syntek_encryption::{EncryptionAlgorithm, encrypt_field_with_version};
///
/// let key = [0u8; 32];
/// let key_id = 1; // Current key version
/// let plaintext = "sensitive data";
///
/// let encrypted = encrypt_field_with_version(
///     plaintext,
///     &key,
///     key_id,
///     EncryptionAlgorithm::ChaCha20Poly1305
/// )?;
/// ```
pub fn encrypt_field_with_version(
    plaintext: &str,
    key: &[u8],
    key_id: u32,
    algo: EncryptionAlgorithm,
) -> Result<Vec<u8>> {
    // Validate key length
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    // SECURITY: Prevent DoS via unbounded allocations
    if plaintext.len() > MAX_PLAINTEXT_SIZE {
        anyhow::bail!(
            "Plaintext too large: {} bytes exceeds maximum of {} bytes",
            plaintext.len(),
            MAX_PLAINTEXT_SIZE
        );
    }

    // SECURITY: Generate cryptographically secure random nonce
    let rng = SystemRandom::new();
    let mut nonce_bytes = [0u8; 12];
    rng.fill(&mut nonce_bytes)
        .map_err(|_| anyhow::anyhow!("Failed to generate secure random nonce"))?;

    // Encrypt the plaintext
    let ciphertext = match algo {
        EncryptionAlgorithm::AES256GCM => {
            let cipher = Aes256Gcm::new_from_slice(key)
                .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
            let nonce = AesNonce::from_slice(&nonce_bytes);
            cipher
                .encrypt(nonce, plaintext.as_bytes())
                .map_err(|e| anyhow::anyhow!("AES-256-GCM encryption failed: {}", e))?
        }
        EncryptionAlgorithm::ChaCha20Poly1305 => {
            let cipher = ChaCha20Poly1305::new_from_slice(key)
                .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
            let nonce = Nonce::from_slice(&nonce_bytes);
            cipher
                .encrypt(nonce, plaintext.as_bytes())
                .map_err(|e| anyhow::anyhow!("ChaCha20-Poly1305 encryption failed: {}", e))?
        }
    };

    // Build versioned format: version (1) || key_id (4) || nonce (12) || ciphertext
    let mut result = Vec::with_capacity(1 + 4 + nonce_bytes.len() + ciphertext.len());
    result.push(FORMAT_VERSION);
    result.extend_from_slice(&key_id.to_be_bytes());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&ciphertext);

    Ok(result)
}

/// Decrypt a single field value with key versioning support
///
/// # Arguments
///
/// * `ciphertext` - The encrypted data (version || key_id || nonce || ciphertext OR legacy nonce || ciphertext)
/// * `keys` - HashMap of key_id to 32-byte decryption keys
/// * `algo` - Decryption algorithm (must match encryption algorithm)
///
/// # Returns
///
/// Returns the decrypted plaintext string
///
/// # Security
///
/// - Supports both versioned and legacy (non-versioned) formats
/// - Attempts decryption with the key specified by key_id
/// - Falls back to trying all keys if key_id lookup fails
/// - Legacy format (no version byte) tries all keys sequentially
/// - Uses zeroize to clear plaintext bytes from memory
///
/// # Format Detection
///
/// - Version 1: First byte is 0x01, followed by 4-byte key_id
/// - Version 0 (legacy): First byte is part of nonce (likely not 0x01)
///
/// # Example
///
/// ```rust,ignore
/// use std::collections::HashMap;
/// use syntek_encryption::{EncryptionAlgorithm, decrypt_field_with_version};
///
/// let mut keys = HashMap::new();
/// keys.insert(1, vec![0u8; 32]); // Old key
/// keys.insert(2, vec![1u8; 32]); // New key
///
/// let plaintext = decrypt_field_with_version(
///     &encrypted,
///     &keys,
///     EncryptionAlgorithm::ChaCha20Poly1305
/// )?;
/// ```
pub fn decrypt_field_with_version(
    ciphertext: &[u8],
    keys: &HashMap<u32, Vec<u8>>,
    algo: EncryptionAlgorithm,
) -> Result<String> {
    if keys.is_empty() {
        anyhow::bail!("No decryption keys provided");
    }

    // SECURITY: Prevent DoS via unbounded allocations
    if ciphertext.len() > MAX_CIPHERTEXT_SIZE + 5 {
        // +5 for version + key_id
        anyhow::bail!(
            "Ciphertext too large: {} bytes exceeds maximum",
            ciphertext.len()
        );
    }

    // Check if this is a versioned format
    if ciphertext.len() >= 17 && ciphertext[0] == FORMAT_VERSION {
        // Versioned format: version (1) || key_id (4) || nonce (12) || ciphertext
        let key_id = u32::from_be_bytes([
            ciphertext[1],
            ciphertext[2],
            ciphertext[3],
            ciphertext[4],
        ]);

        let (nonce_bytes, encrypted_data) = ciphertext[5..].split_at(12);

        // Try to get the key by ID first
        if let Some(key) = keys.get(&key_id) {
            if let Ok(plaintext) = try_decrypt(nonce_bytes, encrypted_data, key, algo) {
                return Ok(plaintext);
            }
        }

        // If key_id lookup failed, try all keys (for key migration scenarios)
        for key in keys.values() {
            if let Ok(plaintext) = try_decrypt(nonce_bytes, encrypted_data, key, algo) {
                return Ok(plaintext);
            }
        }

        anyhow::bail!("Decryption failed: no valid key found for key_id {}", key_id);
    } else {
        // Legacy format (no versioning): nonce (12) || ciphertext
        if ciphertext.len() < 12 {
            anyhow::bail!(
                "Invalid ciphertext length: expected at least 12 bytes, got {}",
                ciphertext.len()
            );
        }

        let (nonce_bytes, encrypted_data) = ciphertext.split_at(12);

        // Try all keys for legacy format (no key_id to guide us)
        for key in keys.values() {
            if let Ok(plaintext) = try_decrypt(nonce_bytes, encrypted_data, key, algo) {
                return Ok(plaintext);
            }
        }

        anyhow::bail!("Decryption failed: no valid key found (legacy format)");
    }
}

/// Helper function to attempt decryption with a specific key
///
/// # Arguments
///
/// * `nonce_bytes` - The 12-byte nonce
/// * `encrypted_data` - The ciphertext (with authentication tag)
/// * `key` - 32-byte decryption key
/// * `algo` - Decryption algorithm
///
/// # Returns
///
/// Returns Ok(plaintext) if decryption succeeds, Err otherwise
fn try_decrypt(
    nonce_bytes: &[u8],
    encrypted_data: &[u8],
    key: &[u8],
    algo: EncryptionAlgorithm,
) -> Result<String> {
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    let mut plaintext_bytes = match algo {
        EncryptionAlgorithm::AES256GCM => {
            let cipher = Aes256Gcm::new_from_slice(key)
                .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
            let nonce = AesNonce::from_slice(nonce_bytes);
            cipher
                .decrypt(nonce, encrypted_data)
                .map_err(|e| anyhow::anyhow!("AES-256-GCM decryption failed: {}", e))?
        }
        EncryptionAlgorithm::ChaCha20Poly1305 => {
            let cipher = ChaCha20Poly1305::new_from_slice(key)
                .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
            let nonce = Nonce::from_slice(nonce_bytes);
            cipher
                .decrypt(nonce, encrypted_data)
                .map_err(|e| anyhow::anyhow!("ChaCha20-Poly1305 decryption failed: {}", e))?
        }
    };

    // Convert to String and zeroize the byte vector
    let result = String::from_utf8(plaintext_bytes.clone())
        .map_err(|e| anyhow::anyhow!("Invalid UTF-8 in decrypted data: {}", e))?;

    // SECURITY: Zeroize the plaintext bytes from memory
    plaintext_bytes.zeroize();

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_versioned_encrypt_decrypt_roundtrip() {
        let key = [42u8; 32];
        let key_id = 1;
        let plaintext = "Hello, versioned encryption!";

        let mut keys = HashMap::new();
        keys.insert(key_id, key.to_vec());

        let ciphertext = encrypt_field_with_version(
            plaintext,
            &key,
            key_id,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();
        let decrypted =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_key_rotation_with_multiple_keys() {
        let old_key = [42u8; 32];
        let new_key = [99u8; 32];
        let plaintext = "Test key rotation";

        // Encrypt with old key (key_id = 1)
        let ciphertext1 = encrypt_field_with_version(
            plaintext,
            &old_key,
            1,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();

        // Encrypt with new key (key_id = 2)
        let ciphertext2 = encrypt_field_with_version(
            plaintext,
            &new_key,
            2,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();

        // Set up key registry with both keys
        let mut keys = HashMap::new();
        keys.insert(1, old_key.to_vec());
        keys.insert(2, new_key.to_vec());

        // Both ciphertexts should decrypt correctly
        let decrypted1 =
            decrypt_field_with_version(&ciphertext1, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();
        let decrypted2 =
            decrypt_field_with_version(&ciphertext2, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();

        assert_eq!(decrypted1, plaintext);
        assert_eq!(decrypted2, plaintext);
    }

    #[test]
    fn test_versioned_format_structure() {
        let key = [42u8; 32];
        let key_id = 0x12345678u32;
        let plaintext = "Test";

        let ciphertext = encrypt_field_with_version(
            plaintext,
            &key,
            key_id,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();

        // Check format: version (1) || key_id (4) || nonce (12) || ciphertext
        assert!(ciphertext.len() >= 1 + 4 + 12 + plaintext.len());

        // Verify version byte
        assert_eq!(ciphertext[0], FORMAT_VERSION);

        // Verify key_id (big-endian)
        let stored_key_id = u32::from_be_bytes([
            ciphertext[1],
            ciphertext[2],
            ciphertext[3],
            ciphertext[4],
        ]);
        assert_eq!(stored_key_id, key_id);
    }

    #[test]
    fn test_missing_key_id_fails() {
        let key = [42u8; 32];
        let plaintext = "Test";

        let ciphertext = encrypt_field_with_version(
            plaintext,
            &key,
            1,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();

        // Try to decrypt with wrong key_id
        let mut keys = HashMap::new();
        keys.insert(2, key.to_vec()); // Different key_id

        let result =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305);
        assert!(result.is_err());
    }

    #[test]
    fn test_empty_keys_fails() {
        let ciphertext = vec![0u8; 20];
        let keys = HashMap::new();

        let result =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("No decryption keys"));
    }

    #[test]
    fn test_versioned_aes256gcm_roundtrip() {
        let key = [42u8; 32];
        let key_id = 1;
        let plaintext = "AES-256-GCM with versioning";

        let mut keys = HashMap::new();
        keys.insert(key_id, key.to_vec());

        let ciphertext =
            encrypt_field_with_version(plaintext, &key, key_id, EncryptionAlgorithm::AES256GCM)
                .unwrap();
        let decrypted =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::AES256GCM)
                .unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_versioned_unicode() {
        let key = [42u8; 32];
        let key_id = 1;
        let plaintext = "Hello 世界 🌍 مرحبا";

        let mut keys = HashMap::new();
        keys.insert(key_id, key.to_vec());

        let ciphertext = encrypt_field_with_version(
            plaintext,
            &key,
            key_id,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();
        let decrypted =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_fallback_to_all_keys() {
        let key1 = [42u8; 32];
        let key2 = [99u8; 32];
        let plaintext = "Test fallback";

        // Encrypt with key1 (key_id = 1)
        let ciphertext = encrypt_field_with_version(
            plaintext,
            &key1,
            1,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();

        // Provide multiple keys without the correct key_id
        let mut keys = HashMap::new();
        keys.insert(10, key2.to_vec()); // Wrong key
        keys.insert(20, key1.to_vec()); // Correct key but wrong ID

        // Should still decrypt by trying all keys
        let decrypted =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_large_plaintext_with_versioning() {
        let key = [42u8; 32];
        let key_id = 1;
        let plaintext = "A".repeat(MAX_PLAINTEXT_SIZE - 1000);

        let mut keys = HashMap::new();
        keys.insert(key_id, key.to_vec());

        let ciphertext = encrypt_field_with_version(
            &plaintext,
            &key,
            key_id,
            EncryptionAlgorithm::ChaCha20Poly1305,
        )
        .unwrap();
        let decrypted =
            decrypt_field_with_version(&ciphertext, &keys, EncryptionAlgorithm::ChaCha20Poly1305)
                .unwrap();

        assert_eq!(decrypted, plaintext);
    }
}
