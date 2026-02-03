//! PyO3 bindings for Syntek Rust modules

use pyo3::prelude::*;

mod encryption;
mod hashing;
mod llm;

#[pymodule]
fn syntek_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    encryption::register_encryption_functions(m)?;
    hashing::register_hashing_functions(m)?;
    llm::register_llm_functions(m)?;
    Ok(())
}
