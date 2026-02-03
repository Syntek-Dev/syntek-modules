//! Environment file loading utilities
//!
//! This module handles loading environment variables from .env files
//! for different deployment environments (dev, test, staging, production).

use colored::*;
use std::path::PathBuf;

/// Load environment variables from a file
///
/// # Arguments
///
/// * `env_file` - Path to .env file (e.g., .env.dev, .env.production)
///
/// # Returns
///
/// * `Ok(())` if file loaded successfully or doesn't exist
/// * `Err` if file exists but cannot be parsed
///
/// # Notes
///
/// If the file doesn't exist, prints a warning but continues execution.
pub fn load_env(env_file: &PathBuf) -> anyhow::Result<()> {
    if env_file.exists() {
        dotenvy::from_path(env_file)?;
        println!(
            "{} {}",
            "📝 Loaded environment:".dimmed(),
            env_file.display().to_string().cyan()
        );
    } else {
        println!(
            "{} {}",
            "⚠️  Environment file not found:".yellow(),
            env_file.display()
        );
        println!("{}", "   Continuing without environment file...".dimmed());
    }
    Ok(())
}
