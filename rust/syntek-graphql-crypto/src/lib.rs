//! syntek-graphql-crypto — GraphQL middleware preventing plaintext resolver output
//!
//! Intercepts Strawberry GraphQL resolver output and ensures no sensitive field
//! is returned as plaintext. All encrypted values pass through syntek-crypto
//! before being serialised into the GraphQL response.
//!
//! # Types
//!
//! - [`EncryptedFieldSpec`] — describes a single field annotated with `@encrypted`
//!   or `@encrypted(batch: "group_name")` in the GraphQL schema.
//! - [`MiddlewareError`] — structured error type returned by the middleware on
//!   encrypt/decrypt failures, key resolution failures, or unauthenticated access.

use serde::{Deserialize, Serialize};
use thiserror::Error;

// ---------------------------------------------------------------------------
// EncryptedFieldSpec
// ---------------------------------------------------------------------------

/// Describes a single field that carries the `@encrypted` or
/// `@encrypted(batch: "group_name")` directive in the GraphQL schema.
///
/// The middleware uses a list of these specs at startup to determine which
/// fields need crypto treatment on reads and writes.
///
/// # Batch grouping
///
/// - `batch_group == None`  → individual field; encrypted/decrypted with a
///   single `encrypt_field` / `decrypt_field` call.
/// - `batch_group == Some(name)` → all specs on the same model sharing the
///   same `name` are processed together in one `encrypt_fields_batch` /
///   `decrypt_fields_batch` call.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EncryptedFieldSpec {
    /// Name of the GraphQL / model field (e.g. `"email"`, `"first_name"`).
    pub field_name: String,

    /// Django model name that owns this field (e.g. `"User"`).
    /// Used to resolve the correct `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>` env var.
    pub model_name: String,

    /// Batch group name when the field is annotated with
    /// `@encrypted(batch: "group_name")`, or `None` for individual fields.
    pub batch_group: Option<String>,
}

// ---------------------------------------------------------------------------
// MiddlewareError
// ---------------------------------------------------------------------------

/// Structured errors produced by the GraphQL crypto middleware.
///
/// All variants implement [`std::error::Error`] via `thiserror` so they can
/// be boxed, propagated with `?`, and converted into structured GraphQL error
/// payloads.
#[derive(Debug, Error)]
pub enum MiddlewareError {
    /// Encryption of `field` failed (e.g. invalid key, Rust crypto error).
    ///
    /// On this error the middleware rejects the entire mutation — no partial
    /// ciphertext is written to the ORM.
    #[error("encryption failed for field '{field}'")]
    EncryptFailed {
        /// Name of the field that could not be encrypted.
        field: String,
    },

    /// Decryption of `field` failed (e.g. tampered ciphertext, wrong key).
    ///
    /// For individual fields: that field is nulled and an error is appended
    /// to the GraphQL `errors` array; the rest of the response is intact.
    ///
    /// For batch groups: all fields in the group are nulled and a single
    /// error is appended.
    #[error("decryption failed for field '{field}'")]
    DecryptFailed {
        /// Name of the field that could not be decrypted.
        field: String,
    },

    /// The `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>` environment variable for
    /// `model`/`field` is missing or empty at request time.
    #[error("key resolution failed for model '{model}', field '{field}'")]
    KeyResolutionFailed {
        /// Django model name (e.g. `"User"`).
        model: String,
        /// Field name (e.g. `"phone"`).
        field: String,
    },

    /// An unauthenticated request attempted to resolve an `@encrypted` field.
    ///
    /// All encrypted fields in the response are set to `null` and this error
    /// is appended to the GraphQL `errors` array.  The request is not aborted.
    #[error("unauthenticated access to encrypted field")]
    UnauthenticatedAccess,
}
