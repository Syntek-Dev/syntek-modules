//! Field-level encryption for individual sensitive fields
//!
//! # Security Limits
//!
//! To prevent DoS attacks via unbounded memory allocations:
//! - Maximum plaintext size: 10 MB
//! - Maximum ciphertext size: 10 MB + overhead
//! - Key size: Must be exactly 32 bytes

use anyhow::Result;
use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Nonce,
};
use ring::rand::{SecureRandom, SystemRandom};
use secrecy::SecretString;
use zeroize::Zeroize;

/// Maximum plaintext size (10 MB) - prevents DoS via unbounded allocations
const MAX_PLAINTEXT_SIZE: usize = 10 * 1024 * 1024;

/// Maximum ciphertext size (10 MB + nonce + tag) - prevents DoS via unbounded allocations
const MAX_CIPHERTEXT_SIZE: usize = MAX_PLAINTEXT_SIZE + 12 + 16;

/// Encrypt a single field value
///
/// # Arguments
///
/// * `plaintext` - The plaintext string to encrypt
/// * `key` - 32-byte encryption key for ChaCha20-Poly1305
///
/// # Returns
///
/// Returns a Vec<u8> containing: nonce (12 bytes) || ciphertext (variable length)
///
/// # Security
///
/// - Uses cryptographically secure random nonce generation via ring::rand::SystemRandom
/// - Nonce is prepended to ciphertext for decryption
/// - Each encryption generates a unique nonce to prevent nonce reuse attacks
pub fn encrypt_field(plaintext: &str, key: &[u8]) -> Result<Vec<u8>> {
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

    let cipher = ChaCha20Poly1305::new_from_slice(key)
        .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;

    // SECURITY: Generate cryptographically secure random nonce
    // ChaCha20-Poly1305 requires a 12-byte (96-bit) nonce
    let rng = SystemRandom::new();
    let mut nonce_bytes = [0u8; 12];
    rng.fill(&mut nonce_bytes)
        .map_err(|_| anyhow::anyhow!("Failed to generate secure random nonce"))?;

    let nonce = Nonce::from_slice(&nonce_bytes);

    let ciphertext = cipher
        .encrypt(nonce, plaintext.as_bytes())
        .map_err(|e| anyhow::anyhow!("Encryption failed: {}", e))?;

    // Prepend nonce to ciphertext for storage/transmission
    let mut result = Vec::with_capacity(nonce_bytes.len() + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&ciphertext);

    Ok(result)
}

/// Decrypt a single field value
///
/// # Arguments
///
/// * `ciphertext` - The encrypted data containing: nonce (12 bytes) || ciphertext (variable length)
/// * `key` - 32-byte decryption key for ChaCha20-Poly1305
///
/// # Returns
///
/// Returns the decrypted plaintext string
///
/// # Security
///
/// - Extracts nonce from the first 12 bytes of ciphertext
/// - Uses zeroize to clear plaintext bytes from memory after conversion to String
/// - Note: The returned String cannot be zeroized (Rust limitation)
/// - For maximum security, consider using secrecy::SecretString for the return value
pub fn decrypt_field(ciphertext: &[u8], key: &[u8]) -> Result<String> {
    // Validate key length
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    // Validate ciphertext has at least nonce + minimal ciphertext
    if ciphertext.len() < 12 {
        anyhow::bail!(
            "Invalid ciphertext length: expected at least 12 bytes, got {}",
            ciphertext.len()
        );
    }

    // SECURITY: Prevent DoS via unbounded allocations
    if ciphertext.len() > MAX_CIPHERTEXT_SIZE {
        anyhow::bail!(
            "Ciphertext too large: {} bytes exceeds maximum of {} bytes",
            ciphertext.len(),
            MAX_CIPHERTEXT_SIZE
        );
    }

    let cipher = ChaCha20Poly1305::new_from_slice(key)
        .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;

    // SECURITY: Extract nonce from first 12 bytes
    let (nonce_bytes, encrypted_data) = ciphertext.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);

    let mut plaintext_bytes = cipher
        .decrypt(nonce, encrypted_data)
        .map_err(|e| anyhow::anyhow!("Decryption failed: {}", e))?;

    // Convert to String and zeroize the byte vector
    let result = String::from_utf8(plaintext_bytes.clone())
        .map_err(|e| anyhow::anyhow!("Invalid UTF-8 in decrypted data: {}", e))?;

    // SECURITY: Zeroize the plaintext bytes from memory
    plaintext_bytes.zeroize();

    Ok(result)
}

