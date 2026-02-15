//! Authentication module installer
//!
//! Main installer orchestrating backend, frontend, GraphQL, and Rust installation.

use crate::config::auth_config::{AuthConfig, AuthConfigGenerator, InstallMode};
use crate::config::generator::ConfigGenerator;
use crate::config::loader::{ConfigLoader, ProjectConfig};
use crate::install::{
    backend::BackendInstaller, frontend::FrontendInstaller, graphql::GraphQLInstaller,
    rust::RustInstaller,
};
use crate::security::SecretsManager;
use crate::utils::error::Result;
use colored::Colorize;
use std::path::Path;

/// Authentication installer options
pub struct AuthInstallOptions {
    pub mode: InstallMode,
    pub enable_social_auth: bool,
    pub social_providers: Vec<String>,
    pub skip_rust: bool,
    pub skip_frontend: bool,
    pub syntek_modules_path: Option<String>,
}

impl Default for AuthInstallOptions {
    fn default() -> Self {
        Self {
            mode: InstallMode::Full,
            enable_social_auth: false,
            social_providers: Vec::new(),
            skip_rust: false,
            skip_frontend: false,
            syntek_modules_path: None,
        }
    }
}

/// Authentication installer
pub struct AuthInstaller;

impl AuthInstaller {
    /// Install authentication system
    pub fn install(project_dir: &Path, options: AuthInstallOptions) -> Result<()> {
        println!("{}", "=== Syntek Authentication Installer ===\n".bold().cyan());

        // Load or create project configuration
        let mut config = Self::load_or_create_config(project_dir)?;

        // Generate authentication configuration
        let mut secrets = SecretsManager::new();
        let mut auth_config = AuthConfigGenerator::generate(options.mode, &mut secrets)?;

        // Add social providers if requested
        if options.enable_social_auth {
            Self::add_social_providers(&mut auth_config, &options.social_providers, &mut secrets)?;
        }

        // Generate configuration files
        println!("{}", "Generating configuration files...".bold());
        ConfigGenerator::generate_auth_config(project_dir, &auth_config)?;
        println!("{} Configuration files generated\n", "✓".green().bold());

        // Install backend modules
        let backend_modules = BackendInstaller::install_auth(
            project_dir,
            &config,
            matches!(options.mode, InstallMode::Minimal),
        )?;
        Self::update_installed_modules(&mut config, "backend", &backend_modules)?;

        // Install GraphQL modules
        let graphql_modules = GraphQLInstaller::install_auth(project_dir, &config)?;
        Self::update_installed_modules(&mut config, "graphql", &graphql_modules)?;

        // Generate GraphQL schema
        GraphQLInstaller::generate_schema_boilerplate(project_dir)?;
        GraphQLInstaller::generate_url_config(project_dir)?;

        // Install frontend (unless skipped or minimal mode)
        if !options.skip_frontend && !matches!(options.mode, InstallMode::Minimal) {
            match options.mode {
                InstallMode::WebOnly | InstallMode::Full => {
                    let web_packages = FrontendInstaller::install_web_auth(project_dir, &config)?;
                    Self::update_installed_modules(&mut config, "web", &web_packages)?;
                }
                InstallMode::MobileOnly => {
                    let mobile_packages =
                        FrontendInstaller::install_mobile_auth(project_dir, &config)?;
                    Self::update_installed_modules(&mut config, "mobile", &mobile_packages)?;
                }
                _ => {
                    let web_packages = FrontendInstaller::install_web_auth(project_dir, &config)?;
                    let mobile_packages =
                        FrontendInstaller::install_mobile_auth(project_dir, &config)?;
                    Self::update_installed_modules(&mut config, "web", &web_packages)?;
                    Self::update_installed_modules(&mut config, "mobile", &mobile_packages)?;
                }
            }

            // Install shared modules
            if config.shared.enabled {
                let shared_modules = FrontendInstaller::install_shared(project_dir, &config)?;
                Self::update_installed_modules(&mut config, "shared", &shared_modules)?;

                // Copy shared modules from syntek-modules if path provided
                if let Some(ref syntek_path) = options.syntek_modules_path {
                    let syntek_modules_path = Path::new(syntek_path);
                    FrontendInstaller::copy_shared_modules(
                        syntek_modules_path,
                        project_dir,
                        &config,
                    )?;
                }
            }
        }

        // Install Rust crates (unless skipped)
        if !options.skip_rust {
            if let Some(ref syntek_path) = options.syntek_modules_path {
                let syntek_modules_path = Path::new(syntek_path);
                let rust_crates =
                    RustInstaller::install_auth(syntek_modules_path, project_dir, &config)?;
                Self::update_installed_modules(&mut config, "rust", &rust_crates)?;

                // Show PyO3 integration instructions
                RustInstaller::generate_pyo3_instructions()?;
            } else {
                println!(
                    "{}",
                    "Skipping Rust installation (syntek-modules path not provided)".yellow()
                );
            }
        }

        // Save updated configuration
        ConfigLoader::save_to_project(project_dir, &config)?;

        // Print summary
        Self::print_installation_summary(project_dir, &config, &auth_config)?;

        println!("\n{}", "Installation complete!".bold().green());
        println!(
            "\nNext steps:\n  1. Review configuration in {}\n  2. Update .env with your secrets\n  3. Run: syntek verify auth",
            "config/auth/README.md".cyan()
        );

        Ok(())
    }

