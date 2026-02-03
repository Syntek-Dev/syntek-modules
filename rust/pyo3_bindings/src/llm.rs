//! Python bindings for LLM gateway

use pyo3::prelude::*;

#[pyfunction]
fn llm_complete_py(_prompt: &str) -> PyResult<String> {
    // TODO: Implement
    Ok(String::new())
}

pub fn register_llm_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(llm_complete_py, m)?)?;
    Ok(())
}
