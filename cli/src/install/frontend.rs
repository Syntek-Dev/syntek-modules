//! Frontend installation module (Web and Mobile)
//!
//! Installs React/Next.js/React Native packages via npm/pnpm.

use crate::config::loader::ProjectConfig;
use crate::utils::error::{CliError, Result};
use crate::utils::exec;
use colored::Colorize;
use indicatif::{ProgressBar, ProgressStyle};
use std::path::Path;

/// Frontend installer
pub struct FrontendInstaller;

impl FrontendInstaller {
    /// Install web authentication packages
    pub fn install_web_auth(project_dir: &Path, config: &ProjectConfig) -> Result<Vec<String>> {
        if config.web.directory.is_empty() {
            println!("{}", "Skipping web installation (not configured)".yellow());
            return Ok(Vec::new());
        }

        let web_dir = project_dir.join(&config.web.directory);
        if !web_dir.exists() {
            return Err(CliError::InvalidPath(web_dir));
        }

        println!("{}", "\nInstalling web authentication packages...".bold());

        let mut installed = Vec::new();

        // Web packages
        let packages = vec!["@syntek/security-core", "@syntek/security-auth", "@syntek/ui-auth"];

        for package in &packages {
            Self::install_package(&web_dir, package, &config.web.package_manager)?;
            installed.push(package.to_string());
        }

        Ok(installed)
    }

    /// Install mobile authentication packages
    pub fn install_mobile_auth(project_dir: &Path, config: &ProjectConfig) -> Result<Vec<String>> {
        if config.mobile.directory.is_empty() {
            println!(
                "{}",
                "Skipping mobile installation (not configured)".yellow()
            );
            return Ok(Vec::new());
        }

        let mobile_dir = project_dir.join(&config.mobile.directory);
        if !mobile_dir.exists() {
            return Err(CliError::InvalidPath(mobile_dir));
        }

        println!("{}", "\nInstalling mobile authentication packages...".bold());

        let mut installed = Vec::new();

        // Mobile packages
        let packages = vec!["@syntek/security-core", "@syntek/mobile-auth"];

        for package in &packages {
            Self::install_package(&mobile_dir, package, &config.mobile.package_manager)?;
            installed.push(package.to_string());
        }

        Ok(installed)
    }

    /// Install shared packages
    pub fn install_shared(project_dir: &Path, config: &ProjectConfig) -> Result<Vec<String>> {
        if !config.shared.enabled {
            println!("{}", "Skipping shared installation (not enabled)".yellow());
            return Ok(Vec::new());
        }

        let shared_dir = project_dir.join(&config.shared.directory);
        if !shared_dir.exists() {
            std::fs::create_dir_all(&shared_dir)?;
        }

        println!("{}", "\nInstalling shared authentication modules...".bold());

        // Shared auth structure is typically copied from syntek-modules
        // Not installed via package manager
        println!(
            "{}",
            "Shared modules will be copied from syntek-modules repository".cyan()
        );

        Ok(vec!["shared/auth".to_string()])
    }

    /// Install single npm/pnpm package
    fn install_package(package_dir: &Path, package: &str, package_manager: &str) -> Result<()> {
        let spinner = ProgressBar::new_spinner();
        spinner.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner:.green} {msg}")
                .unwrap(),
        );
        spinner.set_message(format!("Installing {}...", package.cyan()));
        spinner.enable_steady_tick(std::time::Duration::from_millis(100));

        let result = match package_manager {
            "pnpm" => exec::run_command("pnpm", &["add", package], Some(package_dir)),
            "npm" => exec::run_command("npm", &["install", package], Some(package_dir)),
            "yarn" => exec::run_command("yarn", &["add", package], Some(package_dir)),
            _ => {
                return Err(CliError::InvalidConfig(format!(
                    "Unsupported package manager: {}",
                    package_manager
                )))
            }
        };

        spinner.finish_and_clear();

        if result.is_ok() {
            println!("{} {}", "✓".green().bold(), package.cyan());
        } else {
            println!("{} {} (failed)", "✗".red().bold(), package.cyan());
        }

        result.map(|_| ())
    }

    /// Verify web installation
    pub fn verify_web_installation(
        project_dir: &Path,
        config: &ProjectConfig,
        packages: &[String],
    ) -> Result<()> {
        if packages.is_empty() {
            return Ok(());
        }

        println!("{}", "\nVerifying web installation...".bold());

        let web_dir = project_dir.join(&config.web.directory);
        let package_json = web_dir.join("package.json");

        if !package_json.exists() {
            return Err(CliError::ValidationFailed(
                "package.json not found in web directory".to_string(),
            ));
        }

        let content = std::fs::read_to_string(&package_json)?;

        for package in packages {
            if content.contains(package) {
                println!("{} {} listed in package.json", "✓".green().bold(), package.cyan());
            } else {
                println!(
                    "{} {} not found in package.json",
                    "✗".red().bold(),
                    package.cyan()
                );
                return Err(CliError::SmokeTestFailed(format!(
                    "Package {} not installed",
                    package
                )));
            }
        }

        Ok(())
    }

    /// Verify mobile installation
    pub fn verify_mobile_installation(
        project_dir: &Path,
        config: &ProjectConfig,
        packages: &[String],
    ) -> Result<()> {
        if packages.is_empty() {
            return Ok(());
        }

        println!("{}", "\nVerifying mobile installation...".bold());

        let mobile_dir = project_dir.join(&config.mobile.directory);
        let package_json = mobile_dir.join("package.json");

        if !package_json.exists() {
            return Err(CliError::ValidationFailed(
                "package.json not found in mobile directory".to_string(),
            ));
        }

        let content = std::fs::read_to_string(&package_json)?;

        for package in packages {
            if content.contains(package) {
                println!("{} {} listed in package.json", "✓".green().bold(), package.cyan());
            } else {
                println!(
                    "{} {} not found in package.json",
                    "✗".red().bold(),
                    package.cyan()
                );
                return Err(CliError::SmokeTestFailed(format!(
                    "Package {} not installed",
                    package
                )));
            }
        }

        Ok(())
    }

    /// Copy shared modules from syntek-modules repository
    pub fn copy_shared_modules(
        syntek_modules_path: &Path,
        project_dir: &Path,
        config: &ProjectConfig,
    ) -> Result<()> {
        let source = syntek_modules_path.join("shared").join("auth");
        let target = project_dir.join(&config.shared.directory).join("auth");

        if !source.exists() {
            return Err(CliError::PackageNotFound("shared/auth".to_string()));
        }

        println!(
            "{}",
            "\nCopying shared authentication modules...".bold()
        );

        crate::utils::fs::copy_dir_recursive(&source, &target)?;

        println!(
            "{} Shared modules copied to {}",
            "✓".green().bold(),
            target.display()
        );

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::loader::ConfigLoader;
    use tempfile::TempDir;

    #[test]
    fn test_frontend_installer_structure() {
        let temp_dir = TempDir::new().unwrap();
        let config = ConfigLoader::create_default("test-project");

        // Create directories
        let web_dir = temp_dir.path().join(&config.web.directory);
        std::fs::create_dir_all(&web_dir).unwrap();

        assert!(web_dir.exists());
    }
}
