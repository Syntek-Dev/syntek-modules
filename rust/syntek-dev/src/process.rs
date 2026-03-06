use anyhow::Result;
use std::path::Path;
use tokio::process::Command;

/// Run a command, inheriting the terminal's stdin/stdout/stderr.
/// Returns `true` if the process exits with code 0.
pub async fn run(program: &str, args: &[&str], cwd: &Path) -> Result<bool> {
    let status = Command::new(program)
        .args(args)
        .current_dir(cwd)
        .status()
        .await?;
    Ok(status.success())
}

/// Run a command with extra environment variables, inheriting stdio.
#[allow(dead_code)]
pub async fn run_env(
    program: &str,
    args: &[&str],
    cwd: &Path,
    env: &[(&str, &str)],
) -> Result<bool> {
    let mut cmd = Command::new(program);
    cmd.args(args).current_dir(cwd);
    for (k, v) in env {
        cmd.env(k, v);
    }
    let status = cmd.status().await?;
    Ok(status.success())
}

/// Spawn a background process, returning the child handle.
/// The caller is responsible for calling `child.kill().await`.
pub fn spawn(program: &str, args: &[&str], cwd: &Path) -> Result<tokio::process::Child> {
    Ok(Command::new(program)
        .args(args)
        .current_dir(cwd)
        .spawn()?)
}

/// Return true if the given executable exists on PATH.
pub fn exists(program: &str) -> bool {
    which::which(program).is_ok()
}
