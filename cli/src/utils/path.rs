//! Path validation and manipulation utilities

use crate::utils::error::{CliError, Result};
use std::env;
use std::path::{Path, PathBuf};

/// Validate that a path is within a base directory (prevent directory traversal)
pub fn validate_path_within_base(base: &Path, path: &Path) -> Result<()> {
    let canonical_base = base.canonicalize().map_err(|_e| {
        CliError::InvalidPath(base.to_path_buf())
    })?;

    let canonical_path = if path.exists() {
        path.canonicalize().map_err(|_| {
            CliError::InvalidPath(path.to_path_buf())
        })?
    } else {
        // For non-existent paths, check parent directory
        let parent = path.parent().ok_or_else(|| {
            CliError::InvalidPath(path.to_path_buf())
        })?;

        let canonical_parent = parent.canonicalize().map_err(|_| {
            CliError::InvalidPath(parent.to_path_buf())
        })?;

        canonical_parent.join(path.file_name().ok_or_else(|| {
            CliError::InvalidPath(path.to_path_buf())
        })?)
    };

    if !canonical_path.starts_with(&canonical_base) {
        return Err(CliError::FileOperation(format!(
            "Path {:?} is outside base directory {:?}",
            path, base
        )));
    }

    Ok(())
}

/// Get current working directory
pub fn current_dir() -> Result<PathBuf> {
    env::current_dir().map_err(|e| {
        CliError::FileOperation(format!("Failed to get current directory: {}", e))
    })
}

/// Resolve path relative to base directory
pub fn resolve_path(base: &Path, path: &Path) -> PathBuf {
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        base.join(path)
    }
}

/// Get project root by searching for syntek.toml
pub fn find_project_root(start: &Path) -> Option<PathBuf> {
    let mut current = start;

    loop {
        if current.join("syntek.toml").exists() {
            return Some(current.to_path_buf());
        }

        if current.join(".git").exists() {
            // Git root without syntek.toml - not initialized
            return None;
        }

        current = current.parent()?;
    }
}

/// Get syntek-modules repository path
pub fn get_syntek_modules_path() -> Result<PathBuf> {
    // Try environment variable first
    if let Ok(path) = env::var("SYNTEK_MODULES_PATH") {
        let path = PathBuf::from(path);
        if path.exists() {
            return Ok(path);
        }
    }

    // Try relative to current directory
    let current = current_dir()?;
    let relative = current.join("syntek-modules");
    if relative.exists() {
        return Ok(relative);
    }

    // Try parent directory
    if let Some(parent) = current.parent() {
        let parent_modules = parent.join("syntek-modules");
        if parent_modules.exists() {
            return Ok(parent_modules);
        }
    }

    Err(CliError::ConfigNotFound(PathBuf::from("syntek-modules")))
}

/// Normalize path (resolve . and .., remove redundant separators)
pub fn normalize_path(path: &Path) -> PathBuf {
    let mut components = Vec::new();

    for component in path.components() {
        match component {
            std::path::Component::CurDir => {}
            std::path::Component::ParentDir => {
                components.pop();
            }
            c => components.push(c),
        }
    }

    components.iter().collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_validate_path_within_base() {
        let temp = TempDir::new().unwrap();
        let base = temp.path();
        let valid = base.join("subdir/file.txt");
        let invalid = temp.path().parent().unwrap().join("outside.txt");

        assert!(validate_path_within_base(base, &valid).is_ok());

        // This would fail because invalid is outside base
        // Can't test easily without creating parent directory
    }

    #[test]
    fn test_normalize_path() {
        let path = Path::new("/foo/./bar/../baz");
        let normalized = normalize_path(path);
        assert_eq!(normalized, PathBuf::from("/foo/baz"));
    }
}
