//! Configuration validator
//!
//! Validates project structure, dependencies, and configuration completeness.

use crate::config::loader::ProjectConfig;
use crate::utils::error::{CliError, Result, Warning};
use std::path::Path;

/// Validation result with warnings
pub struct ValidationResult {
    pub success: bool,
    pub warnings: Vec<Warning>,
    pub errors: Vec<String>,
}

impl ValidationResult {
    pub fn new() -> Self {
        Self {
            success: true,
            warnings: Vec::new(),
            errors: Vec::new(),
        }
    }

    pub fn add_error(&mut self, error: String) {
        self.success = false;
        self.errors.push(error);
    }

    pub fn add_warning(&mut self, warning: Warning) {
        self.warnings.push(warning);
    }

    pub fn is_ok(&self) -> bool {
        self.success
    }
}

impl Default for ValidationResult {
    fn default() -> Self {
        Self::new()
    }
}

/// Configuration validator
pub struct ConfigValidator;

impl ConfigValidator {
    /// Validate complete project structure
    pub fn validate_project(project_dir: &Path, config: &ProjectConfig) -> ValidationResult {
        let mut result = ValidationResult::new();

        // Validate directory structure
        Self::validate_directories(project_dir, config, &mut result);

        // Validate configuration completeness
        Self::validate_config_completeness(config, &mut result);

        // Validate dependencies
        Self::validate_dependencies(project_dir, config, &mut result);

        result
    }

    /// Validate directory structure exists
    fn validate_directories(
        project_dir: &Path,
        config: &ProjectConfig,
        result: &mut ValidationResult,
    ) {
        // Check backend directory
        let backend_dir = project_dir.join(&config.backend.directory);
        if !backend_dir.exists() {
            result.add_warning(Warning::MissingOptionalDependency {
                name: "backend".to_string(),
                feature: format!("Backend directory: {}", config.backend.directory),
            });
        }

        // Check web directory
        if !config.web.directory.is_empty() {
            let web_dir = project_dir.join(&config.web.directory);
            if !web_dir.exists() {
                result.add_warning(Warning::MissingOptionalDependency {
                    name: "web".to_string(),
                    feature: format!("Web directory: {}", config.web.directory),
                });
            }
        }

        // Check mobile directory
        if !config.mobile.directory.is_empty() {
            let mobile_dir = project_dir.join(&config.mobile.directory);
            if !mobile_dir.exists() {
                result.add_warning(Warning::MissingOptionalDependency {
                    name: "mobile".to_string(),
                    feature: format!("Mobile directory: {}", config.mobile.directory),
                });
            }
        }

        // Check shared directory
        if config.shared.enabled {
            let shared_dir = project_dir.join(&config.shared.directory);
            if !shared_dir.exists() {
                result.add_error(format!(
                    "Shared directory not found: {}",
                    config.shared.directory
                ));
            }
        }
    }

    /// Validate configuration completeness
    fn validate_config_completeness(config: &ProjectConfig, result: &mut ValidationResult) {
        // Check project metadata
        if config.project.name.is_empty() {
            result.add_error("Project name is required".to_string());
        }

        if config.project.version.is_empty() {
            result.add_error("Project version is required".to_string());
        }

        // Check backend config
        if config.backend.django_version.is_none() {
            result.add_warning(Warning::MissingOptionalDependency {
                name: "django_version".to_string(),
                feature: "Backend configuration".to_string(),
            });
        }

        if config.backend.python_version.is_none() {
            result.add_warning(Warning::MissingOptionalDependency {
                name: "python_version".to_string(),
                feature: "Backend configuration".to_string(),
            });
        }

        // Check frontend config
        if config.web.framework.is_none() && config.mobile.framework.is_none() {
            result.add_warning(Warning::MissingOptionalDependency {
                name: "frontend_framework".to_string(),
                feature: "No frontend framework configured".to_string(),
            });
        }
    }

