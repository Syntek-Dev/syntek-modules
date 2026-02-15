//! Django backend installation module
//!
//! Installs Django authentication packages via uv/pip.

use crate::config::loader::ProjectConfig;
use crate::utils::error::{CliError, Result};
use crate::utils::exec;
use colored::Colorize;
use indicatif::{ProgressBar, ProgressStyle};
use std::path::Path;

/// Backend installer
pub struct BackendInstaller;

impl BackendInstaller {
    /// Install authentication backend modules
    pub fn install_auth(
        project_dir: &Path,
        config: &ProjectConfig,
        minimal: bool,
    ) -> Result<Vec<String>> {
        let backend_dir = project_dir.join(&config.backend.directory);
        if !backend_dir.exists() {
            return Err(CliError::InvalidPath(backend_dir));
        }

        println!("{}", "Installing Django authentication modules...".bold());

        let mut installed = Vec::new();

        // Core security bundle (always required)
        let security_modules = vec!["syntek-security-core", "syntek-security-auth"];

        for module in &security_modules {
            Self::install_module(&backend_dir, module, &config.backend.package_manager)?;
            installed.push(module.to_string());
        }

        // Authentication module
        Self::install_module(
            &backend_dir,
            "syntek-authentication",
            &config.backend.package_manager,
        )?;
        installed.push("syntek-authentication".to_string());

        // Full installation includes additional modules
        if !minimal {
            let additional = vec!["syntek-profiles", "syntek-audit"];

            for module in &additional {
                Self::install_module(&backend_dir, module, &config.backend.package_manager)?;
                installed.push(module.to_string());
            }
        }

        Ok(installed)
    }

    /// Install single Django module
    fn install_module(backend_dir: &Path, module: &str, package_manager: &str) -> Result<()> {
        let spinner = ProgressBar::new_spinner();
        spinner.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner:.green} {msg}")
                .unwrap(),
        );
        spinner.set_message(format!("Installing {}...", module.cyan()));
        spinner.enable_steady_tick(std::time::Duration::from_millis(100));

        let result = match package_manager {
            "uv" => exec::run_command("uv", &["pip", "install", module], Some(backend_dir)),
            "pip" => exec::run_command("pip", &["install", module], Some(backend_dir)),
            _ => {
                return Err(CliError::InvalidConfig(format!(
                    "Unsupported package manager: {}",
                    package_manager
                )))
            }
        };

        spinner.finish_and_clear();

        if result.is_ok() {
            println!("{} {}", "✓".green().bold(), module.cyan());
        } else {
            println!("{} {} (failed)", "✗".red().bold(), module.cyan());
        }

        result.map(|_| ())
    }

    /// Verify backend installation
    pub fn verify_installation(
        project_dir: &Path,
        config: &ProjectConfig,
        modules: &[String],
    ) -> Result<()> {
        println!("{}", "\nVerifying backend installation...".bold());

        let backend_dir = project_dir.join(&config.backend.directory);

        for module in modules {
            // Check if module can be imported
            let check_import = format!(
                "python -c \"import {}\"",
                module.replace('-', "_").replace("syntek_", "syntek_")
            );

            let result = exec::run_command_silent("sh", &["-c", &check_import], Some(&backend_dir));

            if result.is_ok() {
                println!("{} {} can be imported", "✓".green().bold(), module.cyan());
            } else {
                println!(
                    "{} {} cannot be imported",
                    "✗".red().bold(),
                    module.cyan()
                );
                return Err(CliError::SmokeTestFailed(format!(
                    "Module {} import failed",
                    module
                )));
            }
        }

        Ok(())
    }

    /// Add modules to INSTALLED_APPS in Django settings
    pub fn update_django_settings(
        project_dir: &Path,
        settings_path: &str,
        modules: &[String],
    ) -> Result<()> {
        let settings_file = project_dir.join(settings_path);
        if !settings_file.exists() {
            println!(
                "{}",
                "Warning: Django settings file not found. Please manually add modules to INSTALLED_APPS.".yellow()
            );
            return Ok(());
        }

        let content = std::fs::read_to_string(&settings_file)?;

        // Check if modules already added
        let all_present = modules
            .iter()
            .all(|m| content.contains(&format!("'{}'", m.replace('-', "_"))));

        if all_present {
            println!("{}", "Django settings already configured.".green());
            return Ok(());
        }

        println!(
            "{}",
            "\nAdd the following to INSTALLED_APPS in your Django settings:".yellow()
        );
        for module in modules {
            println!("    '{}',", module.replace('-', "_").cyan());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::loader::ConfigLoader;
    use tempfile::TempDir;

    #[test]
    fn test_backend_installer() {
        let temp_dir = TempDir::new().unwrap();
        let config = ConfigLoader::create_default("test-project");

        // Create backend directory
        let backend_dir = temp_dir.path().join(&config.backend.directory);
        std::fs::create_dir_all(&backend_dir).unwrap();

        // Note: Actual installation would require uv/pip to be available
        // This test just verifies the structure
        assert!(backend_dir.exists());
    }
}
