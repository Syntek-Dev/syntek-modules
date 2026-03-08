//! `syntek.manifest.toml` data structures.
//!
//! The schema is:
//!
//! ```toml
//! id            = "syntek-auth"             # required
//! version       = "1.0.0"                   # required
//! kind          = "backend"                 # required — rust-crate | backend | frontend | mobile
//!
//! [[options]]
//! key     = "MFA_REQUIRED"
//! label   = "Require MFA for all users?"
//! kind    = "bool"
//! default = "true"
//!
//! [[settings]]
//! key     = "MFA_REQUIRED"
//! kind    = "bool"
//! default = "true"
//!
//! installed_apps = ["syntek_auth"]          # backend only
//!
//! [[providers]]
//! name    = "AuthProvider"
//! import  = "@syntek/ui-auth"               # frontend / mobile only
//!
//! entry_point = "app/layout.tsx"            # frontend / mobile only
//!
//! [[post_install_steps]]
//! label   = "Add URL patterns"
//! snippet = "path('auth/', include('syntek_auth.urls')),"
//! lang    = "python"
//! ```

use serde::{Deserialize, Serialize};

/// The kind of module this manifest describes.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ModuleKind {
    RustCrate,
    Backend,
    Frontend,
    Mobile,
}

/// An interactive install option.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ManifestOption {
    /// The settings key this option maps to (e.g. `MFA_REQUIRED`).
    pub key: String,
    /// Human-readable label shown in the interactive prompt.
    pub label: String,
    /// Type hint: `bool`, `str`, `int`, `list`.
    pub kind: String,
    /// Default value rendered in the prompt.
    pub default: Option<String>,
}

/// A settings key that will be written to `settings.py`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ManifestSetting {
    pub key: String,
    pub kind: String,
    pub default: Option<String>,
}

/// A React/React-Native provider that must wrap the entry point.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ManifestProvider {
    pub name: String,
    pub import: String,
}

/// A post-install step rendered as a formatted copy-paste snippet.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PostInstallStep {
    pub label: String,
    pub snippet: String,
    /// Language identifier used for syntax highlighting (e.g. `python`, `typescript`).
    pub lang: String,
}

/// The fully-parsed and validated manifest.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Manifest {
    pub id: String,
    pub version: String,
    pub kind: ModuleKind,
    #[serde(default)]
    pub options: Vec<ManifestOption>,
    #[serde(default)]
    pub settings: Vec<ManifestSetting>,
    #[serde(default)]
    pub installed_apps: Vec<String>,
    #[serde(default)]
    pub providers: Vec<ManifestProvider>,
    pub entry_point: Option<String>,
    #[serde(default)]
    pub post_install_steps: Vec<PostInstallStep>,
}