    /// Load or create project configuration
    fn load_or_create_config(project_dir: &Path) -> Result<ProjectConfig> {
        match ConfigLoader::load_from_project(project_dir) {
            Ok(config) => {
                println!("{} Loaded existing configuration\n", "✓".green().bold());
                Ok(config)
            }
            Err(_) => {
                println!("{}", "Creating new configuration...\n".yellow());
                let project_name = project_dir
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("my-project");
                Ok(ConfigLoader::create_default(project_name))
            }
        }
    }

    /// Add social authentication providers
    fn add_social_providers(
        auth_config: &mut AuthConfig,
        providers: &[String],
        secrets: &mut SecretsManager,
    ) -> Result<()> {
        println!("{}", "\nConfiguring social authentication...".bold());

        for provider in providers {
            AuthConfigGenerator::add_social_provider(auth_config, provider, secrets)?;
            println!("{} Added {} provider", "✓".green().bold(), provider.cyan());
        }

        Ok(())
    }

    /// Update installed modules in configuration
    fn update_installed_modules(
        config: &mut ProjectConfig,
        module_type: &str,
        modules: &[String],
    ) -> Result<()> {
        for module in modules {
            ConfigLoader::add_module(config, module_type, module)?;
        }
        Ok(())
    }

    /// Print installation summary
    fn print_installation_summary(
        project_dir: &Path,
        config: &ProjectConfig,
        auth_config: &AuthConfig,
    ) -> Result<()> {
        println!("\n{}", "=== Installation Summary ===".bold().cyan());

        println!("\n{}", "Backend modules:".bold());
        for module in &config.modules.backend {
            println!("  {} {}", "✓".green(), module.cyan());
        }

        println!("\n{}", "GraphQL modules:".bold());
        for module in &config.modules.graphql {
            println!("  {} {}", "✓".green(), module.cyan());
        }

        if !config.modules.web.is_empty() {
            println!("\n{}", "Web packages:".bold());
            for package in &config.modules.web {
                println!("  {} {}", "✓".green(), package.cyan());
            }
        }

        if !config.modules.mobile.is_empty() {
            println!("\n{}", "Mobile packages:".bold());
            for package in &config.modules.mobile {
                println!("  {} {}", "✓".green(), package.cyan());
            }
        }

        if !config.modules.rust.is_empty() {
            println!("\n{}", "Rust crates:".bold());
            for crate_name in &config.modules.rust {
                println!("  {} {}", "✓".green(), crate_name.cyan());
            }
        }

        println!("\n{}", "Configuration:".bold());
        println!("  Mode: {}", auth_config.mode.cyan());
        println!("  Rate limiting: {}", "✓ Configured".green());
        println!("  Constant-time responses: {}", "✓ Enabled".green());
        println!("  SMS cost prevention: {}", "✓ Enabled".green());
        println!("  GDPR compliance: {}", "✓ Enabled".green());

        if !auth_config.social_providers.is_empty() {
            println!("\n{}", "Social authentication:".bold());
            for provider in &auth_config.social_providers {
                println!("  {} {}", "✓".green(), provider.name.cyan());
            }
        }

        println!("\n{}", "Generated files:".bold());
        let config_dir = project_dir.join("config").join("auth");
        println!("  {} {}", "✓".green(), config_dir.join("settings.toml").display());
        println!("  {} {}", "✓".green(), config_dir.join("README.md").display());
        println!("  {} {}", "✓".green(), project_dir.join(".env.example").display());

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_load_or_create_config() {
        let temp_dir = TempDir::new().unwrap();
        let config = AuthInstaller::load_or_create_config(temp_dir.path()).unwrap();
        assert!(!config.project.name.is_empty());
    }
}
