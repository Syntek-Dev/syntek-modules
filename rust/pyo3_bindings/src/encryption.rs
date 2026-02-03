//! Python bindings for encryption functions

use pyo3::prelude::*;

#[pyfunction]
fn encrypt_field_py(_plaintext: &str, _key: &[u8]) -> PyResult<Vec<u8>> {
    // TODO: Implement
    Ok(Vec::new())
}

#[pyfunction]
fn decrypt_field_py(_ciphertext: &[u8], _key: &[u8]) -> PyResult<String> {
    // TODO: Implement
    Ok(String::new())
}

pub fn register_encryption_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encrypt_field_py, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_field_py, m)?)?;
    Ok(())
}
