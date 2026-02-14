//! PyO3 bindings for security utilities
//!
//! Provides Python bindings for:
//! - Constant-time token comparison (timing-attack resistant)
//! - Constant-time HMAC comparison (timing-attack resistant)

use pyo3::prelude::*;
use syntek_security::constant_time;

/// Compare two tokens in constant time (timing-attack resistant)
///
/// This function compares two strings in constant time, making it resistant to
/// timing attacks. It always takes the same amount of time regardless of where
/// (or if) the strings differ.
///
/// # Arguments
///
/// * `a` - First token string
/// * `b` - Second token string
///
/// # Returns
///
/// Returns `True` if the tokens are equal, `False` otherwise
///
/// # Security
///
/// - Uses constant-time comparison to prevent timing attacks
/// - Safe for comparing session tokens, API keys, CSRF tokens
/// - Takes the same time for matching and non-matching strings
///
/// # Example
///
/// ```python
/// from syntek_rust import compare_tokens_py
///
/// stored_token = "session_token_abc123"
/// user_provided = "session_token_abc123"
///
/// if compare_tokens_py(stored_token, user_provided):
///     print("Token valid")
/// else:
///     print("Token invalid")
/// ```
#[pyfunction]
#[pyo3(name = "compare_tokens")]
fn compare_tokens_py(a: &str, b: &str) -> bool {
    constant_time::compare_tokens(a, b)
}

/// Compare two HMAC values in constant time (timing-attack resistant)
///
/// This function compares two byte arrays in constant time, making it resistant to
/// timing attacks. It always takes the same amount of time regardless of where
/// (or if) the byte arrays differ.
///
/// # Arguments
///
/// * `a` - First HMAC bytes
/// * `b` - Second HMAC bytes
///
/// # Returns
///
/// Returns `True` if the HMACs are equal, `False` otherwise
///
/// # Security
///
/// - Uses constant-time comparison to prevent timing attacks
/// - Safe for comparing HMAC values, digital signatures, MACs
/// - Takes the same time for matching and non-matching byte arrays
///
/// # Example
///
/// ```python
/// from syntek_rust import compare_hmac_py
/// import hmac
/// import hashlib
///
/// key = b"secret_key"
/// message = b"important message"
///
/// # Compute HMAC
/// expected_hmac = hmac.new(key, message, hashlib.sha256).digest()
/// provided_hmac = b"some_hmac_value"
///
/// if compare_hmac_py(expected_hmac, provided_hmac):
///     print("HMAC valid")
/// else:
///     print("HMAC invalid")
/// ```
#[pyfunction]
#[pyo3(name = "compare_hmac")]
fn compare_hmac_py(a: &[u8], b: &[u8]) -> bool {
    constant_time::compare_hmac(a, b)
}

/// Register security functions in the Python module
pub fn register_security_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compare_tokens_py, m)?)?;
    m.add_function(wrap_pyfunction!(compare_hmac_py, m)?)?;
    Ok(())
}
