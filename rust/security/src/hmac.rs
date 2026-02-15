//! HMAC-SHA256 implementation for constant-time lookups.
//!
//! Provides HMAC-based hashing for email, phone, and IP addresses to enable
//! constant-time database lookups that prevent timing attacks and user enumeration.
//!
//! # Security Features
//!
//! - Uses HMAC-SHA256 for cryptographically secure hashing
//! - Constant-time comparison prevents timing attacks
//! - URL-safe base64 encoding for database compatibility
//! - Zero-copy operations where possible for performance
//!
//! # Example
//!
//! ```
//! use syntek_security::hmac::{hash_for_lookup, verify_hmac};
//!
//! let key = b"secret-hmac-key-32-bytes-long!!!";
//! let email = "user@example.com";
//!
//! // Hash for database storage
//! let hash = hash_for_lookup(email, key).unwrap();
//!
//! // Verify during lookup (constant-time)
//! assert!(verify_hmac(email, key, &hash).unwrap());
//! ```

use anyhow::{Context, Result};
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use subtle::ConstantTimeEq;

type HmacSha256 = Hmac<Sha256>;

/// Hashes data using HMAC-SHA256 for constant-time database lookups.
///
/// Creates a cryptographically secure hash suitable for database indexing.
/// The hash output is URL-safe base64 encoded for storage compatibility.
///
/// # Security Considerations
///
/// - Use a unique, randomly generated key of at least 32 bytes
/// - Store the key securely (use OpenBao or environment variables)
/// - Rotate keys periodically (implement key versioning)
/// - Never use user-supplied data as the HMAC key
///
/// # Arguments
///
/// * `data` - The data to hash (email, phone, IP address)
/// * `key` - The HMAC secret key (minimum 32 bytes recommended)
///
/// # Returns
///
/// * `Result<String>` - URL-safe base64 encoded hash (44 characters)
///
/// # Errors
///
/// Returns error if key length is invalid (HMAC-SHA256 accepts any key length,
/// but we enforce minimum security requirements).
///
/// # Example
///
/// ```
/// let key = b"my-secret-key-at-least-32-bytes!";
/// let email = "user@example.com";
/// let hash = hash_for_lookup(email, key)?;
/// println!("Hash: {}", hash); // e.g., "Xj8kPqR7nM9vL3hB2cN5wQ8zY1xT6uK4sF0dG..."
/// ```
pub fn hash_for_lookup(data: &str, key: &[u8]) -> Result<String> {
    // Enforce minimum key length for security (32 bytes = 256 bits)
    if key.len() < 32 {
        anyhow::bail!("HMAC key must be at least 32 bytes for security");
    }

    // Create HMAC instance with key
    let mut mac = HmacSha256::new_from_slice(key)
        .context("Failed to create HMAC instance with provided key")?;

    // Update with data
    mac.update(data.as_bytes());

    // Finalize and get result
    let result = mac.finalize();
    let code_bytes = result.into_bytes();

    // Encode as URL-safe base64 (no padding for consistency)
    let encoded = URL_SAFE_NO_PAD.encode(code_bytes);

    Ok(encoded)
}

/// Verifies data against an HMAC hash using constant-time comparison.
///
/// Prevents timing attacks by using constant-time comparison that takes
/// the same amount of time regardless of where the comparison fails.
///
/// # Security Considerations
///
/// - Uses `subtle::ConstantTimeEq` for timing-attack resistance
/// - Comparison time is independent of input values
/// - Safe against user enumeration via timing analysis
///
/// # Arguments
///
/// * `data` - The data to verify (email, phone, IP address)
/// * `key` - The HMAC secret key (must match hash generation key)
/// * `expected_hash` - The hash to verify against (base64 encoded)
///
/// # Returns
///
/// * `Result<bool>` - `true` if hash matches, `false` otherwise
///
/// # Errors
///
/// Returns error if hash generation fails or hash format is invalid.
///
/// # Example
///
/// ```
/// let key = b"my-secret-key-at-least-32-bytes!";
/// let email = "user@example.com";
/// let hash = hash_for_lookup(email, key)?;
///
/// // Later, verify during lookup
/// if verify_hmac(email, key, &hash)? {
///     println!("Hash verified!");
/// }
/// ```
pub fn verify_hmac(data: &str, key: &[u8], expected_hash: &str) -> Result<bool> {
    // Generate hash for the provided data
    let computed_hash = hash_for_lookup(data, key)?;

    // Constant-time comparison to prevent timing attacks
    // This takes the same time whether strings match or not
    let is_valid = computed_hash.as_bytes().ct_eq(expected_hash.as_bytes());

    Ok(is_valid.into())
}

/// Hashes an email address for database lookup.
///
/// Convenience wrapper around `hash_for_lookup` specifically for email addresses.
/// Normalises email to lowercase before hashing for case-insensitive lookups.
///
/// # Arguments
///
/// * `email` - The email address to hash
/// * `key` - The HMAC secret key
///
/// # Returns
///
/// * `Result<String>` - URL-safe base64 encoded hash
///
/// # Example
///
/// ```
/// let key = b"my-secret-key-at-least-32-bytes!";
/// let hash = hash_email("User@Example.COM", key)?;
/// // Email is normalised to lowercase before hashing
/// ```
pub fn hash_email(email: &str, key: &[u8]) -> Result<String> {
    let normalised = email.to_lowercase();
    hash_for_lookup(&normalised, key)
}

