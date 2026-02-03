//! Build artifact cleanup command
//!
//! Removes build artifacts and caches:
//! - Python: __pycache__, *.pyc files
//! - Node: Clean web and mobile builds
//! - Rust: cargo clean
//!
//! Optionally removes dependencies (node_modules) with --deps flag.

use colored::*;
use crate::utils::exec;

pub fn run(deps: bool) -> anyhow::Result<()> {
    println!("{}", "🧹 Cleaning build artifacts...".green().bold());

    // Clean Python
    println!("{}", "🐍 Cleaning Python...".cyan());
    exec::run_command(
        "find",
        &[
            ".",
            "-type",
            "d",
            "-name",
            "__pycache__",
            "-exec",
            "rm",
            "-rf",
            "{}",
            "+",
        ],
    )?;
    exec::run_command("find", &[".", "-type", "f", "-name", "*.pyc", "-delete"])?;

    // Clean Node
    println!("{}", "⚛️  Cleaning Node...".cyan());
    exec::run_command("pnpm", &["--filter", "web", "clean"])?;
    exec::run_command("pnpm", &["--filter", "mobile", "clean"])?;

    if deps {
        exec::run_command("rm", &["-rf", "node_modules"])?;
    }

    // Clean Rust
    println!("{}", "🦀 Cleaning Rust...".cyan());
    exec::run_command("cargo", &["clean"])?;

    println!("{}", "✅ Clean complete!".green().bold());
    Ok(())
}
