//! syntek-pyo3 — PyO3 Django bindings exposing syntek-crypto field encryption
//!
//! All encryption at the PyO3 boundary uses the **versioned** API from
//! `syntek_crypto::key_versioning`.  The unversioned `encrypt_field` /
//! `decrypt_field` from `syntek_crypto` are deliberately not exposed here —
//! they produce ciphertexts that are format-incompatible with key rotation
//! (US076).  All Python consumers must use a [`KeyRing`] (see below).
//!
//! # Ciphertext format (versioned)
//!
//! ```text
//! stored value = base64( version(2) || nonce(12) || ciphertext || tag(16) )
//! minimum decoded length: 30 bytes
//! version 0 is reserved; valid versions start at 1
//! ```
//!
//! # Python API
//!
//! ```python
//! from syntek_pyo3 import KeyRing, encrypt_field, decrypt_field
//!
//! ring = KeyRing()
//! ring.add(1, key_bytes)                                  # add version 1 key
//! ct = encrypt_field("hello@example.com", ring, "User", "email")
//! pt = decrypt_field(ct, ring, "User", "email")
//! ```
//!
//! # Exception types
//!
//! - `syntek_pyo3.DecryptionError` — single-field decrypt failure
//! - `syntek_pyo3.BatchDecryptionError` — any field in a batch decrypt fails
//!
//! Both inherit from Python's `ValueError`.
//!
//! # Plaintext zeroisation
//!
//! Intermediate Rust `String` values holding decrypted plaintext are wrapped in
//! `zeroize::Zeroizing<String>` before they cross the PyO3 boundary.  Once the
//! value is a Python `str`, zeroisation is no longer possible from the Rust side.
//! Consumer code should avoid holding decrypted values in long-lived variables.

use base64ct::{Base64, Encoding};
use pyo3::prelude::*;
use syntek_crypto::key_versioning::{
    KeyRing, KeyVersion, decrypt_fields_batch_versioned, decrypt_versioned,
    encrypt_fields_batch_versioned, encrypt_versioned,
};
use zeroize::Zeroizing;

// ---------------------------------------------------------------------------
// Internal helper — pure Rust, also exported for Rust tests
// ---------------------------------------------------------------------------

/// Returns `true` when `s` is a valid **versioned** ciphertext.
///
/// A valid versioned ciphertext must:
/// - Be valid base64ct-encoded data
/// - Decode to at least 30 bytes: `version(2) || nonce(12) || tag(16)`
/// - Have a non-zero version prefix (version 0 is reserved)
///
/// This rejects unversioned ciphertexts (28-byte minimum, no version prefix)
/// produced by the legacy `syntek_crypto::encrypt_field` API.  That API is
/// intentionally not exposed at the PyO3 boundary.
pub fn is_valid_ciphertext_format(s: &str) -> bool {
    match Base64::decode_vec(s) {
        Ok(bytes) if bytes.len() >= 30 => {
            // bytes[0..2] hold the big-endian key version. Version 0 is reserved.
            let version = u16::from_be_bytes([bytes[0], bytes[1]]);
            version != 0
        }
        _ => false,
    }
}

// ---------------------------------------------------------------------------
// Python exception classes — registered with the module
// ---------------------------------------------------------------------------

pyo3::create_exception!(
    syntek_pyo3,
    PyDecryptionError,
    pyo3::exceptions::PyValueError,
    "Raised when AES-256-GCM decryption fails (e.g. tampered ciphertext, AAD mismatch, or invalid key)."
);

pyo3::create_exception!(
    syntek_pyo3,
    PyBatchDecryptionError,
    pyo3::exceptions::PyValueError,
    "Raised when one or more fields in a batch decryption operation fail."
);

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
// Internal: map CryptoError → PyErr with specific exception types
// ---------------------------------------------------------------------------

/// Maps a `CryptoError` to the appropriate Python exception class.
///
/// - `DecryptionError` variants → `PyDecryptionError`
/// - `BatchError` variants → `PyBatchDecryptionError`
/// - All other variants → `PyValueError`
fn crypto_err_to_py(e: syntek_crypto::CryptoError) -> PyErr {
    match &e {
        syntek_crypto::CryptoError::DecryptionError(_) => PyDecryptionError::new_err(e.to_string()),
        syntek_crypto::CryptoError::BatchError { .. } => {
            PyBatchDecryptionError::new_err(e.to_string())
        }
        _ => pyo3::exceptions::PyValueError::new_err(e.to_string()),
    }
}

