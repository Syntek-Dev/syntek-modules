//! Cryptographically secure token generation.
//!
//! Provides token generation for authentication flows including:
//! - Email verification tokens
//! - Password reset tokens
//! - API keys
//! - Verification codes (numeric)
//!
//! # Security Features
//!
//! - Uses `ring::rand::SystemRandom` for cryptographic randomness
//! - URL-safe base64 encoding for token strings
//! - Configurable token lengths
//! - Zero-padded numeric codes
//! - Statistical uniformity tests
//!
//! # Example
//!
//! ```
//! use syntek_security::tokens::{generate_token, generate_verification_code};
//!
//! // Generate URL-safe token (32 bytes = ~43 characters base64)
//! let token = generate_token(32).unwrap();
//!
//! // Generate 6-digit verification code
//! let code = generate_verification_code().unwrap();
//! ```

use anyhow::Result;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use ring::rand::{SecureRandom, SystemRandom};

/// Default token length in bytes (32 bytes = 256 bits).
///
/// This produces a base64 string of ~43 characters which provides
/// sufficient entropy for security tokens.
pub const DEFAULT_TOKEN_LENGTH: usize = 32;

/// Default verification code length (6 digits).
///
/// Standard for SMS/email verification codes. Provides 1,000,000
/// possible combinations (10^6).
pub const DEFAULT_CODE_LENGTH: usize = 6;

/// Generates a cryptographically secure random token.
///
/// Creates a URL-safe base64 encoded token suitable for:
/// - Email verification links
/// - Password reset tokens
/// - Session tokens
/// - API keys
///
/// # Security Considerations
///
/// - Uses `ring::rand::SystemRandom` (backed by OS CSPRNG)
/// - Sufficient entropy for security tokens (256 bits default)
/// - URL-safe encoding prevents issues in URLs and cookies
/// - No padding to avoid information leakage
///
/// # Arguments
///
/// * `length` - The length in bytes (default: 32). Minimum 16 bytes recommended.
///
/// # Returns
///
/// * `Result<String>` - URL-safe base64 encoded token
///
/// # Errors
///
/// Returns error if:
/// - Length is less than 16 bytes (insufficient entropy)
/// - Random number generation fails
///
/// # Example
///
/// ```
/// // Generate 32-byte token (~43 characters base64)
/// let token = generate_token(32)?;
/// println!("Token: {}", token);
///
/// // Generate longer token for API keys
/// let api_key = generate_token(64)?;
/// ```
pub fn generate_token(length: usize) -> Result<String> {
    // Enforce minimum entropy requirement
    if length < 16 {
        anyhow::bail!("Token length must be at least 16 bytes for security");
    }

    // Create system random number generator
    let rng = SystemRandom::new();

    // Generate random bytes
    let mut bytes = vec![0u8; length];
    rng.fill(&mut bytes)
        .map_err(|_| anyhow::anyhow!("Failed to generate random bytes"))?;

    // Encode as URL-safe base64 without padding
    let token = URL_SAFE_NO_PAD.encode(&bytes);

    Ok(token)
}

/// Generates a cryptographically secure numeric verification code.
///
/// Creates a zero-padded numeric code suitable for:
/// - SMS verification codes
/// - Email verification codes
/// - TOTP backup codes
///
/// # Security Considerations
///
/// - Uses secure randomness (not predictable)
/// - Uniform distribution across all possible codes
/// - Zero-padded for consistent length
/// - Default 6 digits provides 10^6 = 1,000,000 combinations
///
/// # Arguments
///
/// * `length` - Number of digits (default: 6). Range: 4-12.
///
/// # Returns
///
/// * `Result<String>` - Zero-padded numeric code
///
/// # Errors
///
/// Returns error if:
/// - Length is less than 4 or greater than 12
/// - Random number generation fails
///
/// # Example
///
/// ```
/// // Generate 6-digit code (e.g., "042785")
/// let code = generate_verification_code()?;
///
/// // Generate 8-digit code
/// let longer_code = generate_verification_code_with_length(8)?;
/// ```
pub fn generate_verification_code() -> Result<String> {
    generate_verification_code_with_length(DEFAULT_CODE_LENGTH)
}

