//! Tool installation and verification utilities
//!
//! This module provides functions for checking, installing, and configuring
//! development tools required by the Syntek Modules repository:
//!
//! - Python tools (pytest, pre-commit, detect-secrets)
//! - Rust components (rustfmt, clippy)
//! - Node dependencies (via pnpm)
//! - Git hooks (pre-commit, commit-msg)
//! - Secrets baseline (for secret scanning)

use colored::*;
use std::process::Command;

/// Check if a tool is installed
///
/// # Arguments
///
/// * `tool` - Tool name (e.g., "uv", "git", "pnpm")
///
/// # Returns
///
/// * `true` if tool is installed and responds to --version
/// * `false` if tool is not found
pub fn check_tool_installed(tool: &str) -> bool {
    Command::new(tool)
        .arg("--version")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

/// Ensure Python virtual environment exists
pub fn ensure_venv_exists() -> anyhow::Result<()> {
    let venv_path = std::path::Path::new(".venv");

    if venv_path.exists() {
        println!("{}", "   ✓ Virtual environment already exists".green());
    } else {
        println!(
            "{}",
            "   Creating virtual environment with uv sync...".dimmed()
        );
        crate::utils::exec::run_command("uv", &["sync"])?;
        println!("{}", "   ✓ Virtual environment created".green());
    }

    Ok(())
}

/// Install Python dev tools
pub fn install_python_dev_tools() -> anyhow::Result<()> {
    println!("{}", "   🐍 Installing Python dev tools...".dimmed());

    print!("      Syncing dev dependencies...");
    std::io::Write::flush(&mut std::io::stdout())?;

    let output = Command::new("uv")
        .args(["sync", "--extra", "dev"])
        .output()?;

    if output.status.success() {
        println!(" {}", "✓".green());
        println!("{}", "   ✓ Python dev tools installed".green());
    } else {
        println!(" {}", "✗".red());
        let stderr = String::from_utf8_lossy(&output.stderr);
        eprintln!("{}", stderr);
        anyhow::bail!("Failed to sync dev dependencies");
    }

    Ok(())
}

/// Install Rust components
pub fn install_rust_components() -> anyhow::Result<()> {
    println!("{}", "   🦀 Installing Rust components...".dimmed());

    let rustfmt_check = Command::new("rustup")
        .args(["component", "list"])
        .output()?;

    let rustfmt_output = String::from_utf8_lossy(&rustfmt_check.stdout);

    if !rustfmt_output.contains("rustfmt") || !rustfmt_output.contains("installed") {
        print!("      Installing rustfmt...");
        std::io::Write::flush(&mut std::io::stdout())?;

        let output = Command::new("rustup")
            .args(["component", "add", "rustfmt"])
            .output()?;

        if output.status.success() {
            println!(" {}", "✓".green());
        } else {
            println!(" {}", "✗".red());
        }
    } else {
        println!("{}", "      rustfmt already installed ✓".dimmed());
    }

    if !rustfmt_output.contains("clippy") || !rustfmt_output.contains("installed") {
        print!("      Installing clippy...");
        std::io::Write::flush(&mut std::io::stdout())?;

        let output = Command::new("rustup")
            .args(["component", "add", "clippy"])
            .output()?;

        if output.status.success() {
            println!(" {}", "✓".green());
        } else {
            println!(" {}", "✗".red());
        }
    } else {
        println!("{}", "      clippy already installed ✓".dimmed());
    }

    println!("{}", "   ✓ Rust components installed".green());
    Ok(())
}

/// Install Node dependencies
pub fn install_node_dependencies() -> anyhow::Result<()> {
    println!("{}", "   📦 Installing Node dependencies...".dimmed());

    let output = Command::new("pnpm")
        .args(["install", "--silent"])
        .output()?;

    if output.status.success() {
        println!("{}", "   ✓ Node dependencies installed".green());
    } else {
        println!(
            "{}",
            "   ⚠ Warning: Node dependencies installation had issues".yellow()
        );
    }

    Ok(())
}

/// Setup Git hooks
pub fn setup_git_hooks() -> anyhow::Result<()> {
    if !std::path::Path::new(".git").exists() {
        println!("{}", "   ⚠ Not a git repository - skipping hooks".yellow());
        return Ok(());
    }

    print!("      Installing pre-commit hook...");
    std::io::Write::flush(&mut std::io::stdout())?;

    let output = Command::new("uv")
        .args(["run", "pre-commit", "install"])
        .output()?;

    if output.status.success() {
        println!(" {}", "✓".green());
    } else {
        println!(" {}", "✗".red());
        anyhow::bail!("Failed to install pre-commit hook");
    }

    print!("      Installing commit-msg hook...");
    std::io::Write::flush(&mut std::io::stdout())?;

    let output = Command::new("uv")
        .args(["run", "pre-commit", "install", "--hook-type", "commit-msg"])
        .output()?;

    if output.status.success() {
        println!(" {}", "✓".green());
    } else {
        println!(" {}", "✗".red());
        anyhow::bail!("Failed to install commit-msg hook");
    }

    println!("{}", "   ✓ Git hooks installed".green());
    Ok(())
}

/// Create secrets baseline
pub fn create_secrets_baseline() -> anyhow::Result<()> {
    let baseline_path = std::path::Path::new(".secrets.baseline");

    if baseline_path.exists() {
        println!("{}", "   ✓ Secrets baseline already exists".green());
        return Ok(());
    }

    print!("      Scanning for secrets...");
    std::io::Write::flush(&mut std::io::stdout())?;

    let output = Command::new("uv")
        .args([
            "run",
            "detect-secrets",
            "scan",
            "--baseline",
            ".secrets.baseline",
        ])
        .output()?;

    if output.status.success() {
        println!(" {}", "✓".green());
        println!("{}", "   ✓ Secrets baseline created".green());
    } else {
        println!(" {}", "✗".red());
        anyhow::bail!("Failed to create secrets baseline");
    }

    Ok(())
}
