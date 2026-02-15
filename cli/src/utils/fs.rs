//! File system operations
//!
//! Secure file operations with permission validation.

use crate::utils::error::{CliError, Result, Warning};
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Copy directory recursively with permission validation
pub fn copy_dir_all(src: &Path, dst: &Path) -> Result<()> {
    if !src.exists() {
        return Err(CliError::InvalidPath(src.to_path_buf()));
    }

    if !src.is_dir() {
        return Err(CliError::FileOperation(format!(
            "{:?} is not a directory",
            src
        )));
    }

    // Create destination directory
    fs::create_dir_all(dst)?;

    for entry in WalkDir::new(src)
        .follow_links(false)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let path = entry.path();
        let relative = path.strip_prefix(src).map_err(|e| {
            CliError::FileOperation(format!("Failed to strip prefix: {}", e))
        })?;

        let target = dst.join(relative);

        if entry.file_type().is_dir() {
            fs::create_dir_all(&target)?;
        } else {
            if let Some(parent) = target.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::copy(path, &target)?;

            // Preserve executable permissions on Unix
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let metadata = fs::metadata(path)?;
                let permissions = metadata.permissions();
                fs::set_permissions(&target, permissions)?;
            }
        }
    }

    Ok(())
}

/// Create file with secure permissions (0600 on Unix)
pub fn create_secure_file(path: &Path, contents: &str) -> Result<()> {
    fs::write(path, contents)?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut permissions = fs::metadata(path)?.permissions();
        permissions.set_mode(0o600);
        fs::set_permissions(path, permissions)?;
    }

    Ok(())
}

/// Check if directory is empty
pub fn is_dir_empty(path: &Path) -> Result<bool> {
    if !path.exists() {
        return Ok(true);
    }

    if !path.is_dir() {
        return Err(CliError::FileOperation(format!(
            "{:?} is not a directory",
            path
        )));
    }

    let entries = fs::read_dir(path)?;
    Ok(entries.count() == 0)
}

/// Validate file permissions (Unix only)
#[cfg(unix)]
pub fn validate_permissions(path: &Path, expected_mode: u32) -> Result<Option<Warning>> {
    use std::os::unix::fs::PermissionsExt;

    let metadata = fs::metadata(path)?;
    let mode = metadata.permissions().mode();

    // Check if world-readable or world-writable
    if mode & 0o077 != 0 {
        return Ok(Some(Warning::InsecurePermissions {
            path: path.to_path_buf(),
            mode,
            recommended: expected_mode,
        }));
    }

    Ok(None)
}

#[cfg(not(unix))]
pub fn validate_permissions(_path: &Path, _expected_mode: u32) -> Result<Option<Warning>> {
    Ok(None)
}

/// Ensure directory exists with secure permissions
pub fn ensure_dir(path: &Path) -> Result<()> {
    if path.exists() {
        if !path.is_dir() {
            return Err(CliError::FileOperation(format!(
                "{:?} exists but is not a directory",
                path
            )));
        }
        return Ok(());
    }

    fs::create_dir_all(path)?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut permissions = fs::metadata(path)?.permissions();
        permissions.set_mode(0o755);
        fs::set_permissions(path, permissions)?;
    }

    Ok(())
}

/// Remove directory if empty, warn if not
pub fn remove_dir_if_empty(path: &Path) -> Result<bool> {
    if is_dir_empty(path)? {
        fs::remove_dir(path)?;
        Ok(true)
    } else {
        Ok(false)
    }
}

/// Find file by name in directory tree
pub fn find_file(base: &Path, name: &str) -> Option<PathBuf> {
    WalkDir::new(base)
        .follow_links(false)
        .into_iter()
        .filter_map(|e| e.ok())
        .find(|e| e.file_name().to_str() == Some(name))
        .map(|e| e.path().to_path_buf())
}

/// Alias for copy_dir_all
pub fn copy_dir_recursive(src: &Path, dst: &Path) -> Result<()> {
    copy_dir_all(src, dst)
}

/// Alias for fs::create_dir_all
pub fn create_dir_all(path: &Path) -> Result<()> {
    fs::create_dir_all(path).map_err(|e| CliError::Io(e))
}

/// Write file with content
pub fn write_file(path: &Path, content: &str) -> Result<()> {
    fs::write(path, content).map_err(|e| CliError::Io(e))
}

/// Copy file
pub fn copy_file(src: &Path, dst: &Path) -> Result<()> {
    fs::copy(src, dst).map_err(|e| CliError::Io(e))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_copy_dir_all() {
        let temp = TempDir::new().unwrap();
        let src = temp.path().join("src");
        let dst = temp.path().join("dst");

        fs::create_dir(&src).unwrap();
        fs::write(src.join("file.txt"), "test").unwrap();

        copy_dir_all(&src, &dst).unwrap();
        assert!(dst.join("file.txt").exists());
    }

    #[test]
    fn test_is_dir_empty() {
        let temp = TempDir::new().unwrap();
        let empty = temp.path().join("empty");
        let not_empty = temp.path().join("not_empty");

        fs::create_dir(&empty).unwrap();
        fs::create_dir(&not_empty).unwrap();
        fs::write(not_empty.join("file.txt"), "test").unwrap();

        assert!(is_dir_empty(&empty).unwrap());
        assert!(!is_dir_empty(&not_empty).unwrap());
    }
}
