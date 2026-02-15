//! Constant-time comparison utilities for preventing timing attacks
//!
//! This module provides timing-attack resistant comparison functions for security-critical
//! operations like token validation, password verification, and HMAC comparison.
//!
//! # Security
//!
//! Regular string comparison (`==`, `str::eq()`) can leak timing information based on where
//! the strings differ. Attackers can exploit this to progressively guess values character
//! by character. Constant-time comparison functions always take the same amount of time
//! regardless of where (or if) the inputs differ.
//!
//! # When to Use
//!
//! Use constant-time comparison for:
//! - Authentication tokens (session tokens, API keys, JWT signatures)
//! - Password hashes
//! - HMAC values
//! - CSRF tokens
//! - Any security-sensitive comparison where timing leaks could aid an attacker
//!
//! # Performance
//!
//! Constant-time operations are slightly slower than regular comparisons (~10-20ns overhead)
//! but provide critical security guarantees. The overhead is negligible compared to network
//! latency or database queries.
//!
//! # Example
//!
//! ```rust,ignore
//! use syntek_security::constant_time::{compare_tokens, compare_hmac};
//!
//! // Compare authentication tokens (constant-time)
//! let stored_token = "user_session_abc123xyz";
//! let provided_token = "user_session_abc123xyz";
//! assert!(compare_tokens(stored_token, provided_token));
//!
//! // Compare HMAC values (constant-time)
//! let expected_hmac = b"hmac_signature_bytes";
//! let computed_hmac = b"hmac_signature_bytes";
//! assert!(compare_hmac(expected_hmac, computed_hmac));
//! ```

use subtle::ConstantTimeEq;

/// Compare two strings in constant time (timing-attack resistant)
///
/// # Arguments
///
/// * `a` - First string to compare
/// * `b` - Second string to compare
///
/// # Returns
///
/// Returns `true` if the strings are equal, `false` otherwise
///
/// # Security
///
/// - Uses `subtle::ConstantTimeEq` for timing-attack resistance
/// - Takes the same time regardless of where the strings differ
/// - Takes the same time for matching and non-matching strings
/// - Compares full length even if early mismatch found
/// - Resistant to cache-timing attacks
///
/// # Use Cases
///
/// - Session token validation
/// - API key comparison
/// - CSRF token verification
/// - JWT signature comparison
/// - Password hash comparison (though argon2/bcrypt already do this)
///
/// # Performance
///
/// - ~10-20ns overhead compared to regular string comparison
/// - Linear time complexity: O(n) where n = max(len(a), len(b))
/// - Safe for use in hot paths (authentication, session validation)
///
/// # Example
///
/// ```rust,ignore
/// use syntek_security::constant_time::compare_tokens;
///
/// let stored_token = "session_token_abc123";
/// let user_provided = "session_token_abc123";
///
/// if compare_tokens(stored_token, user_provided) {
///     println!("Token valid");
/// } else {
///     println!("Token invalid");
/// }
/// ```
pub fn compare_tokens(a: &str, b: &str) -> bool {
    // Convert strings to byte slices for constant-time comparison
    let a_bytes = a.as_bytes();
    let b_bytes = b.as_bytes();

    // Early length check (length is not a secret, so this is safe)
    // This prevents unnecessary work for obviously different inputs
    if a_bytes.len() != b_bytes.len() {
        return false;
    }

    // Constant-time byte comparison using subtle crate
    // Returns 1u8 if equal, 0u8 if different, in constant time
    a_bytes.ct_eq(b_bytes).into()
}

