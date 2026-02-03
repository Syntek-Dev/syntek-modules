//! Dependency installation command
//!
//! Installs dependencies for specified targets:
//! - All: Python + Node + Rust
//! - Backend: Python (uv sync)
//! - Web/Mobile/Shared: Node (pnpm install)
//! - Rust: Cargo build
//!
//! Each ecosystem uses its appropriate package manager for optimal performance.

use colored::*;
use crate::utils::exec;

/// Run dependency installation for specified target
///
/// # Arguments
///
/// * `target` - Installation target (All, Backend, Web, Mobile, Shared, Rust)
///
/// # Returns
///
/// * `Ok(())` if installation succeeds
/// * `Err` if any installation fails
pub fn run(target: crate::InstallTarget) -> anyhow::Result<()> {
    println!("{}", "📦 Installing dependencies...".green().bold());

    match target {
        crate::InstallTarget::All => {
            install_backend()?;
            install_pnpm_workspace()?;
            install_rust()?;
        }
        crate::InstallTarget::Backend => install_backend()?,
        crate::InstallTarget::Web | crate::InstallTarget::Mobile | crate::InstallTarget::Shared => {
            install_pnpm_workspace()?;
        }
        crate::InstallTarget::Rust => install_rust()?,
    }

    println!("{}", "✅ Dependencies installed!".green().bold());
    Ok(())
}

fn install_backend() -> anyhow::Result<()> {
    println!("{}", "🐍 Installing Python dependencies...".cyan());
    exec::run_command("uv", &["sync"])?;
    Ok(())
}

fn install_pnpm_workspace() -> anyhow::Result<()> {
    println!(
        "{}",
        "📦 Installing pnpm workspace (web/mobile/shared)...".cyan()
    );
    exec::run_command("pnpm", &["install"])?;
    Ok(())
}

fn install_rust() -> anyhow::Result<()> {
    println!("{}", "🦀 Building Rust crates...".cyan());
    exec::run_command_in_dir("cargo", &["build", "--workspace"], "rust")?;
    Ok(())
}