    /// Validate dependencies are installed
    fn validate_dependencies(
        project_dir: &Path,
        config: &ProjectConfig,
        result: &mut ValidationResult,
    ) {
        // Check Python/uv
        if config.backend.package_manager == "uv" {
            let uv_lock = project_dir.join(&config.backend.directory).join("uv.lock");
            if !uv_lock.exists() {
                result.add_warning(Warning::MissingOptionalDependency {
                    name: "uv.lock".to_string(),
                    feature: "Backend dependencies not installed".to_string(),
                });
            }
        }

        // Check Node.js/pnpm
        if config.web.package_manager == "pnpm" && !config.web.directory.is_empty() {
            let pnpm_lock = project_dir.join(&config.web.directory).join("pnpm-lock.yaml");
            if !pnpm_lock.exists() {
                result.add_warning(Warning::MissingOptionalDependency {
                    name: "pnpm-lock.yaml".to_string(),
                    feature: "Web dependencies not installed".to_string(),
                });
            }
        }

        if config.mobile.package_manager == "pnpm" && !config.mobile.directory.is_empty() {
            let pnpm_lock = project_dir
                .join(&config.mobile.directory)
                .join("pnpm-lock.yaml");
            if !pnpm_lock.exists() {
                result.add_warning(Warning::MissingOptionalDependency {
                    name: "pnpm-lock.yaml".to_string(),
                    feature: "Mobile dependencies not installed".to_string(),
                });
            }
        }
    }

    /// Validate authentication module installation
    pub fn validate_auth_installation(
        project_dir: &Path,
        config: &ProjectConfig,
    ) -> ValidationResult {
        let mut result = ValidationResult::new();

        // Check if auth modules are installed
        if !config.modules.backend.contains(&"syntek-authentication".to_string()) {
            result.add_error("syntek-authentication not installed in backend".to_string());
        }

        if !config.modules.graphql.contains(&"syntek-graphql-auth".to_string()) {
            result.add_error("syntek-graphql-auth not installed".to_string());
        }

        // Check for required files
        let config_dir = project_dir.join("config").join("auth");
        if !config_dir.exists() {
            result.add_error("Auth configuration directory not found".to_string());
        } else {
            let settings_path = config_dir.join("settings.toml");
            if !settings_path.exists() {
                result.add_error("Auth settings.toml not found".to_string());
            }
        }

        let env_example = project_dir.join(".env.example");
        if !env_example.exists() {
            result.add_warning(Warning::MissingOptionalDependency {
                name: ".env.example".to_string(),
                feature: "Environment template not found".to_string(),
            });
        }

        result
    }

    /// Check for security issues
    pub fn validate_security(project_dir: &Path) -> ValidationResult {
        let mut result = ValidationResult::new();

        // Check .env file permissions
        let env_file = project_dir.join(".env");
        if env_file.exists() {
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                if let Ok(metadata) = std::fs::metadata(&env_file) {
                    let mode = metadata.permissions().mode();
                    let file_mode = mode & 0o777;
                    if file_mode != 0o600 {
                        result.add_warning(Warning::InsecurePermissions {
                            path: env_file.clone(),
                            mode: file_mode,
                            recommended: 0o600,
                        });
                    }
                }
            }
        }

        // Check for potential secrets in config files
        let config_auth = project_dir.join("config").join("auth").join("settings.toml");
        if config_auth.exists() {
            if let Ok(content) = std::fs::read_to_string(&config_auth) {
                if content.contains("your_") || content.contains("example_") {
                    result.add_warning(Warning::PotentialSecret {
                        path: "config/auth/settings.toml".to_string(),
                        suggestion: "Replace placeholder values before deploying".to_string(),
                    });
                }
            }

            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                if let Ok(metadata) = std::fs::metadata(&config_auth) {
                    let mode = metadata.permissions().mode();
                    let file_mode = mode & 0o777;
                    if file_mode != 0o600 {
                        result.add_warning(Warning::InsecurePermissions {
                            path: config_auth.clone(),
                            mode: file_mode,
                            recommended: 0o600,
                        });
                    }
                }
            }
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::loader::ConfigLoader;
    use tempfile::TempDir;

    #[test]
    fn test_validate_config_completeness() {
        let config = ConfigLoader::create_default("test-project");
        let mut result = ValidationResult::new();

        ConfigValidator::validate_config_completeness(&config, &mut result);
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_directories() {
        let temp_dir = TempDir::new().unwrap();
        let config = ConfigLoader::create_default("test-project");
        let mut result = ValidationResult::new();

        ConfigValidator::validate_directories(temp_dir.path(), &config, &mut result);
        // Should have warnings for missing directories
        assert!(!result.warnings.is_empty());
    }

    #[test]
    fn test_validate_auth_installation() {
        let temp_dir = TempDir::new().unwrap();
        let config = ConfigLoader::create_default("test-project");

        let result = ConfigValidator::validate_auth_installation(temp_dir.path(), &config);
        // Should fail as auth is not installed
        assert!(!result.is_ok());
    }
}
