//! syntek-pyo3 — PyO3 Django bindings exposing syntek-crypto field encryption
//!
//! Exposes six functions to Python:
//! - `encrypt_field(plaintext, key, model, field)` → `ciphertext`
//! - `decrypt_field(ciphertext, key, model, field)` → `plaintext`
//! - `hash_password(password)` → `hash`
//! - `verify_password(password, hash)` → `bool`
//! - `encrypt_fields_batch(fields, key, model)` → `list[str]`
//! - `decrypt_fields_batch(fields, key, model)` → `list[str]`
//!
//! Also exposes `EncryptedField` and `EncryptedFieldDescriptor` for Django model integration.

use base64ct::{Base64, Encoding};
use pyo3::prelude::*;

// ---------------------------------------------------------------------------
// Internal helper — pure Rust, also exposed for Rust tests
// ---------------------------------------------------------------------------

/// Returns `true` when `s` is valid base64ct-encoded data whose decoded byte
/// length is at least 28 (12-byte nonce + 16-byte GCM tag minimum).
pub fn is_valid_ciphertext_format(s: &str) -> bool {
    match Base64::decode_vec(s) {
        Ok(bytes) => bytes.len() >= 28_usize,
        Err(_) => false,
    }
}

// ---------------------------------------------------------------------------
// Error types — exported for Rust integration tests
// ---------------------------------------------------------------------------

/// Returned when AES-256-GCM decryption fails at the PyO3 boundary.
#[derive(Debug, thiserror::Error)]
#[error("decryption error: {0}")]
pub struct DecryptionError(String);

impl DecryptionError {
    pub fn new(msg: impl Into<String>) -> Self {
        Self(msg.into())
    }
}

/// Returned when one field in a batch decryption fails.
#[derive(Debug, thiserror::Error)]
#[error("batch decryption error on field '{field}': {reason}")]
pub struct BatchDecryptionError {
    field: String,
    reason: String,
}

impl BatchDecryptionError {
    pub fn new(field: impl Into<String>, reason: impl Into<String>) -> Self {
        Self {
            field: field.into(),
            reason: reason.into(),
        }
    }
}

// ---------------------------------------------------------------------------
// Internal: map CryptoError → PyErr (ValueError)
// ---------------------------------------------------------------------------

fn crypto_err_to_py(e: syntek_crypto::CryptoError) -> PyErr {
    pyo3::exceptions::PyValueError::new_err(e.to_string())
}

// ---------------------------------------------------------------------------
// PyO3 functions
// ---------------------------------------------------------------------------

#[pyfunction]
fn encrypt_field(plaintext: &str, key: &[u8], model: &str, field: &str) -> PyResult<String> {
    syntek_crypto::encrypt_field(plaintext, key, model, field).map_err(crypto_err_to_py)
}

#[pyfunction]
fn decrypt_field(ciphertext: &str, key: &[u8], model: &str, field: &str) -> PyResult<String> {
    syntek_crypto::decrypt_field(ciphertext, key, model, field).map_err(crypto_err_to_py)
}

#[pyfunction]
fn hash_password(password: &str) -> PyResult<String> {
    syntek_crypto::hash_password(password).map_err(crypto_err_to_py)
}

#[pyfunction]
fn verify_password(password: &str, hash: &str) -> PyResult<bool> {
    syntek_crypto::verify_password(password, hash).map_err(crypto_err_to_py)
}

#[pyfunction]
fn encrypt_fields_batch(
    fields: Vec<(String, String)>,
    key: &[u8],
    model: &str,
) -> PyResult<Vec<String>> {
    let borrowed: Vec<(&str, &str)> = fields
        .iter()
        .map(|(f, v)| (f.as_str(), v.as_str()))
        .collect();
    syntek_crypto::encrypt_fields_batch(&borrowed, key, model).map_err(crypto_err_to_py)
}

#[pyfunction]
fn decrypt_fields_batch(
    fields: Vec<(String, String)>,
    key: &[u8],
    model: &str,
) -> PyResult<Vec<String>> {
    let borrowed: Vec<(&str, &str)> = fields
        .iter()
        .map(|(f, v)| (f.as_str(), v.as_str()))
        .collect();
    syntek_crypto::decrypt_fields_batch(&borrowed, key, model).map_err(crypto_err_to_py)
}