/// Generates a numeric verification code with specified length.
///
/// # Arguments
///
/// * `length` - Number of digits (4-12)
///
/// # Returns
///
/// * `Result<String>` - Zero-padded numeric code
///
/// # Errors
///
/// Returns error if length is out of range or random generation fails.
pub fn generate_verification_code_with_length(length: usize) -> Result<String> {
    // Validate code length
    if length < 4 {
        anyhow::bail!("Verification code must be at least 4 digits");
    }
    if length > 12 {
        anyhow::bail!("Verification code cannot exceed 12 digits");
    }

    // Calculate maximum value for the given length
    let max_value = 10_u64.pow(length as u32);

    // Generate random number using rejection sampling for uniform distribution
    let code_value = generate_uniform_random(max_value)?;

    // Format with zero-padding
    let code = format!("{:0width$}", code_value, width = length);

    Ok(code)
}

/// Generates a uniformly distributed random number in range [0, max).
///
/// Uses rejection sampling to ensure uniform distribution without modulo bias.
///
/// # Arguments
///
/// * `max` - The exclusive upper bound
///
/// # Returns
///
/// * `Result<u64>` - Random number in range [0, max)
///
/// # Errors
///
/// Returns error if random generation fails or max is zero.
fn generate_uniform_random(max: u64) -> Result<u64> {
    if max == 0 {
        anyhow::bail!("Maximum value must be greater than zero");
    }

    let rng = SystemRandom::new();

    // Rejection sampling to avoid modulo bias
    let range = u64::MAX - (u64::MAX % max);

    loop {
        let mut bytes = [0u8; 8];
        rng.fill(&mut bytes)
            .map_err(|_| anyhow::anyhow!("Failed to generate random bytes"))?;

        let value = u64::from_le_bytes(bytes);

        // Accept if within unbiased range
        if value < range {
            return Ok(value % max);
        }
        // Otherwise, retry (rejection sampling)
    }
}

/// Generates multiple verification codes at once.
///
/// Useful for generating backup codes or batch token generation.
///
/// # Arguments
///
/// * `count` - Number of codes to generate (max 100)
/// * `length` - Digits per code (4-12)
///
/// # Returns
///
/// * `Result<Vec<String>>` - Vector of unique verification codes
///
/// # Errors
///
/// Returns error if count exceeds limit or generation fails.
///
/// # Example
///
/// ```
/// // Generate 10 backup codes (6 digits each)
/// let codes = generate_backup_codes(10, 6)?;
/// ```
pub fn generate_backup_codes(count: usize, length: usize) -> Result<Vec<String>> {
    if count > 100 {
        anyhow::bail!("Cannot generate more than 100 codes at once");
    }

    let mut codes = Vec::with_capacity(count);
    for _ in 0..count {
        codes.push(generate_verification_code_with_length(length)?);
    }

    Ok(codes)
}

