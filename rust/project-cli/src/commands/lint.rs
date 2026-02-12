//! Code linting command
//!
//! Runs linters across all ecosystems:
//! - Python: Ruff for fast linting
//! - TypeScript: ESLint for JS/TS/React
//! - Rust: Clippy for Rust code
//!
//! Supports auto-fix mode to automatically resolve fixable issues.

use crate::utils::exec;
use colored::*;

pub fn run(fix: bool) -> anyhow::Result<()> {
    println!("{}", "🔍 Linting code...".green().bold());

    // Python (ruff)
    println!("{}", "🐍 Linting Python...".cyan());
    let mut args = vec!["run", "ruff", "check", "."];
    if fix {
        args.push("--fix");
    }
    exec::run_command("uv", &args)?;

    // TypeScript (ESLint)
    println!("{}", "⚛️  Linting TypeScript...".cyan());
    let mut args = vec!["--filter", "web", "lint"];
    if fix {
        args.push("--fix");
    }
    exec::run_command("pnpm", &args)?;

    // Rust (clippy)
    println!("{}", "🦀 Linting Rust...".cyan());
    let mut args = vec!["clippy", "--workspace", "--all-targets"];
    if fix {
        args.push("--fix");
        args.push("--allow-dirty");
    }
    exec::run_command_in_dir("cargo", &args, "rust")?;

    println!("{}", "✅ Linting complete!".green().bold());
    Ok(())
}
