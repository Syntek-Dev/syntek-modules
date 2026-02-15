//! Configuration file generator
//!
//! Orchestrates generation of Django settings, env files, and documentation.

use crate::config::auth_config::AuthConfig;
use crate::config::templates::{configuration_readme, django_settings_toml, env_template};
use crate::security::permissions;
use crate::utils::error::{CliError, Result};
use crate::utils::fs;
use std::path::Path;

/// Configuration generator
pub struct ConfigGenerator;

impl ConfigGenerator {
    /// Generate all configuration files for target project
    pub fn generate_auth_config(target_dir: &Path, config: &AuthConfig) -> Result<()> {
        // Create config directory
        let config_dir = target_dir.join("config").join("auth");
        fs::create_dir_all(&config_dir)?;

        // Generate Django settings
        let settings_path = config_dir.join("settings.toml");
        let settings_content = django_settings_toml(config);
        fs::write_file(&settings_path, &settings_content)?;
        permissions::set_file_permissions(&settings_path, 0o600)?;

        // Generate .env template
        let env_path = target_dir.join(".env.example");
        let env_content = env_template(config);
        fs::write_file(&env_path, &env_content)?;
        permissions::set_file_permissions(&env_path, 0o600)?;

        // Generate README
        let readme_path = config_dir.join("README.md");
        let readme_content = configuration_readme(config);
        fs::write_file(&readme_path, &readme_content)?;

        // Generate actual .env if it doesn't exist
        let env_actual = target_dir.join(".env");
        if !env_actual.exists() {
            fs::write_file(&env_actual, &env_content)?;
            permissions::set_file_permissions(&env_actual, 0o600)?;
        }

        Ok(())
    }

    /// Validate configuration files were created
    pub fn verify_config_files(target_dir: &Path) -> Result<()> {
        let config_dir = target_dir.join("config").join("auth");
        let settings_path = config_dir.join("settings.toml");
        let env_path = target_dir.join(".env.example");
        let readme_path = config_dir.join("README.md");

        if !settings_path.exists() {
            return Err(CliError::ValidationFailed(
                "settings.toml not found".to_string(),
            ));
        }

        if !env_path.exists() {
            return Err(CliError::ValidationFailed(
                ".env.example not found".to_string(),
            ));
        }

        if !readme_path.exists() {
            return Err(CliError::ValidationFailed("README.md not found".to_string()));
        }

        // Check permissions
        permissions::check_file_permissions(&settings_path, 0o600)?;
        permissions::check_file_permissions(&env_path, 0o600)?;

        Ok(())
    }

    /// Update existing configuration (merge changes)
    pub fn update_config(target_dir: &Path, config: &AuthConfig) -> Result<()> {
        let config_dir = target_dir.join("config").join("auth");
        let settings_path = config_dir.join("settings.toml");

        // Backup existing config
        if settings_path.exists() {
            let backup_path = config_dir.join("settings.toml.backup");
            fs::copy_file(&settings_path, &backup_path)?;
        }

        // Write new config
        Self::generate_auth_config(target_dir, config)?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::auth_config::{AuthConfigGenerator, InstallMode};
    use crate::security::SecretsManager;
    use tempfile::TempDir;

    #[test]
    fn test_generate_config_files() {
        let temp_dir = TempDir::new().unwrap();
        let mut secrets = SecretsManager::new();
        let config = AuthConfigGenerator::generate(InstallMode::Full, &mut secrets).unwrap();

        let result = ConfigGenerator::generate_auth_config(temp_dir.path(), &config);
        assert!(result.is_ok());

        // Verify files exist
        let config_dir = temp_dir.path().join("config").join("auth");
        assert!(config_dir.join("settings.toml").exists());
        assert!(temp_dir.path().join(".env.example").exists());
        assert!(config_dir.join("README.md").exists());
    }

    #[test]
    fn test_verify_config_files() {
        let temp_dir = TempDir::new().unwrap();
        let mut secrets = SecretsManager::new();
        let config = AuthConfigGenerator::generate(InstallMode::Full, &mut secrets).unwrap();

        ConfigGenerator::generate_auth_config(temp_dir.path(), &config).unwrap();
        let result = ConfigGenerator::verify_config_files(temp_dir.path());
        assert!(result.is_ok());
    }
}
