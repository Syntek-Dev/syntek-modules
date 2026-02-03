//! Command execution utilities
//!
//! This module provides helper functions for executing external commands
//! and capturing their output. Used throughout the CLI for running tools
//! like uv, pnpm, cargo, pytest, etc.

use std::process::Command;

/// Run a command and return an error if it fails
///
/// # Arguments
///
/// * `cmd` - Command name (e.g., "uv", "pnpm", "cargo")
/// * `args` - Command arguments as string slices
///
/// # Returns
///
/// * `Ok(())` if command exits with status 0
/// * `Err` with error message if command fails
///
/// # Examples
///
/// ```no_run
/// use crate::utils::exec::run_command;
/// run_command("uv", &["sync"])?;
/// ```
pub fn run_command(cmd: &str, args: &[&str]) -> anyhow::Result<()> {
    let status = Command::new(cmd).args(args).status()?;

    if !status.success() {
        anyhow::bail!("Command failed: {} {}", cmd, args.join(" "));
    }

    Ok(())
}

/// Run a command in a specific directory
///
/// # Arguments
///
/// * `cmd` - Command name
/// * `args` - Command arguments
/// * `dir` - Directory to run command in
///
/// # Returns
///
/// * `Ok(())` if command succeeds
/// * `Err` if command fails
pub fn run_command_in_dir(cmd: &str, args: &[&str], dir: &str) -> anyhow::Result<()> {
    let status = Command::new(cmd).args(args).current_dir(dir).status()?;

    if !status.success() {
        anyhow::bail!("Command failed: {} {} (in {})", cmd, args.join(" "), dir);
    }

    Ok(())
}

/// Run a command and capture its output
///
/// # Arguments
///
/// * `cmd` - Command name
/// * `args` - Command arguments
///
/// # Returns
///
/// * `Ok(String)` containing stdout if command succeeds
/// * `Err` if command fails
pub fn run_command_output(cmd: &str, args: &[&str]) -> anyhow::Result<String> {
    let output = Command::new(cmd).args(args).output()?;

    if !output.status.success() {
        anyhow::bail!("Command failed: {} {}", cmd, args.join(" "));
    }

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
