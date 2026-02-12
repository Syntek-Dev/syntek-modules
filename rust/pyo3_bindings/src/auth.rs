//! PyO3 bindings for authentication functions.
//!
//! Provides Python bindings for:
//! - Email encryption/decryption/hashing
//! - Phone number encryption/decryption/hashing
//! - IP address encryption/decryption/hashing
//! - Token generation
//! - Password hashing and verification
//!
//! # Security Features
//!
//! - Zeroizes sensitive data in Rust memory
//! - Input validation before encryption
//! - HMAC-SHA256 for constant-time lookups
//! - Argon2id OWASP 2025 parameters
//!
//! # Python Usage
//!
//! ```python
//! from syntek_rust import (
//!     encrypt_email_py, decrypt_email_py, hash_email_py,
//!     generate_token_py, generate_verification_code_py,
//!     hash_password_py, verify_password_py,
//! )
//!
//! # Email encryption
//! key = b"32-byte-encryption-key-!!!!!!!!!"
//! encrypted = encrypt_email_py("user@example.com", key)
//! decrypted = decrypt_email_py(encrypted, key)
//!
//! # HMAC hashing
//! hmac_key = b"32-byte-hmac-key-!!!!!!!!!!!!!!!!!"
//! email_hash = hash_email_py("user@example.com", hmac_key)
//!
//! # Token generation
//! token = generate_token_py(32)  # 32 bytes
//! code = generate_verification_code_py()  # 6-digit code
//!
//! # Password hashing
//! password_hash = hash_password_py("my-password")
//! is_valid = verify_password_py("my-password", password_hash)
//! ```

use pyo3::prelude::*;
use pyo3::types::PyBytes;

/// Registers authentication functions with Python module.
///
/// Called from lib.rs to register all authentication-related functions.
pub fn register_auth_functions(module: &Bound<'_, PyModule>) -> PyResult<()> {
    // Email functions
    module.add_function(wrap_pyfunction!(encrypt_email_py, module)?)?;
    module.add_function(wrap_pyfunction!(decrypt_email_py, module)?)?;
    module.add_function(wrap_pyfunction!(hash_email_py, module)?)?;

    // Phone functions
    module.add_function(wrap_pyfunction!(encrypt_phone_number_py, module)?)?;
    module.add_function(wrap_pyfunction!(decrypt_phone_number_py, module)?)?;
    module.add_function(wrap_pyfunction!(hash_phone_py, module)?)?;

    // IP functions
    module.add_function(wrap_pyfunction!(encrypt_ip_address_py, module)?)?;
    module.add_function(wrap_pyfunction!(decrypt_ip_address_py, module)?)?;
    module.add_function(wrap_pyfunction!(hash_ip_address_py, module)?)?;

    // Token functions
    module.add_function(wrap_pyfunction!(generate_token_py, module)?)?;
    module.add_function(wrap_pyfunction!(generate_verification_code_py, module)?)?;
    module.add_function(wrap_pyfunction!(hash_token_py, module)?)?;

    // OAuth functions
    module.add_function(wrap_pyfunction!(generate_pkce_verifier_py, module)?)?;
    module.add_function(wrap_pyfunction!(generate_pkce_challenge_py, module)?)?;
    module.add_function(wrap_pyfunction!(generate_pkce_pair_py, module)?)?;
    module.add_function(wrap_pyfunction!(encrypt_oauth_token_py, module)?)?;
    module.add_function(wrap_pyfunction!(decrypt_oauth_token_py, module)?)?;

    Ok(())
}

// ============================================================================
// Email Functions
// ============================================================================

