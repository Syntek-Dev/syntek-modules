//! syntek-manifest — shared manifest parser and installer framework
//!
//! Every Syntek module's installer binary links against this crate. It provides:
//!
//! - [`ManifestParser`] — parses and validates `syntek.manifest.toml`
//! - [`OptionPrompter`] — renders interactive prompts for each declared option
//! - [`SettingsWriter`] — writes typed `SYNTEK_<MODULE>` blocks to `settings.py`
//! - [`InstalledAppsWriter`] — appends entries to `INSTALLED_APPS` without duplicating
//! - [`ProviderWrapper`] — wraps a frontend entry point with declared providers
//! - [`PostInstallPrinter`] — formats post-install steps as copy-paste snippets
//! - [`DuplicateDetector`] — detects existing `SYNTEK_<MODULE>` blocks before writing

pub mod duplicate_detector;
pub mod error;
pub mod manifest;
pub mod parser;
pub mod post_install;
pub mod prompter;
pub mod provider_wrapper;
pub mod settings_writer;
