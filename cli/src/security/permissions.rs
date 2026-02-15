//! File permission validation
//!
//! Validates and enforces secure file permissions.

use crate::utils::error::{CliError, Result, Warning};
use std::path::Path;

/// Permission validator
pub struct PermissionValidator;

impl PermissionValidator {
    /// Validate config file permissions (should be 0600 or stricter)
    pub fn validate_config_file(path: &Path) -> Result<Vec<Warning>> {
        let mut warnings = Vec::new();

        if !path.exists() {
            return Err(CliError::ConfigNotFound(path.to_path_buf()));
        }

        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let metadata = std::fs::metadata(path)?;
            let mode = metadata.permissions().mode();

            // Config files should not be world-readable or group-readable
            if mode & 0o077 != 0 {
                warnings.push(Warning::InsecurePermissions {
                    path: path.to_path_buf(),
                    mode,
                    recommended: 0o600,
                });
            }
        }

        Ok(warnings)
    }

    /// Validate directory permissions (should be 0700 or 0755)
    pub fn validate_directory(path: &Path, allow_group_read: bool) -> Result<Vec<Warning>> {
        let mut warnings = Vec::new();

        if !path.exists() {
            return Err(CliError::InvalidPath(path.to_path_buf()));
        }

        if !path.is_dir() {
            return Err(CliError::FileOperation(format!(
                "{:?} is not a directory",
                path
            )));
        }

        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let metadata = std::fs::metadata(path)?;
            let mode = metadata.permissions().mode();

            let recommended = if allow_group_read { 0o755 } else { 0o700 };

            // Check for world-writable
            if mode & 0o002 != 0 {
                warnings.push(Warning::InsecurePermissions {
                    path: path.to_path_buf(),
                    mode,
                    recommended,
                });
            }

            // Check for excessive permissions
            if !allow_group_read && mode & 0o077 != 0 {
                warnings.push(Warning::InsecurePermissions {
                    path: path.to_path_buf(),
                    mode,
                    recommended,
                });
            }
        }

        Ok(warnings)
    }

    /// Set secure permissions on file
    #[cfg(unix)]
    pub fn set_secure_permissions(path: &Path, mode: u32) -> Result<()> {
        use std::os::unix::fs::PermissionsExt;
        let mut permissions = std::fs::metadata(path)?.permissions();
        permissions.set_mode(mode);
        std::fs::set_permissions(path, permissions)?;
        Ok(())
    }

    #[cfg(not(unix))]
    pub fn set_secure_permissions(_path: &Path, _mode: u32) -> Result<()> {
        // No-op on non-Unix systems
        Ok(())
    }

    /// Check if file is executable
    #[cfg(unix)]
    pub fn is_executable(path: &Path) -> Result<bool> {
        use std::os::unix::fs::PermissionsExt;
        let metadata = std::fs::metadata(path)?;
        let mode = metadata.permissions().mode();
        Ok(mode & 0o111 != 0)
    }

    #[cfg(not(unix))]
    pub fn is_executable(_path: &Path) -> Result<bool> {
        // On Windows, check extension
        Ok(_path
            .extension()
            .map(|ext| ext == "exe" || ext == "bat" || ext == "cmd")
            .unwrap_or(false))
    }
}

/// Set file permissions (convenience function)
pub fn set_file_permissions(path: &Path, mode: u32) -> Result<()> {
    PermissionValidator::set_secure_permissions(path, mode)
}

/// Check file permissions (convenience function)
pub fn check_file_permissions(path: &Path, _expected: u32) -> Result<()> {
    let warnings = PermissionValidator::validate_config_file(path)?;

    if !warnings.is_empty() {
        for warning in warnings {
            if let Warning::InsecurePermissions { path, mode, recommended } = warning {
                return Err(CliError::InsecurePermissions {
                    path,
                    mode,
                    recommended,
                });
            }
        }
    }

    Ok(())
}

#[cfg(test)]
#[cfg(unix)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_validate_config_file() {
        let temp = TempDir::new().unwrap();
        let file = temp.path().join("config.toml");

        fs::write(&file, "test").unwrap();

        // Set insecure permissions
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&file).unwrap().permissions();
        perms.set_mode(0o644);
        fs::set_permissions(&file, perms).unwrap();

        let warnings = PermissionValidator::validate_config_file(&file).unwrap();
        assert!(!warnings.is_empty());
    }

    #[test]
    fn test_set_secure_permissions() {
        let temp = TempDir::new().unwrap();
        let file = temp.path().join("test.txt");

        fs::write(&file, "test").unwrap();

        PermissionValidator::set_secure_permissions(&file, 0o600).unwrap();

        use std::os::unix::fs::PermissionsExt;
        let mode = fs::metadata(&file).unwrap().permissions().mode();
        assert_eq!(mode & 0o777, 0o600);
    }
}