// ---------------------------------------------------------------------------
// Encrypted-field metadata registry (side-channel)
//
// Stores (model_name, field_name) pairs installed by EncryptedField's
// contribute_to_class.  This avoids overwriting the Django field object on
// the model class — the field remains intact for Django's _meta, migrations,
// and ORM introspection.
// ---------------------------------------------------------------------------

use std::sync::Mutex;

static ENCRYPTED_FIELD_REGISTRY: Mutex<Vec<(String, String)>> = Mutex::new(Vec::new());

/// Return a snapshot of all registered (model_name, field_name) pairs.
///
/// Used by the GraphQL middleware to resolve the AAD pair for an encrypted
/// column without requiring a descriptor on the model class.
#[pyfunction]
fn get_encrypted_field_registry() -> Vec<(String, String)> {
    ENCRYPTED_FIELD_REGISTRY
        .lock()
        .expect("encrypted field registry lock poisoned")
        .clone()
}

// ---------------------------------------------------------------------------
// KeyRing — versioned keyring exposed to Python
// ---------------------------------------------------------------------------

/// A versioned keyring for AES-256-GCM field encryption.
///
/// Maps key version numbers (`u16`, starting at 1) to 32-byte AES-256-GCM keys.
/// The active key (used for all new writes) is the highest version number in
/// the ring.
///
/// # Usage
///
/// ```python
/// ring = KeyRing()
/// ring.add(1, key_bytes)  # version 1 key
/// ring.add(2, new_key_bytes)  # version 2 becomes the active key
///
/// ct = encrypt_field("secret", ring, "User", "email")
/// pt = decrypt_field(ct, ring, "User", "email")
/// ```
///
/// # Key rotation
///
/// To rotate keys:
/// 1. Add the new key as a higher version number.
/// 2. New writes use the new key automatically (it is now the active version).
/// 3. Old rows are still readable as long as their version key is in the ring.
/// 4. Run `reencrypt_to_active` in a background task to migrate old rows.
/// 5. Once all rows are migrated, remove the old version.
#[pyclass(name = "KeyRing")]
pub struct PyKeyRing {
    pub(crate) inner: KeyRing,
}

#[pymethods]
impl PyKeyRing {
    /// Create a new, empty keyring.
    #[new]
    fn new() -> Self {
        Self {
            inner: KeyRing::new(),
        }
    }