/// Decrypt a single field value into a SecretString (maximum security)
///
/// # Arguments
///
/// * `ciphertext` - The encrypted data containing: nonce (12 bytes) || ciphertext (variable length)
/// * `key` - 32-byte decryption key for ChaCha20-Poly1305
///
/// # Returns
///
/// Returns the decrypted plaintext as a SecretString
///
/// # Security
///
/// - SecretString ensures the decrypted value is zeroized when dropped
/// - Extracts nonce from the first 12 bytes of ciphertext
/// - Uses zeroize to clear intermediate plaintext bytes from memory
/// - Recommended for highly sensitive data (passwords, API keys, etc.)
///
/// # Example
///
/// ```rust,ignore
/// use secrecy::ExposeSecret;
///
/// let secret = decrypt_field_secure(&ciphertext, &key)?;
/// // Use the secret
/// println!("Decrypted: {}", secret.expose_secret());
/// // SecretString is automatically zeroized when it goes out of scope
/// ```
pub fn decrypt_field_secure(ciphertext: &[u8], key: &[u8]) -> Result<SecretString> {
    // Validate key length
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    // Validate ciphertext has at least nonce + minimal ciphertext
    if ciphertext.len() < 12 {
        anyhow::bail!(
            "Invalid ciphertext length: expected at least 12 bytes, got {}",
            ciphertext.len()
        );
    }

    // SECURITY: Prevent DoS via unbounded allocations
    if ciphertext.len() > MAX_CIPHERTEXT_SIZE {
        anyhow::bail!(
            "Ciphertext too large: {} bytes exceeds maximum of {} bytes",
            ciphertext.len(),
            MAX_CIPHERTEXT_SIZE
        );
    }

    let cipher = ChaCha20Poly1305::new_from_slice(key)
        .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;

    // SECURITY: Extract nonce from first 12 bytes
    let (nonce_bytes, encrypted_data) = ciphertext.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);

    let mut plaintext_bytes = cipher
        .decrypt(nonce, encrypted_data)
        .map_err(|e| anyhow::anyhow!("Decryption failed: {}", e))?;

    // Convert to String and wrap in SecretString
    let plaintext = String::from_utf8(plaintext_bytes.clone())
        .map_err(|e| anyhow::anyhow!("Invalid UTF-8 in decrypted data: {}", e))?;

    // SECURITY: Zeroize the plaintext bytes from memory
    plaintext_bytes.zeroize();

    // SECURITY: SecretString will zeroize the string when dropped
    Ok(SecretString::new(plaintext.into_boxed_str()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use secrecy::ExposeSecret;

    #[test]
    fn test_encrypt_decrypt_roundtrip() {
        let key = [42u8; 32];
        let plaintext = "Hello, secure world!";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();
        let decrypted = decrypt_field(&ciphertext, &key).unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_encrypt_decrypt_secure_roundtrip() {
        let key = [42u8; 32];
        let plaintext = "Sensitive data here";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();
        let decrypted = decrypt_field_secure(&ciphertext, &key).unwrap();

        assert_eq!(decrypted.expose_secret(), plaintext);
    }

    #[test]
    fn test_unique_nonces() {
        let key = [42u8; 32];
        let plaintext = "Same plaintext";

        // Encrypt the same plaintext twice
        let ciphertext1 = encrypt_field(plaintext, &key).unwrap();
        let ciphertext2 = encrypt_field(plaintext, &key).unwrap();

        // SECURITY: Nonces should be different, so ciphertexts should differ
        assert_ne!(ciphertext1, ciphertext2);

        // Both should decrypt to the same plaintext
        let decrypted1 = decrypt_field(&ciphertext1, &key).unwrap();
        let decrypted2 = decrypt_field(&ciphertext2, &key).unwrap();
        assert_eq!(decrypted1, plaintext);
        assert_eq!(decrypted2, plaintext);
    }

    #[test]
    fn test_nonce_included_in_ciphertext() {
        let key = [42u8; 32];
        let plaintext = "Test";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();

        // Ciphertext should be: 12 bytes (nonce) + plaintext_len + 16 bytes (tag)
        assert!(ciphertext.len() >= 12 + plaintext.len() + 16);

        // First 12 bytes should be the nonce
        assert_eq!(&ciphertext[0..12].len(), &12);
    }

    #[test]
    fn test_invalid_key_length_encrypt() {
        let key = [42u8; 16]; // Wrong size - should be 32
        let plaintext = "Test";

        let result = encrypt_field(plaintext, &key);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Invalid key length"));
    }

    #[test]
    fn test_invalid_key_length_decrypt() {
        let key = [42u8; 16]; // Wrong size - should be 32
        let ciphertext = vec![0u8; 28]; // Dummy ciphertext

        let result = decrypt_field(&ciphertext, &key);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Invalid key length"));
    }

    #[test]
    fn test_ciphertext_too_short() {
        let key = [42u8; 32];
        let ciphertext = vec![0u8; 10]; // Too short - minimum is 12 bytes

        let result = decrypt_field(&ciphertext, &key);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Invalid ciphertext length"));
    }

    #[test]
    fn test_plaintext_size_limit() {
        let key = [42u8; 32];
        let large_plaintext = "A".repeat(MAX_PLAINTEXT_SIZE + 1);

        let result = encrypt_field(&large_plaintext, &key);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("too large"));
    }

    #[test]
    fn test_ciphertext_size_limit() {
        let key = [42u8; 32];
        let large_ciphertext = vec![0u8; MAX_CIPHERTEXT_SIZE + 1];

        let result = decrypt_field(&large_ciphertext, &key);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("too large"));
    }

    #[test]
    fn test_tampered_ciphertext() {
        let key = [42u8; 32];
        let plaintext = "Original message";

        let mut ciphertext = encrypt_field(plaintext, &key).unwrap();

        // Tamper with the ciphertext (flip a bit)
        if let Some(byte) = ciphertext.get_mut(20) {
            *byte ^= 0xFF;
        }

        // Decryption should fail due to authentication failure
        let result = decrypt_field(&ciphertext, &key);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Decryption failed"));
    }

    #[test]
    fn test_wrong_key_decryption() {
        let key1 = [42u8; 32];
        let key2 = [99u8; 32];
        let plaintext = "Secret message";

        let ciphertext = encrypt_field(plaintext, &key1).unwrap();

        // Try to decrypt with wrong key
        let result = decrypt_field(&ciphertext, &key2);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Decryption failed"));
    }

    #[test]
    fn test_empty_plaintext() {
        let key = [42u8; 32];
        let plaintext = "";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();
        let decrypted = decrypt_field(&ciphertext, &key).unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_unicode_plaintext() {
        let key = [42u8; 32];
        let plaintext = "Hello 世界 🌍 Привет";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();
        let decrypted = decrypt_field(&ciphertext, &key).unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_large_but_valid_plaintext() {
        let key = [42u8; 32];
        // Create plaintext just under the limit
        let plaintext = "A".repeat(MAX_PLAINTEXT_SIZE - 1000);

        let ciphertext = encrypt_field(&plaintext, &key).unwrap();
        let decrypted = decrypt_field(&ciphertext, &key).unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_special_characters() {
        let key = [42u8; 32];
        let plaintext = "Test\n\t\r\0special\\characters\"'<>&";

        let ciphertext = encrypt_field(plaintext, &key).unwrap();
        let decrypted = decrypt_field(&ciphertext, &key).unwrap();

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_concurrent_encryption() {
        use std::sync::Arc;
        use std::thread;

        let key = [42u8; 32];
        let plaintext = Arc::new("Concurrent test".to_string());

        let mut handles = vec![];

        // Spawn multiple threads encrypting the same data
        for _ in 0..10 {
            let key_copy = key;
            let plaintext = Arc::clone(&plaintext);

            let handle = thread::spawn(move || encrypt_field(&plaintext, &key_copy).unwrap());

            handles.push(handle);
        }

        let results: Vec<_> = handles.into_iter().map(|h| h.join().unwrap()).collect();

        // All encryptions should succeed
        assert_eq!(results.len(), 10);

        // All ciphertexts should be different (different nonces)
        for i in 0..results.len() {
            for j in (i + 1)..results.len() {
                assert_ne!(results[i], results[j]);
            }
        }

        // All should decrypt to the same plaintext
        for ciphertext in results {
            let decrypted = decrypt_field(&ciphertext, &key).unwrap();
            assert_eq!(decrypted, *plaintext);
        }
    }
}