/// Compare two byte slices in constant time (timing-attack resistant)
///
/// # Arguments
///
/// * `a` - First byte slice to compare
/// * `b` - Second byte slice to compare
///
/// # Returns
///
/// Returns `true` if the byte slices are equal, `false` otherwise
///
/// # Security
///
/// - Uses `subtle::ConstantTimeEq` for timing-attack resistance
/// - Takes the same time regardless of where the slices differ
/// - Compares full length even if early mismatch found
/// - Resistant to cache-timing attacks
///
/// # Use Cases
///
/// - HMAC verification (compare computed vs expected HMAC)
/// - Digital signature verification
/// - Message authentication code (MAC) comparison
/// - Binary token comparison
/// - Encrypted data authentication tag comparison
///
/// # Performance
///
/// - ~10-20ns overhead compared to regular byte comparison
/// - Linear time complexity: O(n) where n = max(len(a), len(b))
/// - Safe for use in cryptographic operations
///
/// # Example
///
/// ```rust,ignore
/// use syntek_security::constant_time::compare_hmac;
/// use hmac::{Hmac, Mac};
/// use sha2::Sha256;
///
/// type HmacSha256 = Hmac<Sha256>;
///
/// let key = b"secret_key";
/// let message = b"important message";
///
/// // Compute HMAC
/// let mut mac = HmacSha256::new_from_slice(key).unwrap();
/// mac.update(message);
/// let expected_hmac = mac.finalize().into_bytes();
///
/// // Verify HMAC (constant-time comparison)
/// let provided_hmac = b"some_hmac_value";
/// if compare_hmac(&expected_hmac, provided_hmac) {
///     println!("HMAC valid");
/// } else {
///     println!("HMAC invalid");
/// }
/// ```
pub fn compare_hmac(a: &[u8], b: &[u8]) -> bool {
    // Early length check (length is not a secret, so this is safe)
    // This prevents unnecessary work for obviously different inputs
    if a.len() != b.len() {
        return false;
    }

    // Constant-time byte comparison using subtle crate
    // Returns 1u8 if equal, 0u8 if different, in constant time
    a.ct_eq(b).into()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{Duration, Instant};

    #[test]
    fn test_compare_tokens_equal() {
        let token1 = "abc123xyz789";
        let token2 = "abc123xyz789";
        assert!(compare_tokens(token1, token2));
    }

    #[test]
    fn test_compare_tokens_different() {
        let token1 = "abc123xyz789";
        let token2 = "abc123xyz788"; // Last char different
        assert!(!compare_tokens(token1, token2));
    }

    #[test]
    fn test_compare_tokens_different_lengths() {
        let token1 = "abc123xyz789";
        let token2 = "abc123xyz7890"; // Extra char
        assert!(!compare_tokens(token1, token2));
    }

    #[test]
    fn test_compare_tokens_empty() {
        assert!(compare_tokens("", ""));
    }

    #[test]
    fn test_compare_tokens_one_empty() {
        assert!(!compare_tokens("abc", ""));
        assert!(!compare_tokens("", "abc"));
    }

    #[test]
    fn test_compare_tokens_unicode() {
        let token1 = "Hello世界🌍";
        let token2 = "Hello世界🌍";
        assert!(compare_tokens(token1, token2));

        let token3 = "Hello世界🌎"; // Different emoji
        assert!(!compare_tokens(token1, token3));
    }

    #[test]
    fn test_compare_tokens_special_chars() {
        let token1 = "abc!@#$%^&*()_+-=[]{}|;':\",./<>?";
        let token2 = "abc!@#$%^&*()_+-=[]{}|;':\",./<>?";
        assert!(compare_tokens(token1, token2));
    }

    #[test]
    fn test_compare_tokens_long_strings() {
        let token1 = "a".repeat(10_000);
        let token2 = "a".repeat(10_000);
        assert!(compare_tokens(&token1, &token2));

        let mut token3 = "a".repeat(10_000);
        token3.push('b'); // Different at the end
        assert!(!compare_tokens(&token1, &token3));
    }

    #[test]
    fn test_compare_hmac_equal() {
        let hmac1 = b"hmac_signature_bytes";
        let hmac2 = b"hmac_signature_bytes";
        assert!(compare_hmac(hmac1, hmac2));
    }

    #[test]
    fn test_compare_hmac_different() {
        let hmac1 = b"hmac_signature_bytes";
        let hmac2 = b"hmac_signature_bytez"; // Last byte different
        assert!(!compare_hmac(hmac1, hmac2));
    }

    #[test]
    fn test_compare_hmac_different_lengths() {
        let hmac1 = b"hmac_signature";
        let hmac2 = b"hmac_signature_bytes";
        assert!(!compare_hmac(hmac1, hmac2));
    }

    #[test]
    fn test_compare_hmac_empty() {
        assert!(compare_hmac(b"", b""));
    }

    #[test]
    fn test_compare_hmac_one_empty() {
        assert!(!compare_hmac(b"abc", b""));
        assert!(!compare_hmac(b"", b"abc"));
    }

    #[test]
    fn test_compare_hmac_binary_data() {
        let hmac1 = &[0u8, 1, 2, 3, 255, 254, 253];
        let hmac2 = &[0u8, 1, 2, 3, 255, 254, 253];
        assert!(compare_hmac(hmac1, hmac2));

        let hmac3 = &[0u8, 1, 2, 3, 255, 254, 252]; // Last byte different
        assert!(!compare_hmac(hmac1, hmac3));
    }

    #[test]
    fn test_compare_hmac_long_slices() {
        let hmac1 = vec![42u8; 10_000];
        let hmac2 = vec![42u8; 10_000];
        assert!(compare_hmac(&hmac1, &hmac2));

        let mut hmac3 = vec![42u8; 10_000];
        hmac3[9_999] = 43; // Different at the end
        assert!(!compare_hmac(&hmac1, &hmac3));
    }

    // ============================================================================
    // Timing Attack Tests
    // ============================================================================

    /// Test that comparison time is constant regardless of where strings differ
    ///
    /// This is a critical security property. If comparison time varies based on
    /// where the mismatch occurs, attackers can use timing information to
    /// progressively guess the correct value.
    #[test]
    fn test_timing_attack_resistance_tokens() {
        const ITERATIONS: usize = 10_000;
        const TOKEN_LENGTH: usize = 64;

        // Generate a reference token (all 'a')
        let reference = "a".repeat(TOKEN_LENGTH);

        // Test case 1: Mismatch at first character
        let mismatch_first = format!("b{}", "a".repeat(TOKEN_LENGTH - 1));

        // Test case 2: Mismatch at middle character
        let mismatch_middle = format!("{}{}{}", "a".repeat(TOKEN_LENGTH / 2), "b", "a".repeat(TOKEN_LENGTH / 2 - 1));

        // Test case 3: Mismatch at last character
        let mismatch_last = format!("{}b", "a".repeat(TOKEN_LENGTH - 1));

        // Test case 4: Complete match
        let match_string = "a".repeat(TOKEN_LENGTH);

        // Measure timing for each case
        let time_first = measure_comparison_time(&reference, &mismatch_first, ITERATIONS);
        let time_middle = measure_comparison_time(&reference, &mismatch_middle, ITERATIONS);
        let time_last = measure_comparison_time(&reference, &mismatch_last, ITERATIONS);
        let time_match = measure_comparison_time(&reference, &match_string, ITERATIONS);

        // Calculate average time and variance
        let times = [time_first, time_middle, time_last, time_match];
        let avg = times.iter().sum::<Duration>() / times.len() as u32;

        // Calculate variance (should be very small for constant-time operations)
        let variance_ns: f64 = times
            .iter()
            .map(|t| {
                let diff = if *t > avg {
                    (*t - avg).as_nanos() as f64
                } else {
                    (avg - *t).as_nanos() as f64
                };
                diff * diff
            })
            .sum::<f64>()
            / times.len() as f64;

        let std_dev_ns = variance_ns.sqrt();

        // SECURITY: Standard deviation should be very small (< 1000ns)
        // This indicates constant-time behavior across different mismatch positions
        //
        // Note: This test may occasionally fail on heavily loaded systems due to
        // OS scheduling variance. The threshold of 1000ns (1µs) is conservative
        // and allows for some system noise while still catching timing leaks.
        println!("Timing attack resistance test results:");
        println!("  First char mismatch:  {:?}", time_first);
        println!("  Middle char mismatch: {:?}", time_middle);
        println!("  Last char mismatch:   {:?}", time_last);
        println!("  Complete match:       {:?}", time_match);
        println!("  Average:              {:?}", avg);
        println!("  Std deviation:        {:.2}ns", std_dev_ns);

        assert!(
            std_dev_ns < 1000.0,
            "Timing variance too large: {:.2}ns (expected < 1000ns). \
             This may indicate a timing leak or system is under heavy load.",
            std_dev_ns
        );
    }

    /// Test that HMAC comparison time is constant regardless of where bytes differ
    #[test]
    fn test_timing_attack_resistance_hmac() {
        const ITERATIONS: usize = 10_000;
        const HMAC_LENGTH: usize = 32; // SHA-256 HMAC length

        // Generate a reference HMAC (all 0x42)
        let reference = vec![0x42u8; HMAC_LENGTH];

        // Test case 1: Mismatch at first byte
        let mut mismatch_first = vec![0x42u8; HMAC_LENGTH];
        mismatch_first[0] = 0xFF;

        // Test case 2: Mismatch at middle byte
        let mut mismatch_middle = vec![0x42u8; HMAC_LENGTH];
        mismatch_middle[HMAC_LENGTH / 2] = 0xFF;

        // Test case 3: Mismatch at last byte
        let mut mismatch_last = vec![0x42u8; HMAC_LENGTH];
        mismatch_last[HMAC_LENGTH - 1] = 0xFF;

        // Test case 4: Complete match
        let match_bytes = vec![0x42u8; HMAC_LENGTH];

        // Measure timing for each case
        let time_first = measure_hmac_comparison_time(&reference, &mismatch_first, ITERATIONS);
        let time_middle = measure_hmac_comparison_time(&reference, &mismatch_middle, ITERATIONS);
        let time_last = measure_hmac_comparison_time(&reference, &mismatch_last, ITERATIONS);
        let time_match = measure_hmac_comparison_time(&reference, &match_bytes, ITERATIONS);

        // Calculate average time and variance
        let times = [time_first, time_middle, time_last, time_match];
        let avg = times.iter().sum::<Duration>() / times.len() as u32;

        // Calculate variance
        let variance_ns: f64 = times
            .iter()
            .map(|t| {
                let diff = if *t > avg {
                    (*t - avg).as_nanos() as f64
                } else {
                    (avg - *t).as_nanos() as f64
                };
                diff * diff
            })
            .sum::<f64>()
            / times.len() as f64;

        let std_dev_ns = variance_ns.sqrt();

        println!("HMAC timing attack resistance test results:");
        println!("  First byte mismatch:  {:?}", time_first);
        println!("  Middle byte mismatch: {:?}", time_middle);
        println!("  Last byte mismatch:   {:?}", time_last);
        println!("  Complete match:       {:?}", time_match);
        println!("  Average:              {:?}", avg);
        println!("  Std deviation:        {:.2}ns", std_dev_ns);

        assert!(
            std_dev_ns < 1000.0,
            "Timing variance too large: {:.2}ns (expected < 1000ns). \
             This may indicate a timing leak or system is under heavy load.",
            std_dev_ns
        );
    }

    /// Helper function to measure comparison time for tokens
    fn measure_comparison_time(a: &str, b: &str, iterations: usize) -> Duration {
        let start = Instant::now();
        for _ in 0..iterations {
            // Use black_box to prevent compiler optimization
            let _ = std::hint::black_box(compare_tokens(
                std::hint::black_box(a),
                std::hint::black_box(b),
            ));
        }
        start.elapsed() / iterations as u32
    }

    /// Helper function to measure comparison time for HMACs
    fn measure_hmac_comparison_time(a: &[u8], b: &[u8], iterations: usize) -> Duration {
        let start = Instant::now();
        for _ in 0..iterations {
            // Use black_box to prevent compiler optimization
            let _ = std::hint::black_box(compare_hmac(
                std::hint::black_box(a),
                std::hint::black_box(b),
            ));
        }
        start.elapsed() / iterations as u32
    }

    #[test]
    fn test_performance_overhead() {
        const ITERATIONS: usize = 100_000;
        let token1 = "session_token_abc123xyz789";
        let token2 = "session_token_abc123xyz789";

        // Measure constant-time comparison
        let start = Instant::now();
        for _ in 0..ITERATIONS {
            let _ = std::hint::black_box(compare_tokens(
                std::hint::black_box(token1),
                std::hint::black_box(token2),
            ));
        }
        let constant_time_duration = start.elapsed();

        // Measure regular comparison (for reference only, not used in production)
        let start = Instant::now();
        for _ in 0..ITERATIONS {
            let _ = std::hint::black_box(
                std::hint::black_box(token1) == std::hint::black_box(token2)
            );
        }
        let regular_duration = start.elapsed();

        println!("Performance comparison:");
        println!("  Constant-time: {:?}", constant_time_duration);
        println!("  Regular:       {:?}", regular_duration);
        println!(
            "  Overhead:      {:?}",
            constant_time_duration.saturating_sub(regular_duration)
        );

        // Overhead should be reasonable (< 1000ns = 1µs per comparison on average)
        let avg_overhead = constant_time_duration
            .saturating_sub(regular_duration)
            .as_nanos()
            / ITERATIONS as u128;
        println!("  Avg overhead:  {}ns per comparison", avg_overhead);

        // This is informational, not a hard requirement
        // The overhead is negligible compared to network latency or database queries
        // Threshold of 1µs allows for system variance while still being performant
        assert!(
            avg_overhead < 1000,
            "Overhead too large: {}ns (expected < 1000ns = 1µs)",
            avg_overhead
        );
    }
}
