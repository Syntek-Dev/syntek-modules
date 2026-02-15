//! Command execution helpers
//!
//! Secure command execution with output capture and error handling.

use crate::utils::error::{CliError, Result};
use std::process::{Command, Output, Stdio};
use std::path::Path;

/// Execute command and return output
pub fn run_command(cmd: &str, args: &[&str], cwd: Option<&Path>) -> Result<Output> {
    let mut command = Command::new(cmd);
    command.args(args);

    if let Some(dir) = cwd {
        command.current_dir(dir);
    }

    let output = command
        .output()
        .map_err(|e| CliError::CommandFailed(format!("Failed to execute {}: {}", cmd, e)))?;

    Ok(output)
}

/// Execute command and check success
pub fn run_command_checked(cmd: &str, args: &[&str], cwd: Option<&Path>) -> Result<()> {
    let output = run_command(cmd, args, cwd)?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(CliError::CommandFailed(format!(
            "{} failed: {}",
            cmd,
            stderr.trim()
        )));
    }

    Ok(())
}

/// Execute command and return stdout as string
pub fn run_command_output(cmd: &str, args: &[&str], cwd: Option<&Path>) -> Result<String> {
    let output = run_command(cmd, args, cwd)?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(CliError::CommandFailed(format!(
            "{} failed: {}",
            cmd,
            stderr.trim()
        )));
    }

    let stdout = String::from_utf8(output.stdout)
        .map_err(|e| CliError::CommandOutput(format!("Invalid UTF-8 output: {}", e)))?;

    Ok(stdout.trim().to_string())
}

/// Execute command silently and return success status
pub fn run_command_silent(cmd: &str, args: &[&str], cwd: Option<&Path>) -> Result<()> {
    let output = run_command(cmd, args, cwd)?;

    if !output.status.success() {
        return Err(CliError::CommandFailed(format!(
            "{} exited with status {}",
            cmd, output.status
        )));
    }

    Ok(())
}

/// Execute command with live output streaming
pub fn run_command_streaming(cmd: &str, args: &[&str], cwd: Option<&Path>) -> Result<()> {
    let mut command = Command::new(cmd);
    command.args(args);

    if let Some(dir) = cwd {
        command.current_dir(dir);
    }

    // Inherit stdio for live output
    command.stdout(Stdio::inherit());
    command.stderr(Stdio::inherit());

    let status = command
        .status()
        .map_err(|e| CliError::CommandFailed(format!("Failed to execute {}: {}", cmd, e)))?;

    if !status.success() {
        return Err(CliError::CommandFailed(format!(
            "{} exited with status {}",
            cmd,
            status.code().unwrap_or(-1)
        )));
    }

    Ok(())
}

/// Check if command exists in PATH
pub fn command_exists(cmd: &str) -> bool {
    Command::new(cmd)
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok()
}

/// Get command version
pub fn get_command_version(cmd: &str) -> Result<String> {
    run_command_output(cmd, &["--version"], None)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_exists() {
        // These should exist on most systems
        assert!(command_exists("echo"));
        assert!(!command_exists("nonexistent_command_12345"));
    }

    #[test]
    fn test_run_command_output() {
        let output = run_command_output("echo", &["hello"], None).unwrap();
        assert_eq!(output, "hello");
    }
}
