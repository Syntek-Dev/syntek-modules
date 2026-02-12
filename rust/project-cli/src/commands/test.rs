//! Test suite command
//!
//! Runs tests across all ecosystems:
//! - Python: pytest for Django backend
//! - TypeScript: vitest for web frontend
//! - Rust: cargo test for Rust crates
//!
//! Supports filtering by module and watch mode for TDD workflow.

use crate::utils::{env, exec};
use colored::*;
use std::path::PathBuf;

/// Run the test suite across all ecosystems
///
/// # Arguments
///
/// * `env_file` - Path to test environment file (default: .env.test)
/// * `module` - Optional specific module to test
/// * `watch` - Enable watch mode for continuous testing
///
/// # Returns
///
/// * `Ok(())` if all tests pass
/// * `Err` if any test fails
pub fn run(env_file: PathBuf, module: Option<String>, watch: bool) -> anyhow::Result<()> {
    println!("{}", "🧪 Running test suite...".green().bold());

    env::load_env(&env_file)?;

    // Backend tests (pytest)
    println!("{}", "🐍 Running Python tests...".cyan());
    let mut args = vec!["run", "pytest"];
    if let Some(ref m) = module {
        args.push(m);
    }
    if watch {
        args.push("--watch");
    }
    exec::run_command("uv", &args)?;

    // Web tests (vitest)
    println!("{}", "⚛️  Running web tests...".cyan());
    let mut args = vec!["--filter", "web", "test"];
    if watch {
        args.push("--watch");
    }
    exec::run_command("pnpm", &args)?;

    // Rust tests
    println!("{}", "🦀 Running Rust tests...".cyan());
    exec::run_command_in_dir("cargo", &["test", "--workspace"], "rust")?;

    println!("{}", "✅ All tests passed!".green().bold());
    Ok(())
}
