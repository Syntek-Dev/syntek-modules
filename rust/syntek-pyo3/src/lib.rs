//! syntek-pyo3 — PyO3 bindings exposing syntek-crypto to Django
//!
//! Exposes four functions to Python:
//! - `encrypt_field(plaintext, key)` -> `ciphertext`
//! - `decrypt_field(ciphertext, key)` -> `plaintext`
//! - `hash_password(password)` -> `hash`
//! - `verify_password(password, hash)` -> `bool`

use pyo3::prelude::*;

/// Module entry point — functions registered during us001/syntek-crypto sprint.
#[pymodule]
fn syntek_pyo3(_py: Python<'_>, _m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
