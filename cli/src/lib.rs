//! Syntek CLI library
//!
//! CLI tool for installing Syntek modules across backend, web, mobile, and Rust layers.

pub mod commands;
pub mod config;
pub mod install;
pub mod security;
pub mod utils;

// Re-export commonly used types
pub use config::{AuthConfig, ConfigLoader, ProjectConfig};
pub use utils::error::{CliError, Result};
