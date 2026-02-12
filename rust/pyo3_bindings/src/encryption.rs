//! Python bindings for encryption functions
//!
//! Provides Python-accessible wrappers for Rust encryption operations.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::collections::HashMap;
use syntek_encryption::{decrypt_batch, decrypt_field, encrypt_batch, encrypt_field};

/// Encrypt a single field value (Python binding)
///
/// # Arguments
///
/// * `plaintext` - The plaintext string to encrypt
/// * `key` - 32-byte encryption key as bytes
///
/// # Returns
///
/// Returns encrypted bytes (nonce + ciphertext)
///
/// # Example (Python)
///
/// ```python
/// from syntek_rust import encrypt_field
///
/// key = b"a" * 32  # 32-byte key
/// encrypted = encrypt_field("sensitive data", key)
/// ```
#[pyfunction]
fn encrypt_field_py(py: Python<'_>, plaintext: &str, key: &[u8]) -> PyResult<Py<PyBytes>> {
    // Call the Rust encryption function
    let encrypted = encrypt_field(plaintext, key)
        .map_err(|e| PyValueError::new_err(format!("Encryption failed: {}", e)))?;

    // Convert to Python bytes
    Ok(PyBytes::new(py, &encrypted).into())
}

/// Decrypt a single field value (Python binding)
///
/// # Arguments
///
/// * `ciphertext` - The encrypted data (nonce + ciphertext)
/// * `key` - 32-byte decryption key as bytes
///
/// # Returns
///
/// Returns decrypted plaintext string
///
/// # Example (Python)
///
/// ```python
/// from syntek_rust import decrypt_field
///
/// key = b"a" * 32  # 32-byte key
/// plaintext = decrypt_field(encrypted, key)
/// print(plaintext)
/// ```
#[pyfunction]
fn decrypt_field_py(ciphertext: &[u8], key: &[u8]) -> PyResult<String> {
    // Call the Rust decryption function
    let plaintext = decrypt_field(ciphertext, key)
        .map_err(|e| PyValueError::new_err(format!("Decryption failed: {}", e)))?;

    Ok(plaintext)
}

/// Encrypt multiple fields together (Python binding)
///
/// # Arguments
///
/// * `fields` - Dictionary of field names to plaintext values
/// * `key` - 32-byte encryption key as bytes
///
/// # Returns
///
/// Returns serialized encrypted batch as bytes
///
/// # Example (Python)
///
/// ```python
/// from syntek_rust import encrypt_batch
///
/// key = b"a" * 32
/// fields = {
///     "email": "user@example.com",
///     "phone": "+1234567890"
/// }
/// encrypted = encrypt_batch(fields, key)
/// ```
#[pyfunction]
fn encrypt_batch_py(
    py: Python<'_>,
    fields: HashMap<String, String>,
    key: &[u8],
) -> PyResult<Py<PyBytes>> {
    // Call the Rust batch encryption function
    let encrypted = encrypt_batch(fields, key)
        .map_err(|e| PyValueError::new_err(format!("Batch encryption failed: {}", e)))?;

    // Convert to Python bytes
    Ok(PyBytes::new(py, &encrypted).into())
}

/// Decrypt multiple fields (Python binding)
///
/// # Arguments
///
/// * `ciphertext` - Serialized encrypted batch
/// * `key` - 32-byte decryption key as bytes
///
/// # Returns
///
/// Returns dictionary of field names to decrypted plaintext values
///
/// # Example (Python)
///
/// ```python
/// from syntek_rust import decrypt_batch
///
/// key = b"a" * 32
/// fields = decrypt_batch(encrypted, key)
/// print(fields["email"])  # "user@example.com"
/// ```
#[pyfunction]
fn decrypt_batch_py(ciphertext: &[u8], key: &[u8]) -> PyResult<HashMap<String, String>> {
    // Call the Rust batch decryption function
    let fields = decrypt_batch(ciphertext, key)
        .map_err(|e| PyValueError::new_err(format!("Batch decryption failed: {}", e)))?;

    Ok(fields)
}

/// Register encryption functions with the Python module
pub fn register_encryption_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encrypt_field_py, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_field_py, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_batch_py, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_batch_py, m)?)?;
    Ok(())
}
