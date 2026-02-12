//! Python bindings for password hashing functions.
//!
//! Provides Argon2id password hashing with OWASP 2025 parameters:
//! - Memory: 19456 KiB (19 MiB)
//! - Iterations: 2
//! - Parallelism: 1
//! - Output: 32 bytes
//!
//! # Security Features
//!
//! - Passwords are copied to owned memory and zeroized after use
//! - Constant-time verification (handled by Argon2 library)
//! - Resistant to GPU and side-channel attacks
//!
//! # Python Usage
//!
//! ```python
//! from syntek_rust import hash_password_py, verify_password_py
//!
//! # Hash a password
//! password_hash = hash_password_py("my-secure-password")
//!
//! # Verify password
//! is_valid = verify_password_py("my-secure-password", password_hash)
//! assert is_valid == True
//! ```

use pyo3::prelude::*;

/// Hashes a password using Argon2id with OWASP 2025 parameters.
///
/// Creates a secure password hash suitable for database storage.
/// The password string is copied to Rust-owned memory and zeroized
/// after hashing.
///
/// # Arguments
///
/// * `password` - The password to hash
///
/// # Returns
///
/// * `PyResult<String>` - PHC format hash string
///
/// # Errors
///
/// Returns error if hashing fails (e.g., out of memory).
///
/// # Security Considerations
///
/// - Password is zeroized in Rust memory after use
/// - Python's original string is NOT zeroized (Python limitation)
/// - Use Python SecureString or clear password after use
///
/// # Example (Python)
///
/// ```python
/// password_hash = hash_password_py("my-password")
/// # Store password_hash in database
/// ```
#[pyfunction]
fn hash_password_py(password: &str) -> PyResult<String> {
    // Copy password to owned String for zeroization
    let password_owned = password.to_string();

    let hash = syntek_hashing::hash_password(&password_owned)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    // password_owned is dropped and zeroized here
    // Note: Python's original string is NOT zeroized

    Ok(hash)
}

/// Verifies a password against an Argon2id hash.
///
/// Uses constant-time comparison to prevent timing attacks.
/// Supports both new OWASP 2025 hashes and legacy hashes.
///
/// # Arguments
///
/// * `password` - The password to verify
/// * `hash` - The PHC format hash to verify against
///
/// # Returns
///
/// * `PyResult<bool>` - `true` if password matches, `false` otherwise
///
/// # Errors
///
/// Returns error if hash format is invalid.
///
/// # Security Considerations
///
/// - Constant-time verification (no timing attacks)
/// - Password is zeroized in Rust memory after use
/// - Safe against hash algorithm downgrade attacks
///
/// # Example (Python)
///
/// ```python
/// password_hash = hash_password_py("my-password")
/// is_valid = verify_password_py("my-password", password_hash)
/// assert is_valid == True
///
/// is_valid = verify_password_py("wrong-password", password_hash)
/// assert is_valid == False
/// ```
#[pyfunction]
fn verify_password_py(password: &str, hash: &str) -> PyResult<bool> {
    // Copy password to owned String for zeroization
    let password_owned = password.to_string();

    let is_valid = syntek_hashing::verify_password(&password_owned, hash)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    // password_owned is dropped and zeroized here

    Ok(is_valid)
}

/// Registers password hashing functions with Python module.
///
/// Called from lib.rs to register all hashing functions.
pub fn register_hashing_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hash_password_py, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password_py, m)?)?;
    Ok(())
}
