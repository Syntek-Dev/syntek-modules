//! Error types for syntek-manifest.

use thiserror::Error;

/// Errors produced by manifest parsing and installation steps.
///
/// `PartialEq` is intentionally **not** derived on this type.  The `Io`
/// variant stores a `message: String` that comes from `std::io::Error::to_string()`,
/// which is platform-dependent (the OS error description differs between Linux,
/// macOS, and Windows).  Deriving `PartialEq` would invite test authors to write
/// `assert_eq!(err, ManifestError::Io { … })`, which produces fragile assertions
/// that break across platforms.  Use `matches!` with a struct pattern instead:
///
/// ```rust,ignore
/// assert!(matches!(result, Err(ManifestError::Io { .. })));
/// ```
#[derive(Debug, Error)]
pub enum ManifestError {
    /// A required field is missing from the manifest.
    #[error("missing required field: `{field}`")]
    MissingField { field: String },

    /// A field value has the wrong type.
    #[error("field `{field}` has wrong type: expected {expected}")]
    WrongType { field: String, expected: String },

    /// The `kind` value is not one of the recognised variants.
    #[error("unknown module kind `{kind}`: expected rust-crate, backend, frontend, or mobile")]
    UnknownKind { kind: String },

    /// Raw TOML parse failure.
    #[error("toml parse error: {0}")]
    TomlParse(String),

    /// The target file could not be read or written.
    #[error("io error for `{path}`: {message}")]
    Io { path: String, message: String },

    /// A `SYNTEK_<MODULE>` block already exists in the target file.
    #[error("existing block detected for `{key}` in `{path}`")]
    ExistingBlock { key: String, path: String },

    /// A `bool` setting received a value that is not `"true"` or `"false"`.
    #[error("invalid bool value `{value}` for key `{key}`: expected \"true\" or \"false\"")]
    InvalidBoolValue { key: String, value: String },

    /// A provider name is not a valid JSX identifier.
    #[error("invalid provider name `{name}`: must match [A-Za-z][A-Za-z0-9]*")]
    InvalidProviderName { name: String },

    /// The module `id` contains characters that are not ASCII alphanumeric or ASCII hyphens.
    ///
    /// An invalid `id` would produce a syntactically incorrect Python identifier when
    /// converted to a settings key (e.g. `SYNTEK_AUTH`), causing Django to fail at
    /// import time with a `SyntaxError`.
    #[error("invalid module id `{id}`: must match [a-zA-Z0-9-]+")]
    InvalidId { id: String },

    /// An `int` setting received a value that cannot be parsed as a 64-bit integer.
    #[error("invalid int value `{value}` for key `{key}`: must be a valid integer")]
    InvalidIntValue { key: String, value: String },

    /// The `version` field does not conform to basic SemVer (`MAJOR.MINOR.PATCH`).
    #[error("invalid version `{version}`: must match MAJOR.MINOR.PATCH (e.g. 1.0.0)")]
    InvalidVersion { version: String },
}
