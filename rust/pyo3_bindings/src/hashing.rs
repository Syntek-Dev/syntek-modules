//! Python bindings for hashing functions

use pyo3::prelude::*;

#[pyfunction]
fn hash_password_py(_password: &str) -> PyResult<String> {
    // TODO: Implement
    Ok(String::new())
}

#[pyfunction]
fn verify_password_py(_password: &str, _hash: &str) -> PyResult<bool> {
    // TODO: Implement
    Ok(false)
}

pub fn register_hashing_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hash_password_py, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password_py, m)?)?;
    Ok(())
}
