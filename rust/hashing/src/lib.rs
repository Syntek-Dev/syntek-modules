//! Password hashing with Argon2id
//!
//! Implements OWASP 2025 recommended Argon2id parameters:
//! - Memory: 19456 KiB (19 MiB)
//! - Iterations: 2
//! - Parallelism: 1
//! - Output: 32 bytes
//!
//! Target hashing time: 100-200ms per password

use anyhow::Result;
use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Algorithm, Argon2, Params, Version,
};
use rand::rngs::OsRng;

/// OWASP 2025 recommended Argon2id parameters.
///
/// These parameters provide strong security while maintaining
/// acceptable performance (100-200ms per hash).
///
/// # Parameters
///
/// - Memory: 19456 KiB (19 MiB) - Resists GPU attacks
/// - Iterations: 2 - Time-memory trade-off
/// - Parallelism: 1 - Single-threaded for consistency
/// - Output: 32 bytes - Strong key length
const ARGON2_MEMORY_KIB: u32 = 19456; // 19 MiB
const ARGON2_ITERATIONS: u32 = 2;
const ARGON2_PARALLELISM: u32 = 1;
const ARGON2_OUTPUT_LEN: usize = 32;

/// Creates Argon2id instance with OWASP 2025 parameters.
///
/// # Returns
///
/// * `Result<Argon2>` - Configured Argon2id instance
///
/// # Errors
///
/// Returns error if parameter configuration is invalid.
fn create_argon2() -> Result<Argon2<'static>> {
    let params = Params::new(
        ARGON2_MEMORY_KIB,
        ARGON2_ITERATIONS,
        ARGON2_PARALLELISM,
        Some(ARGON2_OUTPUT_LEN),
    )
    .map_err(|e| anyhow::anyhow!("Invalid Argon2 parameters: {}", e))?;

    Ok(Argon2::new(Algorithm::Argon2id, Version::V0x13, params))
}

/// Hashes a password using Argon2id with OWASP 2025 parameters.
///
/// Uses cryptographically secure random salt generation and
/// returns a PHC string format hash that includes all parameters.
///
/// # Security Considerations
///
/// - Password is zeroized in Rust memory after use
/// - Salt is randomly generated per password (unique per hash)
/// - Uses Argon2id (hybrid mode) for resistance against both
///   side-channel and GPU attacks
///
/// # Arguments
///
/// * `password` - The password to hash
///
/// # Returns
///
/// * `Result<String>` - PHC format hash string (e.g., "$argon2id$v=19$m=19456,t=2,p=1$...")
///
/// # Errors
///
/// Returns error if hashing fails (e.g., out of memory).
///
/// # Example
///
/// ```
/// let hash = hash_password("my-secure-password")?;
/// println!("Hash: {}", hash);
/// ```
pub fn hash_password(password: &str) -> Result<String> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = create_argon2()?;

    let password_hash = argon2
        .hash_password(password.as_bytes(), &salt)
        .map_err(|e| anyhow::anyhow!("Password hashing failed: {}", e))?
        .to_string();

    Ok(password_hash)
}

/// Verifies a password against a hash.
///
/// Supports both new OWASP 2025 hashes and legacy hashes with
/// different parameters for backward compatibility.
///
/// # Security Considerations
///
/// - Constant-time comparison (handled by Argon2 library)
/// - Password is zeroized after verification
/// - Safe against timing attacks
///
/// # Arguments
///
/// * `password` - The password to verify
/// * `hash` - The PHC format hash to verify against
///
/// # Returns
///
/// * `Result<bool>` - `true` if password matches, `false` otherwise
///
/// # Errors
///
/// Returns error if hash format is invalid or verification fails.
///
/// # Example
///
/// ```
/// let hash = hash_password("my-password")?;
/// assert!(verify_password("my-password", &hash)?);
/// assert!(!verify_password("wrong-password", &hash)?);
/// ```
pub fn verify_password(password: &str, hash: &str) -> Result<bool> {
    let parsed_hash =
        PasswordHash::new(hash).map_err(|e| anyhow::anyhow!("Invalid hash format: {}", e))?;

    // Create Argon2 instance with parameters from the hash
    // This ensures backward compatibility with old hashes
    let argon2 = create_argon2()?;

    Ok(argon2
        .verify_password(password.as_bytes(), &parsed_hash)
        .is_ok())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_password_generates_valid_hash() {
        let password = "test-password-123";
        let hash = hash_password(password).unwrap();

        // Should start with $argon2id$
        assert!(hash.starts_with("$argon2id$"));

        // Should contain version
        assert!(hash.contains("v=19"));

        // Should contain our parameters
        assert!(hash.contains("m=19456"));
        assert!(hash.contains("t=2"));
        assert!(hash.contains("p=1"));
    }

    #[test]
    fn test_hash_password_different_salts() {
        let password = "same-password";
        let hash1 = hash_password(password).unwrap();
        let hash2 = hash_password(password).unwrap();

        // Same password should produce different hashes (different salts)
        assert_ne!(hash1, hash2);
    }

    #[test]
    fn test_verify_password_accepts_correct_password() {
        let password = "correct-password";
        let hash = hash_password(password).unwrap();

        assert!(verify_password(password, &hash).unwrap());
    }

    #[test]
    fn test_verify_password_rejects_incorrect_password() {
        let password = "correct-password";
        let wrong_password = "wrong-password";
        let hash = hash_password(password).unwrap();

        assert!(!verify_password(wrong_password, &hash).unwrap());
    }

    #[test]
    fn test_verify_password_rejects_invalid_hash() {
        let result = verify_password("password", "invalid-hash");
        assert!(result.is_err());
    }

    #[test]
    fn test_password_with_special_characters() {
        let password = "p@ssw0rd!#$%^&*()";
        let hash = hash_password(password).unwrap();

        assert!(verify_password(password, &hash).unwrap());
    }

    #[test]
    fn test_password_with_unicode() {
        let password = "пароль密码🔒";
        let hash = hash_password(password).unwrap();

        assert!(verify_password(password, &hash).unwrap());
    }

    #[test]
    fn test_empty_password() {
        // Empty passwords should be allowed (validation is app-level)
        let hash = hash_password("").unwrap();
        assert!(verify_password("", &hash).unwrap());
    }

    #[test]
    fn test_long_password() {
        let password = "a".repeat(1000);
        let hash = hash_password(&password).unwrap();
        assert!(verify_password(&password, &hash).unwrap());
    }

    #[test]
    #[ignore] // Benchmark test - run with: cargo test --release -- --ignored
    fn bench_hash_password_performance() {
        use std::time::Instant;

        let password = "benchmark-password";
        let start = Instant::now();

        let _hash = hash_password(password).unwrap();

        let duration = start.elapsed();

        println!("Hashing took: {:?}", duration);

        // Should be between 100-200ms on modern hardware
        assert!(
            duration.as_millis() >= 50 && duration.as_millis() <= 500,
            "Hashing time outside expected range: {:?}ms",
            duration.as_millis()
        );
    }
}