// ---------------------------------------------------------------------------
// EncryptedFieldDescriptor — installed on Django model classes
// ---------------------------------------------------------------------------

/// Descriptor installed on a Django model class by `EncryptedField.contribute_to_class`.
///
/// Records the model and field names so the GraphQL middleware can resolve the
/// correct AAD pair without manual annotation.
#[pyclass]
pub struct EncryptedFieldDescriptor {
    #[pyo3(get)]
    pub model_name: String,
    #[pyo3(get)]
    pub field_name: String,
}

#[pymethods]
impl EncryptedFieldDescriptor {
    #[new]
    fn new(model_name: String, field_name: String) -> Self {
        Self {
            model_name,
            field_name,
        }
    }
}

// ---------------------------------------------------------------------------
// EncryptedField — storage-and-validation Django field
// ---------------------------------------------------------------------------

/// A Django model field that stores ciphertext only.
///
/// Responsibilities:
/// - Accept ciphertext (valid base64ct, decoded >= 28 bytes) on `pre_save`.
/// - Reject plaintext with `ValidationError` before any DB write.
/// - Return raw ciphertext from `from_db_value` — no decryption.
/// - Install an `EncryptedFieldDescriptor` on the model class via `contribute_to_class`.
#[pyclass]
pub struct EncryptedField {
    #[pyo3(get, set)]
    pub attname: String,
}

#[pymethods]
impl EncryptedField {
    #[new]
    fn new() -> Self {
        Self {
            attname: String::new(),
        }
    }

    /// Raise Django's `ValidationError` if `value` is not a valid ciphertext.
    fn validate(
        &self,
        py: Python<'_>,
        value: &str,
        model_instance: Option<Py<PyAny>>,
    ) -> PyResult<()> {
        let _ = model_instance;
        if is_valid_ciphertext_format(value) {
            return Ok(());
        }
        let exc_module = PyModule::import(py, "django.core.exceptions")?;
        let ve_cls = exc_module.getattr("ValidationError")?;
        let msg = "Value is not valid ciphertext. \
                   Expected base64ct-encoded data with at least 28 decoded bytes.";
        let exc = ve_cls.call1((msg,))?;
        Err(PyErr::from_value(exc.into_any()))
    }

    /// Passthrough — returns the raw ciphertext from the database unchanged.
    ///
    /// Decryption is the GraphQL middleware's responsibility.
    // `from_db_value` is a Django API convention — the `from_*` naming is intentional.
    #[allow(clippy::wrong_self_convention)]
    fn from_db_value(
        &self,
        value: Option<&str>,
        expression: Option<Py<PyAny>>,
        connection: Option<Py<PyAny>>,
    ) -> Option<String> {
        let _ = (expression, connection);
        value.map(str::to_owned)
    }

    /// Validate then return the field value unchanged; raise `ValidationError` for plaintext.
    fn pre_save(&self, py: Python<'_>, instance: Bound<'_, PyAny>, add: bool) -> PyResult<String> {
        let _ = add;
        let value: String = instance.getattr(self.attname.as_str())?.extract()?;
        self.validate(py, &value, None)?;
        Ok(value)
    }

    /// Set `field.attname = name` and install an `EncryptedFieldDescriptor` on the class.
    fn contribute_to_class(
        &mut self,
        py: Python<'_>,
        cls: Bound<'_, PyAny>,
        name: &str,
    ) -> PyResult<()> {
        self.attname = name.to_owned();
        let model_name: String = cls.getattr("__name__")?.extract()?;
        let descriptor = Py::new(
            py,
            EncryptedFieldDescriptor {
                model_name,
                field_name: name.to_owned(),
            },
        )?;
        cls.setattr(name, descriptor)?;
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Module entry point
// ---------------------------------------------------------------------------

#[pymodule]
fn syntek_pyo3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encrypt_field, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_field, m)?)?;
    m.add_function(wrap_pyfunction!(hash_password, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_fields_batch, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_fields_batch, m)?)?;
    m.add_class::<EncryptedField>()?;
    m.add_class::<EncryptedFieldDescriptor>()?;
    Ok(())
}
