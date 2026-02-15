//! Rust crate installation module
//!
//! Installs Rust encryption/security crates.

use crate::config::loader::ProjectConfig;
use crate::utils::error::{CliError, Result};
use crate::utils::fs;
use colored::Colorize;
use std::path::Path;

/// Rust installer
pub struct RustInstaller;

impl RustInstaller {
    /// Install Rust authentication crates
    pub fn install_auth(
        syntek_modules_path: &Path,
        project_dir: &Path,
        _config: &ProjectConfig,
    ) -> Result<Vec<String>> {
        println!("{}", "\nInstalling Rust authentication crates...".bold());

        let rust_dir = project_dir.join("rust");
        if !rust_dir.exists() {
            std::fs::create_dir_all(&rust_dir)?;
        }

        let mut installed = Vec::new();

        // Copy Rust crates from syntek-modules
        let crates = vec!["encryption", "authentication"];

        for crate_name in &crates {
            Self::copy_crate(syntek_modules_path, &rust_dir, crate_name)?;
            installed.push(crate_name.to_string());
        }

        // Generate Cargo.toml for workspace
        Self::generate_workspace_cargo(&rust_dir, &crates)?;

        Ok(installed)
    }

    /// Copy Rust crate from syntek-modules
    fn copy_crate(syntek_modules_path: &Path, rust_dir: &Path, crate_name: &str) -> Result<()> {
        let source = syntek_modules_path.join("rust").join(crate_name);
        let target = rust_dir.join(crate_name);

        if !source.exists() {
            return Err(CliError::PackageNotFound(format!("rust/{}", crate_name)));
        }

        println!("Copying crate: {}", crate_name.cyan());
        fs::copy_dir_recursive(&source, &target)?;

        println!("{} {} crate installed", "✓".green().bold(), crate_name.cyan());

        Ok(())
    }

    /// Generate workspace Cargo.toml
    fn generate_workspace_cargo(rust_dir: &Path, crates: &[&str]) -> Result<()> {
        let workspace_toml = format!(
            r#"[workspace]
members = [
{}
]
resolver = "2"

[workspace.dependencies]
# Security
secrecy = {{ version = "0.10", features = ["serde"] }}
zeroize = {{ version = "1.8", features = ["derive"] }}

# Cryptography
argon2 = "0.5"
aes-gcm = "0.10"
sha2 = "0.10"
hmac = "0.12"

# PyO3 for Python bindings
pyo3 = {{ version = "0.21", features = ["extension-module"] }}

# Serialization
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"

# Error handling
anyhow = "1.0"
thiserror = "1.0"
"#,
            crates
                .iter()
                .map(|c| format!("    \"{}\",", c))
                .collect::<Vec<_>>()
                .join("\n")
        );

        let cargo_path = rust_dir.join("Cargo.toml");
        std::fs::write(&cargo_path, workspace_toml)?;

        println!(
            "{} Cargo workspace created at {}",
            "✓".green().bold(),
            cargo_path.display()
        );

        Ok(())
    }

    /// Verify Rust installation
    pub fn verify_installation(project_dir: &Path, crates: &[String]) -> Result<()> {
        println!("{}", "\nVerifying Rust installation...".bold());

        let rust_dir = project_dir.join("rust");

        // Check if Cargo.toml exists
        let cargo_toml = rust_dir.join("Cargo.toml");
        if !cargo_toml.exists() {
            return Err(CliError::ValidationFailed(
                "Cargo.toml not found in rust directory".to_string(),
            ));
        }
        println!("{} Cargo.toml found", "✓".green().bold());

        // Check each crate directory
        for crate_name in crates {
            let crate_dir = rust_dir.join(crate_name);
            let crate_toml = crate_dir.join("Cargo.toml");

            if crate_toml.exists() {
                println!(
                    "{} {} crate directory exists",
                    "✓".green().bold(),
                    crate_name.cyan()
                );
            } else {
                println!(
                    "{} {} crate not found",
                    "✗".red().bold(),
                    crate_name.cyan()
                );
                return Err(CliError::SmokeTestFailed(format!(
                    "Crate {} not installed",
                    crate_name
                )));
            }
        }

        // Try to build workspace
        println!("\nBuilding Rust workspace...");
        let result =
            crate::utils::exec::run_command("cargo", &["check", "--workspace"], Some(&rust_dir));

        if result.is_ok() {
            println!("{} Rust workspace builds successfully", "✓".green().bold());
        } else {
            println!(
                "{}",
                "Warning: Rust workspace check failed. You may need to fix dependencies.".yellow()
            );
        }

        Ok(())
    }

    /// Generate PyO3 setup instructions
    pub fn generate_pyo3_instructions() -> Result<()> {
        println!("{}", "\nPyO3 Integration Instructions:".yellow());

        let instructions = r#"
To use Rust encryption from Django:

1. Build the Rust library:
   cd rust && cargo build --release

2. Create Python bindings package:
   cd rust/encryption && maturin develop

3. Import in Django:
   from syntek_rust_encryption import hash_password, encrypt_field

4. Add to pyproject.toml:
   [dependencies]
   syntek-rust-encryption = { path = "./rust/encryption" }

5. Install with uv:
   uv pip install -e ./rust/encryption
"#;

        println!("{}", instructions.cyan());

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::loader::ConfigLoader;
    use tempfile::TempDir;

    #[test]
    fn test_generate_workspace_cargo() {
        let temp_dir = TempDir::new().unwrap();
        let rust_dir = temp_dir.path().join("rust");
        std::fs::create_dir_all(&rust_dir).unwrap();

        let crates = vec!["encryption", "authentication"];
        let result = RustInstaller::generate_workspace_cargo(&rust_dir, &crates);
        assert!(result.is_ok());
        assert!(rust_dir.join("Cargo.toml").exists());
    }
}