    /// Add a key for `version` to the ring.
    ///
    /// `version` must be >= 1 (version 0 is reserved).
    /// `key` must be exactly 32 bytes (AES-256).
    /// Each version may only be added once.
    ///
    /// Raises `ValueError` if any constraint is violated.
    fn add(&mut self, version: u16, key: &[u8]) -> PyResult<()> {
        self.inner
            .add(KeyVersion(version), key)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Return `True` if the ring contains no keys.
    fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    /// Return the number of keys in the ring.
    fn __len__(&self) -> usize {
        self.inner.len()
    }
}

// ---------------------------------------------------------------------------
// PyO3 functions
// ---------------------------------------------------------------------------

/// Encrypt `plaintext` using the active key from `ring`.
///
/// Returns a base64-encoded versioned ciphertext:
/// `base64( version(2) || nonce(12) || ciphertext || tag(16) )`.
///
/// The `model` and `field` strings are encoded into the AAD so that a
/// ciphertext cannot be accepted by a different model/field pair.
#[pyfunction]
fn encrypt_field(
    plaintext: &str,
    ring: PyRef<'_, PyKeyRing>,
    model: &str,
    field: &str,
) -> PyResult<String> {
    encrypt_versioned(plaintext, &ring.inner, model, field).map_err(crypto_err_to_py)
}

/// Decrypt a versioned ciphertext produced by [`encrypt_field`].
///
/// Strips the 2-byte version prefix, resolves the key from `ring`, and
/// delegates to AES-256-GCM decryption.
///
/// Raises `DecryptionError` on tag failure, unknown version, or invalid base64.
#[pyfunction]
fn decrypt_field(
    ciphertext: &str,
    ring: PyRef<'_, PyKeyRing>,
    model: &str,
    field: &str,
) -> PyResult<String> {
    let result =
        decrypt_versioned(ciphertext, &ring.inner, model, field).map_err(crypto_err_to_py)?;
    // Wrap in Zeroizing so the Rust heap allocation is overwritten on drop.
    let zeroised = Zeroizing::new(result);
    Ok(zeroised.to_string())
}

#[pyfunction]
fn hash_password(password: &str) -> PyResult<String> {
    syntek_crypto::hash_password(password).map_err(crypto_err_to_py)
}

#[pyfunction]
fn verify_password(password: &str, hash: &str) -> PyResult<bool> {
    syntek_crypto::verify_password(password, hash).map_err(crypto_err_to_py)
}

/// Encrypt a batch of `(field_name, plaintext)` pairs using the active key from `ring`.
///
/// Each field gets its own random nonce and field-specific AAD. Results are in
/// the same order as the input. The entire batch fails atomically on any error.
#[pyfunction]
fn encrypt_fields_batch(
    fields: Vec<(String, String)>,
    ring: PyRef<'_, PyKeyRing>,
    model: &str,
) -> PyResult<Vec<String>> {
    let borrowed: Vec<(&str, &str)> = fields
        .iter()
        .map(|(f, v)| (f.as_str(), v.as_str()))
        .collect();
    encrypt_fields_batch_versioned(&borrowed, &ring.inner, model).map_err(crypto_err_to_py)
}

/// Decrypt a batch of `(field_name, ciphertext)` pairs using keys from `ring`.
///
/// Intermediate plaintext strings are wrapped in `Zeroizing` before being
/// returned to Python. The entire batch fails atomically on any error.
#[pyfunction]
fn decrypt_fields_batch(
    fields: Vec<(String, String)>,
    ring: PyRef<'_, PyKeyRing>,
    model: &str,
) -> PyResult<Vec<String>> {
    let borrowed: Vec<(&str, &str)> = fields
        .iter()
        .map(|(f, v)| (f.as_str(), v.as_str()))
        .collect();

    let results =
        decrypt_fields_batch_versioned(&borrowed, &ring.inner, model).map_err(crypto_err_to_py)?;

    let output: Vec<String> = results
        .into_iter()
        .map(|s| {
            let z = Zeroizing::new(s);
            z.to_string()
        })
        .collect();

    Ok(output)
}

// ---------------------------------------------------------------------------
// EncryptedFieldDescriptor — metadata carrier, NOT a class-replacing descriptor
// ---------------------------------------------------------------------------

/// Metadata carrier storing the model and field names for an encrypted column.
///
/// Exposed to Python so that the GraphQL middleware can look up the AAD pair
/// for a given model/field combination.  This is a frozen (immutable) data
/// class — `model_name` and `field_name` are read-only.
///
/// **Important:** This class is NOT installed on the Django model class in
/// place of the `EncryptedField`.  It is stored in a module-level registry
/// accessible via `get_encrypted_field_registry()`.
#[pyclass(frozen)]
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

/// A Django model field that stores versioned ciphertext only.
///
/// Responsibilities:
/// - Accept versioned ciphertext (valid base64ct, version >= 1, decoded >= 30
///   bytes) on `pre_save`.
/// - Reject plaintext and unversioned ciphertexts with `ValidationError`.
/// - Return raw ciphertext from `from_db_value` — no decryption.
/// - Register the field's model/field name pair in the encrypted field registry
///   via `contribute_to_class`.
///
/// # Constructor
///
/// Accepts `**kwargs` to forward Django field arguments (`null`, `blank`,
/// `max_length`, `db_column`, etc.).
///
/// # `from_db_value` passthrough
///
/// `from_db_value` returns the raw database value unchanged.  Decryption is
/// the GraphQL middleware's responsibility.  If a database row contains a
/// non-ciphertext value (e.g. written by a direct `UPDATE` bypassing the ORM,
/// or from a pre-encryption migration), `from_db_value` will return it as-is.
/// The GraphQL middleware MUST handle `DecryptionError` for such values.
#[pyclass]
pub struct EncryptedField {
    #[pyo3(get, set)]
    pub attname: String,

    /// Whether this field accepts NULL values (maps to Django's `null=True`).
    #[pyo3(get)]
    pub null: bool,

    /// Whether this field accepts blank values (maps to Django's `blank=True`).
    #[pyo3(get)]
    pub blank: bool,