/// Encrypts an email address.
///
/// Validates email format before encryption to ensure data integrity.
///
/// # Arguments
///
/// * `email` - The email address to encrypt
/// * `key` - The encryption key (32 bytes for ChaCha20-Poly1305)
///
/// # Returns
///
/// * `PyResult<Vec<u8>>` - Encrypted email as bytes (includes nonce)
///
/// # Errors
///
/// Returns error if email is invalid or encryption fails.
///
/// # Example (Python)
///
/// ```python
/// key = b"32-byte-encryption-key-!!!!!!!!!"
/// encrypted = encrypt_email_py("user@example.com", key)
/// ```
#[pyfunction]
fn encrypt_email_py(email: &str, key: &[u8]) -> PyResult<Vec<u8>> {
    // Validate email before encryption
    syntek_encryption::validators::validate_email(email)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    // Encrypt using field-level encryption
    let encrypted = syntek_encryption::encrypt_field(email, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(encrypted)
}

/// Decrypts an email address.
///
/// # Arguments
///
/// * `encrypted` - The encrypted email bytes
/// * `key` - The decryption key (must match encryption key)
///
/// # Returns
///
/// * `PyResult<String>` - Decrypted email address
///
/// # Errors
///
/// Returns error if decryption fails (wrong key or corrupted data).
///
/// # Example (Python)
///
/// ```python
/// key = b"32-byte-encryption-key-!!!!!!!!!"
/// encrypted = encrypt_email_py("user@example.com", key)
/// decrypted = decrypt_email_py(encrypted, key)
/// assert decrypted == "user@example.com"
/// ```
#[pyfunction]
fn decrypt_email_py(encrypted: &[u8], key: &[u8]) -> PyResult<String> {
    let decrypted = syntek_encryption::decrypt_field(encrypted, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(decrypted)
}

/// Hashes an email address for database lookup (HMAC-SHA256).
///
/// Creates a constant-time comparable hash that prevents timing attacks
/// and user enumeration.
///
/// # Arguments
///
/// * `email` - The email address to hash
/// * `key` - The HMAC key (minimum 32 bytes)
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded hash
///
/// # Example (Python)
///
/// ```python
/// hmac_key = b"32-byte-hmac-key-!!!!!!!!!!!!!!!!!"
/// hash = hash_email_py("user@example.com", hmac_key)
/// # Use hash for database index lookups
/// ```
#[pyfunction]
fn hash_email_py(email: &str, key: &[u8]) -> PyResult<String> {
    let hash = syntek_security::hash_email(email, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(hash)
}

// ============================================================================
// Phone Number Functions
// ============================================================================

/// Encrypts a phone number.
///
/// Validates phone format before encryption (E.164).
///
/// # Arguments
///
/// * `phone` - The phone number to encrypt
/// * `key` - The encryption key (32 bytes)
///
/// # Returns
///
/// * `PyResult<Vec<u8>>` - Encrypted phone as bytes
///
/// # Example (Python)
///
/// ```python
/// encrypted = encrypt_phone_number_py("+15551234567", key)
/// ```
#[pyfunction]
fn encrypt_phone_number_py(phone: &str, key: &[u8]) -> PyResult<Vec<u8>> {
    // Validate phone before encryption
    syntek_encryption::validators::validate_phone_number(phone)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let encrypted = syntek_encryption::encrypt_field(phone, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(encrypted)
}

/// Decrypts a phone number.
///
/// # Arguments
///
/// * `encrypted` - The encrypted phone bytes
/// * `key` - The decryption key
///
/// # Returns
///
/// * `PyResult<String>` - Decrypted phone number
#[pyfunction]
fn decrypt_phone_number_py(encrypted: &[u8], key: &[u8]) -> PyResult<String> {
    let decrypted = syntek_encryption::decrypt_field(encrypted, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(decrypted)
}

/// Hashes a phone number for database lookup (HMAC-SHA256).
///
/// Strips formatting before hashing for consistent lookups.
///
/// # Arguments
///
/// * `phone` - The phone number to hash
/// * `key` - The HMAC key (minimum 32 bytes)
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded hash
#[pyfunction]
fn hash_phone_py(phone: &str, key: &[u8]) -> PyResult<String> {
    let hash = syntek_security::hash_phone(phone, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(hash)
}

// ============================================================================
// IP Address Functions
// ============================================================================

/// Encrypts an IP address (IPv4 or IPv6).
///
/// Validates IP format before encryption.
///
/// # Arguments
///
/// * `ip` - The IP address to encrypt
/// * `key` - The encryption key (32 bytes)
///
/// # Returns
///
/// * `PyResult<Vec<u8>>` - Encrypted IP as bytes
///
/// # Example (Python)
///
/// ```python
/// encrypted_ipv4 = encrypt_ip_address_py("192.168.1.1", key)
/// encrypted_ipv6 = encrypt_ip_address_py("2001:0db8::1", key)
/// ```
#[pyfunction]
fn encrypt_ip_address_py(ip: &str, key: &[u8]) -> PyResult<Vec<u8>> {
    // Validate IP before encryption
    syntek_encryption::validators::validate_ip_address(ip)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let encrypted = syntek_encryption::encrypt_field(ip, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(encrypted)
}

/// Decrypts an IP address.
///
/// # Arguments
///
/// * `encrypted` - The encrypted IP bytes
/// * `key` - The decryption key
///
/// # Returns
///
/// * `PyResult<String>` - Decrypted IP address
#[pyfunction]
fn decrypt_ip_address_py(encrypted: &[u8], key: &[u8]) -> PyResult<String> {
    let decrypted = syntek_encryption::decrypt_field(encrypted, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(decrypted)
}

/// Hashes an IP address for database lookup (HMAC-SHA256).
///
/// # Arguments
///
/// * `ip` - The IP address to hash
/// * `key` - The HMAC key (minimum 32 bytes)
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded hash
#[pyfunction]
fn hash_ip_address_py(ip: &str, key: &[u8]) -> PyResult<String> {
    let hash = syntek_security::hash_ip(ip, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(hash)
}

// ============================================================================
// Token Generation Functions
// ============================================================================

/// Generates a cryptographically secure random token.
///
/// # Arguments
///
/// * `length` - Token length in bytes (default: 32, minimum: 16)
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded token
///
/// # Example (Python)
///
/// ```python
/// token = generate_token_py(32)  # ~43 characters
/// api_key = generate_token_py(64)  # ~86 characters
/// ```
#[pyfunction]
#[pyo3(signature = (length = 32))]
fn generate_token_py(length: usize) -> PyResult<String> {
    let token = syntek_security::generate_token(length)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(token)
}

/// Generates a cryptographically secure numeric verification code.
///
/// # Returns
///
/// * `PyResult<String>` - Zero-padded 6-digit code
///
/// # Example (Python)
///
/// ```python
/// code = generate_verification_code_py()
/// print(code)  # e.g., "042785"
/// ```
#[pyfunction]
fn generate_verification_code_py() -> PyResult<String> {
    let code = syntek_security::generate_verification_code()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(code)
}

/// Hashes a token using HMAC-SHA256.
///
/// Used for storing tokens securely in database (e.g., password reset tokens).
///
/// # Arguments
///
/// * `token` - The token to hash
/// * `key` - The HMAC key (minimum 32 bytes)
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded hash
///
/// # Example (Python)
///
/// ```python
/// token = generate_token_py(32)
/// token_hash = hash_token_py(token, hmac_key)
/// # Store token_hash in database
/// ```
#[pyfunction]
fn hash_token_py(token: &str, key: &[u8]) -> PyResult<String> {
    let hash = syntek_security::hash_for_lookup(token, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(hash)
}

// ============================================================================
// OAuth Functions
// ============================================================================

/// Generates a PKCE code verifier for mobile OAuth flows.
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded code verifier
///
/// # Example (Python)
///
/// ```python
/// verifier = generate_pkce_verifier_py()
/// # Store verifier on client
/// ```
#[pyfunction]
fn generate_pkce_verifier_py() -> PyResult<String> {
    let verifier = syntek_security::generate_pkce_code_verifier()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(verifier)
}

/// Generates a PKCE code challenge from a code verifier.
///
/// # Arguments
///
/// * `verifier` - The code verifier
///
/// # Returns
///
/// * `PyResult<String>` - URL-safe base64 encoded code challenge (SHA-256)
///
/// # Example (Python)
///
/// ```python
/// verifier = generate_pkce_verifier_py()
/// challenge = generate_pkce_challenge_py(verifier)
/// # Send challenge to OAuth provider
/// ```
#[pyfunction]
fn generate_pkce_challenge_py(verifier: &str) -> PyResult<String> {
    let challenge = syntek_security::generate_pkce_code_challenge(verifier)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(challenge)
}

/// Generates a matched PKCE verifier and challenge pair.
///
/// # Returns
///
/// * `PyResult<(String, String)>` - Tuple of (verifier, challenge)
///
/// # Example (Python)
///
/// ```python
/// verifier, challenge = generate_pkce_pair_py()
/// # Store verifier, send challenge to OAuth
/// ```
#[pyfunction]
fn generate_pkce_pair_py() -> PyResult<(String, String)> {
    let (verifier, challenge) = syntek_security::generate_pkce_pair()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok((verifier, challenge))
}

/// Encrypts an OAuth token (access or refresh token).
///
/// Uses the same encryption as email/phone (ChaCha20-Poly1305).
///
/// # Arguments
///
/// * `token` - The OAuth token to encrypt
/// * `key` - 32-byte encryption key
///
/// # Returns
///
/// * `PyResult<Vec<u8>>` - Encrypted token bytes
///
/// # Example (Python)
///
/// ```python
/// key = b"32-byte-encryption-key-!!!!!!!!!"
/// encrypted = encrypt_oauth_token_py(access_token, key)
/// ```
#[pyfunction]
fn encrypt_oauth_token_py(py: Python<'_>, token: &str, key: &[u8]) -> PyResult<Py<PyBytes>> {
    let encrypted = syntek_encryption::encrypt_field(token, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(PyBytes::new(py, &encrypted).into())
}

/// Decrypts an OAuth token.
///
/// # Arguments
///
/// * `encrypted` - The encrypted token bytes
/// * `key` - 32-byte decryption key (must match encryption key)
///
/// # Returns
///
/// * `PyResult<String>` - Decrypted OAuth token
///
/// # Example (Python)
///
/// ```python
/// key = b"32-byte-encryption-key-!!!!!!!!!"
/// token = decrypt_oauth_token_py(encrypted, key)
/// ```
#[pyfunction]
fn decrypt_oauth_token_py(encrypted: &[u8], key: &[u8]) -> PyResult<String> {
    let token = syntek_encryption::decrypt_field(encrypted, key)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(token)
}
