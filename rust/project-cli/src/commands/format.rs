//! Code formatting command
//!
//! Formats code across all ecosystems:
//! - Python: Ruff format (replaces black)
//! - TypeScript: Prettier for consistent formatting
//! - Rust: rustfmt for idiomatic Rust style
//!
//! Supports check mode to verify formatting without modifying files.

use colored::*;
use crate::utils::exec;

pub fn run(check: bool) -> anyhow::Result<()> {
    println!("{}", "✨ Formatting code...".green().bold());

    // Python (ruff)
    println!("{}", "🐍 Formatting Python...".cyan());
    let mut args = vec!["run", "ruff", "format"];
    if check {
        args.push("--check");
    }
    args.push(".");
    exec::run_command("uv", &args)?;

    // TypeScript (Prettier)
    println!("{}", "⚛️  Formatting TypeScript...".cyan());
    let mut args = vec!["--filter", "web", "format"];
    if check {
        args.push("--check");
    }
    exec::run_command("pnpm", &args)?;

    // Rust (rustfmt)
    println!("{}", "🦀 Formatting Rust...".cyan());
    let mut args = vec!["fmt", "--all"];
    if check {
        args.push("--check");
    }
    exec::run_command_in_dir("cargo", &args, "rust")?;

    println!("{}", "✅ Formatting complete!".green().bold());
    Ok(())
}
