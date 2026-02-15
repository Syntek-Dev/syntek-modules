//! Configuration loader
//!
//! Loads and parses syntek.toml project configuration.

use crate::utils::error::{CliError, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

/// Project configuration (syntek.toml)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectConfig {
    /// Project metadata
    pub project: ProjectMetadata,

    /// Backend configuration
    #[serde(default)]
    pub backend: BackendConfig,

    /// Web frontend configuration
    #[serde(default)]
    pub web: FrontendConfig,

    /// Mobile frontend configuration
    #[serde(default)]
    pub mobile: FrontendConfig,

    /// Shared modules configuration
    #[serde(default)]
    pub shared: SharedConfig,

    /// Installed modules
    #[serde(default)]
    pub modules: InstalledModules,
}

/// Project metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectMetadata {
    /// Project name
    pub name: String,

    /// Project version
    pub version: String,

    /// Description
    #[serde(default)]
    pub description: String,

    /// Authors
    #[serde(default)]
    pub authors: Vec<String>,
}

/// Backend configuration
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BackendConfig {
    /// Django version
    #[serde(default)]
    pub django_version: Option<String>,

    /// Python version
    #[serde(default)]
    pub python_version: Option<String>,

    /// Package manager (uv, pip)
    #[serde(default = "default_backend_package_manager")]
    pub package_manager: String,

    /// Backend directory
    #[serde(default = "default_backend_dir")]
    pub directory: String,
}

fn default_backend_package_manager() -> String {
    "uv".to_string()
}

fn default_backend_dir() -> String {
    "backend".to_string()
}

/// Frontend configuration
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct FrontendConfig {
    /// Framework (nextjs, react-native)
    #[serde(default)]
    pub framework: Option<String>,

    /// TypeScript version
    #[serde(default)]
    pub typescript_version: Option<String>,

    /// Package manager (npm, pnpm, yarn)
    #[serde(default = "default_frontend_package_manager")]
    pub package_manager: String,

    /// Directory
    #[serde(default)]
    pub directory: String,
}

fn default_frontend_package_manager() -> String {
    "pnpm".to_string()
}

/// Shared modules configuration
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SharedConfig {
    /// Shared directory
    #[serde(default = "default_shared_dir")]
    pub directory: String,

    /// Enable code sharing
    #[serde(default = "default_true")]
    pub enabled: bool,
}

fn default_shared_dir() -> String {
    "shared".to_string()
}

fn default_true() -> bool {
    true
}

/// Installed modules tracking
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct InstalledModules {
    /// Backend modules
    #[serde(default)]
    pub backend: Vec<String>,

    /// Web modules
    #[serde(default)]
    pub web: Vec<String>,

    /// Mobile modules
    #[serde(default)]
    pub mobile: Vec<String>,

    /// Shared modules
    #[serde(default)]
    pub shared: Vec<String>,

    /// GraphQL modules
    #[serde(default)]
    pub graphql: Vec<String>,

    /// Rust crates
    #[serde(default)]
    pub rust: Vec<String>,
}

/// Configuration loader
pub struct ConfigLoader;

impl ConfigLoader {
    /// Load configuration from file
    pub fn load(config_path: &Path) -> Result<ProjectConfig> {
        if !config_path.exists() {
            return Err(CliError::ConfigNotFound(config_path.to_path_buf()));
        }

        let content = std::fs::read_to_string(config_path)?;
        let config: ProjectConfig = toml::from_str(&content)?;

        Ok(config)
    }

    /// Load configuration from project root
    pub fn load_from_project(project_dir: &Path) -> Result<ProjectConfig> {
        let config_path = project_dir.join("syntek.toml");
        Self::load(&config_path)
    }

    /// Save configuration to file
    pub fn save(config_path: &Path, config: &ProjectConfig) -> Result<()> {
        let content = toml::to_string_pretty(config)?;
        std::fs::write(config_path, content)?;
        Ok(())
    }

    /// Save configuration to project root
    pub fn save_to_project(project_dir: &Path, config: &ProjectConfig) -> Result<()> {
        let config_path = project_dir.join("syntek.toml");
        Self::save(&config_path, config)
    }

    /// Create default configuration
    pub fn create_default(project_name: &str) -> ProjectConfig {
        ProjectConfig {
            project: ProjectMetadata {
                name: project_name.to_string(),
                version: "0.1.0".to_string(),
                description: String::new(),
                authors: Vec::new(),
            },
            backend: BackendConfig {
                django_version: Some("6.0.2".to_string()),
                python_version: Some("3.14".to_string()),
                package_manager: "uv".to_string(),
                directory: "backend".to_string(),
            },
            web: FrontendConfig {
                framework: Some("nextjs".to_string()),
                typescript_version: Some("5.9".to_string()),
                package_manager: "pnpm".to_string(),
                directory: "web/packages".to_string(),
            },
            mobile: FrontendConfig {
                framework: Some("react-native".to_string()),
                typescript_version: Some("5.9".to_string()),
                package_manager: "pnpm".to_string(),
                directory: "mobile/packages".to_string(),
            },
            shared: SharedConfig {
                directory: "shared".to_string(),
                enabled: true,
            },
            modules: InstalledModules::default(),
        }
    }

    /// Add installed module
    pub fn add_module(
        config: &mut ProjectConfig,
        module_type: &str,
        module_name: &str,
    ) -> Result<()> {
        let module_list = match module_type {
            "backend" => &mut config.modules.backend,
            "web" => &mut config.modules.web,
            "mobile" => &mut config.modules.mobile,
            "shared" => &mut config.modules.shared,
            "graphql" => &mut config.modules.graphql,
            "rust" => &mut config.modules.rust,
            _ => {
                return Err(CliError::InvalidConfig(format!(
                    "Unknown module type: {}",
                    module_type
                )))
            }
        };

        if !module_list.contains(&module_name.to_string()) {
            module_list.push(module_name.to_string());
        }

        Ok(())
    }

    /// Check if module is installed
    pub fn is_module_installed(config: &ProjectConfig, module_type: &str, module_name: &str) -> bool {
        let module_list = match module_type {
            "backend" => &config.modules.backend,
            "web" => &config.modules.web,
            "mobile" => &config.modules.mobile,
            "shared" => &config.modules.shared,
            "graphql" => &config.modules.graphql,
            "rust" => &config.modules.rust,
            _ => return false,
        };

        module_list.contains(&module_name.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_create_default_config() {
        let config = ConfigLoader::create_default("test-project");
        assert_eq!(config.project.name, "test-project");
        assert_eq!(config.backend.package_manager, "uv");
        assert_eq!(config.web.package_manager, "pnpm");
    }

    #[test]
    fn test_save_and_load_config() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("syntek.toml");
        let config = ConfigLoader::create_default("test-project");

        ConfigLoader::save(&config_path, &config).unwrap();
        let loaded = ConfigLoader::load(&config_path).unwrap();

        assert_eq!(loaded.project.name, config.project.name);
    }

    #[test]
    fn test_add_module() {
        let mut config = ConfigLoader::create_default("test-project");
        ConfigLoader::add_module(&mut config, "backend", "syntek-authentication").unwrap();

        assert!(ConfigLoader::is_module_installed(
            &config,
            "backend",
            "syntek-authentication"
        ));
    }
}
