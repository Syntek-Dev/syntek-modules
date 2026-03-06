use anyhow::{bail, Result};
use std::env;
use std::path::PathBuf;

/// Locate the workspace root by walking up from the current directory,
/// looking for a Cargo.toml that contains `[workspace]`.
pub fn find_root() -> Result<PathBuf> {
    let mut dir = env::current_dir()?;
    loop {
        let candidate = dir.join("Cargo.toml");
        if candidate.exists() {
            let content = std::fs::read_to_string(&candidate)?;
            if content.contains("[workspace]") {
                return Ok(dir);
            }
        }
        if !dir.pop() {
            bail!(
                "Could not locate syntek-modules workspace root.\n\
                 Run syntek-dev from inside the repository."
            );
        }
    }
}

/// Return the path to a binary in the project's Python virtual environment.
pub fn venv_bin(root: &PathBuf, name: &str) -> String {
    let path = root.join(".venv").join("bin").join(name);
    if path.exists() {
        path.to_string_lossy().to_string()
    } else {
        name.to_string()
    }
}

/// Return true if the Python virtual environment exists.
pub fn venv_exists(root: &PathBuf) -> bool {
    root.join(".venv").join("bin").join("python").exists()
}

/// Return the path to sandbox/manage.py, if it exists.
pub fn sandbox_manage(root: &PathBuf) -> Option<PathBuf> {
    let p = root.join("sandbox").join("manage.py");
    if p.exists() { Some(p) } else { None }
}

/// List backend package directories that contain a pyproject.toml.
#[allow(dead_code)]
pub fn backend_packages(root: &PathBuf) -> Vec<PathBuf> {
    let backend = root.join("packages").join("backend");
    if !backend.exists() {
        return vec![];
    }
    std::fs::read_dir(&backend)
        .map(|entries| {
            entries
                .filter_map(|e| e.ok())
                .map(|e| e.path())
                .filter(|p| p.is_dir() && p.join("pyproject.toml").exists())
                .collect()
        })
        .unwrap_or_default()
}
