//! Install command implementation
//!
//! Handles `syntek install auth` command with various flags.

use crate::config::auth_config::InstallMode;
use crate::install::{AuthInstallOptions, AuthInstaller};
use crate::utils::error::Result;
use clap::Args;
use std::path::Path;

/// Install command arguments
#[derive(Debug, Args)]
pub struct InstallArgs {
    /// Module to install (currently only "auth" supported)
    pub module: String,

    /// Full installation (backend + web + mobile + GraphQL + Rust)
    #[arg(long, conflicts_with_all = &["minimal", "web_only", "mobile_only"])]
    pub full: bool,

    /// Minimal installation (backend + GraphQL only)
    #[arg(long, conflicts_with_all = &["full", "web_only", "mobile_only"])]
    pub minimal: bool,

    /// Web-only installation (backend + GraphQL + web)
    #[arg(long, conflicts_with_all = &["full", "minimal", "mobile_only"])]
    pub web_only: bool,

    /// Mobile-only installation (backend + GraphQL + mobile)
    #[arg(long, conflicts_with_all = &["full", "minimal", "web_only"])]
    pub mobile_only: bool,

    /// Enable social authentication
    #[arg(long)]
    pub social_auth: bool,

    /// Social authentication providers (comma-separated: google,github,microsoft,apple,facebook,linkedin,twitter)
    #[arg(long, value_delimiter = ',')]
    pub providers: Vec<String>,

    /// Skip Rust crate installation
    #[arg(long)]
    pub skip_rust: bool,

    /// Skip frontend installation
    #[arg(long)]
    pub skip_frontend: bool,

    /// Path to syntek-modules repository (for copying shared modules and Rust crates)
    #[arg(long, env = "SYNTEK_MODULES_PATH")]
    pub syntek_modules_path: Option<String>,

    /// Target project directory
    #[arg(long, default_value = ".")]
    pub project_dir: String,
}

/// Execute install command
pub fn execute(args: InstallArgs) -> Result<()> {
    // Validate module name
    if args.module != "auth" {
        return Err(crate::utils::error::CliError::ValidationFailed(
            format!("Unknown module: {}. Currently only 'auth' is supported.", args.module),
        ));
    }

    // Determine installation mode
    let mode = if args.minimal {
        InstallMode::Minimal
    } else if args.web_only {
        InstallMode::WebOnly
    } else if args.mobile_only {
        InstallMode::MobileOnly
    } else {
        InstallMode::Full // Default to full
    };

    // Validate providers if social auth is enabled
    let providers = if args.social_auth || !args.providers.is_empty() {
        if args.providers.is_empty() {
            println!(
                "{}",
                "Warning: --social-auth enabled but no providers specified. Use --providers to specify."
                    .to_string()
            );
            Vec::new()
        } else {
            validate_providers(&args.providers)?;
            args.providers.clone()
        }
    } else {
        Vec::new()
    };

    // Create installation options
    let options = AuthInstallOptions {
        mode,
        enable_social_auth: args.social_auth || !providers.is_empty(),
        social_providers: providers,
        skip_rust: args.skip_rust,
        skip_frontend: args.skip_frontend,
        syntek_modules_path: args.syntek_modules_path,
    };

    // Execute installation
    let project_dir = Path::new(&args.project_dir);
    AuthInstaller::install(project_dir, options)?;

    Ok(())
}

/// Validate social auth providers
fn validate_providers(providers: &[String]) -> Result<()> {
    let valid_providers = vec![
        "google", "github", "microsoft", "apple", "facebook", "linkedin", "twitter", "x",
    ];

    for provider in providers {
        let normalized = provider.to_lowercase();
        if !valid_providers.contains(&normalized.as_str()) {
            return Err(crate::utils::error::CliError::ValidationFailed(format!(
                "Invalid provider: {}. Valid providers: {}",
                provider,
                valid_providers.join(", ")
            )));
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_providers() {
        assert!(validate_providers(&["google".to_string(), "github".to_string()]).is_ok());
        assert!(validate_providers(&["invalid".to_string()]).is_err());
    }

    #[test]
    fn test_install_mode_selection() {
        let args = InstallArgs {
            module: "auth".to_string(),
            full: false,
            minimal: true,
            web_only: false,
            mobile_only: false,
            social_auth: false,
            providers: Vec::new(),
            skip_rust: false,
            skip_frontend: false,
            syntek_modules_path: None,
            project_dir: ".".to_string(),
        };

        let mode = if args.minimal {
            InstallMode::Minimal
        } else {
            InstallMode::Full
        };

        assert!(matches!(mode, InstallMode::Minimal));
    }
}