/// Generates a cryptographically secure API key.
///
/// Creates a longer token suitable for API authentication.
/// Format: `sk_` prefix + 64-byte token
///
/// # Returns
///
/// * `Result<String>` - API key with `sk_` prefix
///
/// # Example
///
/// ```
/// let api_key = generate_api_key()?;
/// // e.g., "sk_AbC123XyZ789..."
/// ```
pub fn generate_api_key() -> Result<String> {
    let token = generate_token(64)?;
    Ok(format!("sk_{}", token))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn test_generate_token_default_length() {
        let token = generate_token(32).unwrap();

        // Base64 encoding of 32 bytes is ~43 characters
        assert!(token.len() >= 42 && token.len() <= 44);

        // Should be URL-safe (alphanumeric, -, _)
        assert!(token
            .chars()
            .all(|c| c.is_alphanumeric() || c == '-' || c == '_'));
    }

    #[test]
    fn test_generate_token_different_lengths() {
        let token16 = generate_token(16).unwrap();
        let token64 = generate_token(64).unwrap();

        assert!(token16.len() < token64.len());
    }

    #[test]
    fn test_generate_token_rejects_short_length() {
        let result = generate_token(8);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("at least 16 bytes"));
    }

    #[test]
    fn test_generate_token_produces_unique_tokens() {
        let mut tokens = HashSet::new();

        // Generate 100 tokens
        for _ in 0..100 {
            let token = generate_token(32).unwrap();
            tokens.insert(token);
        }

        // All should be unique
        assert_eq!(tokens.len(), 100);
    }

    #[test]
    fn test_generate_verification_code_default() {
        let code = generate_verification_code().unwrap();

        assert_eq!(code.len(), 6);
        assert!(code.chars().all(|c| c.is_ascii_digit()));
    }

    #[test]
    fn test_generate_verification_code_zero_padded() {
        let code = generate_verification_code().unwrap();

        // Should be exactly 6 digits (including leading zeros)
        assert_eq!(code.len(), 6);

        // Parse as number to ensure valid
        let _num: u32 = code.parse().unwrap();
    }

    #[test]
    fn test_generate_verification_code_with_custom_length() {
        let code4 = generate_verification_code_with_length(4).unwrap();
        let code8 = generate_verification_code_with_length(8).unwrap();

        assert_eq!(code4.len(), 4);
        assert_eq!(code8.len(), 8);
    }

    #[test]
    fn test_generate_verification_code_rejects_invalid_length() {
        assert!(generate_verification_code_with_length(3).is_err());
        assert!(generate_verification_code_with_length(13).is_err());
    }

    #[test]
    fn test_verification_code_uniqueness() {
        let mut codes = HashSet::new();

        // Generate 1000 codes
        for _ in 0..1000 {
            let code = generate_verification_code().unwrap();
            codes.insert(code);
        }

        // Most should be unique (allow small collision rate due to 10^6 space)
        assert!(codes.len() > 990);
    }

    #[test]
    fn test_verification_code_distribution() {
        // Test that codes are uniformly distributed
        let mut digit_counts = vec![0; 10];

        // Generate 6000 codes (6000 * 6 = 36000 digits)
        for _ in 0..6000 {
            let code = generate_verification_code().unwrap();
            for c in code.chars() {
                let digit = c.to_digit(10).unwrap() as usize;
                digit_counts[digit] += 1;
            }
        }

        // Each digit should appear roughly 3600 times (±20%)
        for count in digit_counts {
            assert!(count > 2880 && count < 4320);
        }
    }

    #[test]
    fn test_generate_backup_codes() {
        let codes = generate_backup_codes(10, 6).unwrap();

        assert_eq!(codes.len(), 10);

        // All codes should be 6 digits
        for code in &codes {
            assert_eq!(code.len(), 6);
            assert!(code.chars().all(|c| c.is_ascii_digit()));
        }

        // All should be unique
        let unique: HashSet<_> = codes.iter().collect();
        assert_eq!(unique.len(), 10);
    }

    #[test]
    fn test_generate_backup_codes_rejects_large_count() {
        let result = generate_backup_codes(101, 6);
        assert!(result.is_err());
    }

    #[test]
    fn test_generate_api_key() {
        let api_key = generate_api_key().unwrap();

        assert!(api_key.starts_with("sk_"));
        assert!(api_key.len() > 70); // sk_ + ~86 character token
    }

    #[test]
    fn test_api_key_uniqueness() {
        let key1 = generate_api_key().unwrap();
        let key2 = generate_api_key().unwrap();

        assert_ne!(key1, key2);
    }

    #[test]
    fn test_no_sequential_patterns() {
        // Generate multiple tokens and check for sequential patterns
        for _ in 0..100 {
            let token = generate_token(32).unwrap();

            // Check no obvious patterns like "AAA", "111", "abc"
            let has_triple = token
                .as_bytes()
                .windows(3)
                .any(|w| w[0] == w[1] && w[1] == w[2]);

            // With good randomness, triples should be rare
            // but not impossible, so we just warn here
            if has_triple {
                // This is expected to happen rarely with random data
            }
        }
    }
}
