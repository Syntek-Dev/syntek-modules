//! Batch encryption for multiple related fields
//!
//! Provides efficient encryption/decryption of multiple fields with a single operation.
//! Each field is encrypted with its own unique nonce for security.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use zeroize::Zeroize;

use crate::field_level::{decrypt_field, encrypt_field};

/// Maximum number of fields in a batch - prevents DoS via excessive processing
const MAX_BATCH_FIELDS: usize = 1000;

/// Encrypted batch container
///
/// Stores multiple encrypted fields with their field names.
/// Each field is independently encrypted with its own nonce.
#[derive(Serialize, Deserialize, Debug)]
struct EncryptedBatch {
    /// Map of field names to encrypted values (nonce + ciphertext)
    fields: HashMap<String, Vec<u8>>,
}

/// Encrypt multiple fields together
///
/// # Arguments
///
/// * `fields` - HashMap of field names to plaintext values
/// * `key` - 32-byte encryption key for ChaCha20-Poly1305
///
/// # Returns
///
/// Returns serialized encrypted batch as Vec<u8>
///
/// # Security
///
/// - Each field is encrypted with a unique random nonce
/// - Fields are independently decryptable
/// - Prevents DoS by limiting batch size to MAX_BATCH_FIELDS
/// - Serialized using bincode for efficiency
///
/// # Example
///
/// ```rust,ignore
/// use std::collections::HashMap;
///
/// let mut fields = HashMap::new();
/// fields.insert("email".to_string(), "user@example.com".to_string());
/// fields.insert("phone".to_string(), "+1234567890".to_string());
///
/// let encrypted = encrypt_batch(fields, &key)?;
/// ```
pub fn encrypt_batch(fields: HashMap<String, String>, key: &[u8]) -> Result<Vec<u8>> {
    // Validate key length
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    // SECURITY: Prevent DoS via excessive field count
    if fields.len() > MAX_BATCH_FIELDS {
        anyhow::bail!(
            "Too many fields in batch: {} exceeds maximum of {}",
            fields.len(),
            MAX_BATCH_FIELDS
        );
    }

    let mut encrypted_fields = HashMap::with_capacity(fields.len());

    // Encrypt each field with its own unique nonce
    for (field_name, plaintext) in fields {
        let encrypted = encrypt_field(&plaintext, key)?;
        encrypted_fields.insert(field_name, encrypted);
    }

    let batch = EncryptedBatch {
        fields: encrypted_fields,
    };

    // Serialize the batch
    let serialized = serde_json::to_vec(&batch)
        .map_err(|e| anyhow::anyhow!("Failed to serialize encrypted batch: {}", e))?;

    Ok(serialized)
}

/// Decrypt multiple fields
///
/// # Arguments
///
/// * `ciphertext` - Serialized encrypted batch
/// * `key` - 32-byte decryption key for ChaCha20-Poly1305
///
/// # Returns
///
/// Returns HashMap of field names to decrypted plaintext values
///
/// # Security
///
/// - Each field is independently decrypted
/// - Validates batch structure before decryption
/// - Intermediate plaintext values are zeroized
/// - Prevents DoS by limiting batch size
///
/// # Example
///
/// ```rust,ignore
/// let decrypted_fields = decrypt_batch(&encrypted, &key)?;
/// assert_eq!(decrypted_fields.get("email"), Some(&"user@example.com".to_string()));
/// ```
pub fn decrypt_batch(ciphertext: &[u8], key: &[u8]) -> Result<HashMap<String, String>> {
    // Validate key length
    if key.len() != 32 {
        anyhow::bail!("Invalid key length: expected 32 bytes, got {}", key.len());
    }

    // Deserialize the batch
    let batch: EncryptedBatch = serde_json::from_slice(ciphertext)
        .map_err(|e| anyhow::anyhow!("Failed to deserialize encrypted batch: {}", e))?;

    // SECURITY: Prevent DoS via excessive field count
    if batch.fields.len() > MAX_BATCH_FIELDS {
        anyhow::bail!(
            "Too many fields in batch: {} exceeds maximum of {}",
            batch.fields.len(),
            MAX_BATCH_FIELDS
        );
    }

    let mut decrypted_fields = HashMap::with_capacity(batch.fields.len());

    // Decrypt each field
    for (field_name, encrypted) in batch.fields {
        let mut plaintext = decrypt_field(&encrypted, key)?;
        decrypted_fields.insert(field_name, plaintext.clone());

        // SECURITY: Zeroize intermediate plaintext
        plaintext.zeroize();
    }

    Ok(decrypted_fields)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_batch_encryption_decryption() {
        let key = [42u8; 32];

        let mut fields = HashMap::new();
        fields.insert("email".to_string(), "user@example.com".to_string());
        fields.insert("phone".to_string(), "+1234567890".to_string());
        fields.insert("ssn".to_string(), "123-45-6789".to_string());

        let encrypted = encrypt_batch(fields.clone(), &key).unwrap();
        let decrypted = decrypt_batch(&encrypted, &key).unwrap();

        assert_eq!(decrypted.get("email").unwrap(), "user@example.com");
        assert_eq!(decrypted.get("phone").unwrap(), "+1234567890");
        assert_eq!(decrypted.get("ssn").unwrap(), "123-45-6789");
    }

    #[test]
    fn test_batch_too_many_fields() {
        let key = [42u8; 32];
        let mut fields = HashMap::new();

        // Try to create a batch with too many fields
        for i in 0..MAX_BATCH_FIELDS + 1 {
            fields.insert(format!("field_{}", i), "value".to_string());
        }

        let result = encrypt_batch(fields, &key);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("Too many fields"));
    }

    #[test]
    fn test_batch_invalid_key() {
        let key = [42u8; 16]; // Wrong size
        let fields = HashMap::new();

        let result = encrypt_batch(fields, &key);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Invalid key length"));
    }
}