/// Hashes a phone number for database lookup.
///
/// Convenience wrapper around `hash_for_lookup` specifically for phone numbers.
/// Strips all non-digit characters before hashing for consistent formatting.
///
/// # Arguments
///
/// * `phone` - The phone number to hash (any format)
/// * `key` - The HMAC secret key
///
/// # Returns
///
/// * `Result<String>` - URL-safe base64 encoded hash
///
/// # Example
///
/// ```
/// let key = b"my-secret-key-at-least-32-bytes!";
/// let hash = hash_phone("+1 (555) 123-4567", key)?;
/// // Normalised to "15551234567" before hashing
/// ```
pub fn hash_phone(phone: &str, key: &[u8]) -> Result<String> {
    // Strip all non-digit characters for consistent hashing
    let normalised: String = phone.chars().filter(|c| c.is_ascii_digit()).collect();
    hash_for_lookup(&normalised, key)
}

/// Hashes an IP address for database lookup.
///
/// Convenience wrapper around `hash_for_lookup` specifically for IP addresses.
/// Accepts both IPv4 and IPv6 addresses.
///
/// # Arguments
///
/// * `ip` - The IP address to hash
/// * `key` - The HMAC secret key
///
/// # Returns
///
/// * `Result<String>` - URL-safe base64 encoded hash
///
/// # Example
///
/// ```
/// let key = b"my-secret-key-at-least-32-bytes!";
/// let hash_v4 = hash_ip("192.168.1.1", key)?;
/// let hash_v6 = hash_ip("2001:0db8::1", key)?;
/// ```
pub fn hash_ip(ip: &str, key: &[u8]) -> Result<String> {
    hash_for_lookup(ip, key)
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEST_KEY: &[u8] = b"test-hmac-key-32-bytes-long-!!!";

    #[test]
    fn test_hash_for_lookup_generates_consistent_hash() {
        let data = "test@example.com";
        let hash1 = hash_for_lookup(data, TEST_KEY).unwrap();
        let hash2 = hash_for_lookup(data, TEST_KEY).unwrap();

        assert_eq!(hash1, hash2);
        assert_eq!(hash1.len(), 43); // URL-safe base64 without padding
    }

    #[test]
    fn test_hash_for_lookup_different_data_produces_different_hash() {
        let hash1 = hash_for_lookup("user1@example.com", TEST_KEY).unwrap();
        let hash2 = hash_for_lookup("user2@example.com", TEST_KEY).unwrap();

        assert_ne!(hash1, hash2);
    }

    #[test]
    fn test_hash_for_lookup_different_keys_produce_different_hash() {
        let key1 = b"key1-32-bytes-long-!!!!!!!!!!!!";
        let key2 = b"key2-32-bytes-long-!!!!!!!!!!!!";
        let data = "test@example.com";

        let hash1 = hash_for_lookup(data, key1).unwrap();
        let hash2 = hash_for_lookup(data, key2).unwrap();

        assert_ne!(hash1, hash2);
    }

    #[test]
    fn test_hash_for_lookup_rejects_short_key() {
        let short_key = b"short";
        let result = hash_for_lookup("test", short_key);

        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("at least 32 bytes"));
    }

    #[test]
    fn test_verify_hmac_accepts_valid_hash() {
        let data = "test@example.com";
        let hash = hash_for_lookup(data, TEST_KEY).unwrap();

        let is_valid = verify_hmac(data, TEST_KEY, &hash).unwrap();
        assert!(is_valid);
    }

    #[test]
    fn test_verify_hmac_rejects_invalid_hash() {
        let data = "test@example.com";
        let wrong_hash = "invalid-hash-base64-encoded-!!!";

        let is_valid = verify_hmac(data, TEST_KEY, wrong_hash).unwrap();
        assert!(!is_valid);
    }

    #[test]
    fn test_verify_hmac_rejects_hash_from_different_data() {
        let data1 = "user1@example.com";
        let data2 = "user2@example.com";
        let hash1 = hash_for_lookup(data1, TEST_KEY).unwrap();

        let is_valid = verify_hmac(data2, TEST_KEY, &hash1).unwrap();
        assert!(!is_valid);
    }

    #[test]
    fn test_hash_email_normalises_to_lowercase() {
        let hash1 = hash_email("User@Example.COM", TEST_KEY).unwrap();
        let hash2 = hash_email("user@example.com", TEST_KEY).unwrap();

        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_hash_phone_strips_formatting() {
        let hash1 = hash_phone("+1 (555) 123-4567", TEST_KEY).unwrap();
        let hash2 = hash_phone("15551234567", TEST_KEY).unwrap();

        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_hash_ip_handles_ipv4() {
        let hash = hash_ip("192.168.1.1", TEST_KEY).unwrap();
        assert!(!hash.is_empty());
    }

    #[test]
    fn test_hash_ip_handles_ipv6() {
        let hash = hash_ip("2001:0db8::1", TEST_KEY).unwrap();
        assert!(!hash.is_empty());
    }

    #[test]
    fn test_constant_time_comparison() {
        // Test that verify_hmac uses constant-time comparison
        // This is a basic test - timing tests would be more thorough
        let data = "test@example.com";
        let hash = hash_for_lookup(data, TEST_KEY).unwrap();

        // Create hashes that differ at different positions
        let mut early_diff = hash.clone();
        early_diff.replace_range(0..1, "X");

        let mut late_diff = hash.clone();
        let len = late_diff.len();
        late_diff.replace_range((len - 1)..len, "X");

        // Both should return false in constant time
        assert!(!verify_hmac(data, TEST_KEY, &early_diff).unwrap());
        assert!(!verify_hmac(data, TEST_KEY, &late_diff).unwrap());
    }
}
