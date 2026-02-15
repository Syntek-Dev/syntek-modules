//! Error handling for Syntek CLI
//!
//! Provides comprehensive error types and user-friendly error messages.

use std::path::PathBuf;
use thiserror::Error;

/// Main CLI error type
#[derive(Debug, Error)]
pub enum CliError {
    /// Configuration errors
    #[error("Configuration not found at {0}")]
    ConfigNotFound(PathBuf),

    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),

    #[error("Insecure file permissions: {path:?} has mode {mode:o}, should be {recommended:o}")]
    InsecurePermissions {
        path: PathBuf,
        mode: u32,
        recommended: u32,
    },

    /// Installation errors
    #[error("Installation failed: {0}")]
    InstallationFailed(String),

    #[error("Package {0} not found in syntek-modules repository")]
    PackageNotFound(String),

    #[error("Dependency {0} missing, required by {1}")]
    MissingDependency(String, String),

    #[error("Installation already exists at {0}. Use --force to overwrite")]
    AlreadyInstalled(PathBuf),

    /// Security errors
    #[error("Environment variable {0} not set")]
    MissingEnvVar(String),

    #[error("Secret prompt failed")]
    PromptFailed,

    #[error("Password cannot be empty")]
    EmptyPassword,

    #[error("Password confirmation mismatch")]
    PasswordMismatch,

    #[error("Failed to drop privileges")]
    PrivilegeDropFailed,

    /// File system errors
    #[error("File operation failed: {0}")]
    FileOperation(String),

    #[error("Invalid path: {0}")]
    InvalidPath(PathBuf),

    #[error("Directory not empty: {0}")]
    DirectoryNotEmpty(PathBuf),

    /// User/group errors
    #[error("User not found: {0}")]
    UserNotFound(String),

    #[error("Group not found: {0}")]
    GroupNotFound(String),

    /// Command execution errors
    #[error("Command failed: {0}")]
    CommandFailed(String),

    #[error("Command output error: {0}")]
    CommandOutput(String),

    /// Validation errors
    #[error("Validation failed: {0}")]
    ValidationFailed(String),

    #[error("Smoke test failed: {0}")]
    SmokeTestFailed(String),

    /// I/O errors
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// Serialization errors
    #[error("Serialization error: {0}")]
    Serialization(String),

    /// Generic error
    #[error("{0}")]
    Other(String),
}

impl From<toml::de::Error> for CliError {
    fn from(err: toml::de::Error) -> Self {
        CliError::Serialization(err.to_string())
    }
}

impl From<toml::ser::Error> for CliError {
    fn from(err: toml::ser::Error) -> Self {
        CliError::Serialization(err.to_string())
    }
}

impl From<serde_json::Error> for CliError {
    fn from(err: serde_json::Error) -> Self {
        CliError::Serialization(err.to_string())
    }
}

/// Warning type for non-fatal issues
#[derive(Debug)]
pub enum Warning {
    InsecurePermissions {
        path: PathBuf,
        mode: u32,
        recommended: u32,
    },
    PotentialSecret {
        path: String,
        suggestion: String,
    },
    DeprecatedConfig {
        key: String,
        replacement: Option<String>,
    },
    MissingOptionalDependency {
        name: String,
        feature: String,
    },
}

impl std::fmt::Display for Warning {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Warning::InsecurePermissions {
                path,
                mode,
                recommended,
            } => write!(
                f,
                "⚠️  File {:?} has insecure permissions {:o}, should be {:o}",
                path, mode, recommended
            ),
            Warning::PotentialSecret { path, suggestion } => {
                write!(f, "⚠️  Potential secret in {}: {}", path, suggestion)
            }
            Warning::DeprecatedConfig { key, replacement } => {
                if let Some(new_key) = replacement {
                    write!(f, "⚠️  Config key '{}' is deprecated, use '{}' instead", key, new_key)
                } else {
                    write!(f, "⚠️  Config key '{}' is deprecated", key)
                }
            }
            Warning::MissingOptionalDependency { name, feature } => {
                write!(
                    f,
                    "⚠️  Optional dependency '{}' missing, feature '{}' will be disabled",
                    name, feature
                )
            }
        }
    }
}

/// Result type for CLI operations
pub type Result<T> = std::result::Result<T, CliError>;