    /// Django field keyword arguments forwarded from the constructor.
    #[pyo3(get)]
    pub field_kwargs: Py<pyo3::types::PyDict>,
}

#[pymethods]
impl EncryptedField {
    #[new]
    #[pyo3(signature = (**kwargs))]
    fn new(py: Python<'_>, kwargs: Option<&Bound<'_, pyo3::types::PyDict>>) -> PyResult<Self> {
        let null = kwargs
            .and_then(|kw| kw.get_item("null").ok().flatten())
            .and_then(|v| v.extract::<bool>().ok())
            .unwrap_or(false);

        let blank = kwargs
            .and_then(|kw| kw.get_item("blank").ok().flatten())
            .and_then(|v| v.extract::<bool>().ok())
            .unwrap_or(false);

        let field_kwargs = match kwargs {
            Some(kw) => kw.copy()?.into(),
            None => pyo3::types::PyDict::new(py).into(),
        };

        Ok(Self {
            attname: String::new(),
            null,
            blank,
            field_kwargs,
        })
    }

    /// Raise Django's `ValidationError` if `value` is not a valid versioned ciphertext.
    ///
    /// Accepts: base64ct-encoded data, decoded length >= 30 bytes, version >= 1.
    /// Rejects: plaintext, unversioned ciphertexts (version 0), too-short blobs.
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
        let msg = "Value is not a valid versioned ciphertext. \
                   Expected base64ct-encoded data with at least 30 decoded bytes \
                   and a non-zero version prefix (version 0 is reserved).";
        let exc = ve_cls.call1((msg,))?;
        Err(PyErr::from_value(exc.into_any()))
    }

    /// Passthrough — returns the raw ciphertext from the database unchanged.
    ///
    /// Decryption is the GraphQL middleware's responsibility.
    ///
    /// **Note:** This method may return non-ciphertext values for rows written
    /// outside the ORM (e.g. direct SQL `UPDATE` or pre-encryption migration
    /// data).  The GraphQL middleware MUST handle `DecryptionError` for such
    /// values gracefully.
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

    /// Validate then return the field value unchanged; raise `ValidationError`
    /// for plaintext.
    ///
    /// If the field is nullable (`null=True`) and the value is `None`, returns
    /// `None` directly without validation.  If the field is non-nullable and
    /// the value is `None`, raises `ValidationError`.
    fn pre_save(
        &self,
        py: Python<'_>,
        instance: Bound<'_, PyAny>,
        add: bool,
    ) -> PyResult<Py<PyAny>> {
        let _ = add;
        let raw = instance.getattr(self.attname.as_str())?;

        if raw.is_none() {
            if self.null {
                return Ok(py.None());
            }
            let exc_module = PyModule::import(py, "django.core.exceptions")?;
            let ve_cls = exc_module.getattr("ValidationError")?;
            let msg = format!(
                "Field '{}' does not allow NULL values. \
                 Provide a valid ciphertext or mark the field as null=True.",
                self.attname
            );
            let exc = ve_cls.call1((msg,))?;
            return Err(PyErr::from_value(exc.into_any()));
        }

        let value: String = raw.extract()?;
        self.validate(py, &value, None)?;
        Ok(pyo3::types::PyString::new(py, &value).into_any().unbind())
    }

    /// Register the field's model/field name pair in the encrypted field
    /// registry.
    ///
    /// Sets `field.attname = name` and adds the `(model_name, field_name)`
    /// pair to the module-level registry.
    ///
    /// **Important:** This method does NOT overwrite the field entry on the
    /// Django model class.  The `EncryptedField` object remains on the class
    /// so that Django's `_meta` field registration, migrations, and ORM
    /// introspection continue to work correctly.
    fn contribute_to_class(
        &mut self,
        _py: Python<'_>,
        cls: Bound<'_, PyAny>,
        name: &str,
    ) -> PyResult<()> {
        self.attname = name.to_owned();
        let model_name: String = cls.getattr("__name__")?.extract()?;

        ENCRYPTED_FIELD_REGISTRY
            .lock()
            .expect("encrypted field registry lock poisoned")
            .push((model_name, name.to_owned()));

        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Module entry point
// ---------------------------------------------------------------------------

#[pymodule]
fn syntek_pyo3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Functions
    m.add_function(wrap_pyfunction!(encrypt_field, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_field, m)?)?;
    m.add_function(wrap_pyfunction!(hash_password, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_fields_batch, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_fields_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_encrypted_field_registry, m)?)?;

    // Classes
    m.add_class::<PyKeyRing>()?;
    m.add_class::<EncryptedField>()?;
    m.add_class::<EncryptedFieldDescriptor>()?;

    // Exception classes — importable as syntek_pyo3.DecryptionError, etc.
    m.add("DecryptionError", m.py().get_type::<PyDecryptionError>())?;
    m.add(
        "BatchDecryptionError",
        m.py().get_type::<PyBatchDecryptionError>(),
    )?;

    Ok(())
}
