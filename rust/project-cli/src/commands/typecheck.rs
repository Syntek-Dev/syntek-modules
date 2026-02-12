//! Type checking command
//!
//! Runs type checkers across all ecosystems:
//! - Python: Pyright for static type checking
//! - TypeScript: tsc (TypeScript compiler) for type checking
//! - Rust: cargo check for type validation
//!
//! This command focuses exclusively on type safety without running linters.

use crate::utils::exec;
use colored::*;

pub fn run() -> anyhow::Result<()> {
    println!("{}", "🔍 Type checking code...".green().bold());

    let mut has_errors = false;

    // Python type checking (pyright)
    println!("{}", "🐍 Type checking Python...".cyan());
    let args = vec!["run", "pyright", "backend/", "graphql/"];
    match exec::run_command("uv", &args) {
        Ok(_) => println!("{}", "  ✓ Python types OK".green()),
        Err(_) => {
            println!("{}", "  ✗ Python type errors found".red());
            has_errors = true;
        }
    }

    // TypeScript type checking
    println!("{}", "⚛️  Type checking TypeScript...".cyan());
    let args = vec!["--filter", "web", "typecheck"];
    match exec::run_command("pnpm", &args) {
        Ok(_) => println!("{}", "  ✓ TypeScript types OK".green()),
        Err(_) => {
            println!("{}", "  ✗ TypeScript type errors found".red());
            has_errors = true;
        }
    }

    // Rust type checking (cargo check)
    println!("{}", "🦀 Type checking Rust...".cyan());
    let args = vec!["check", "--workspace", "--all-targets"];
    match exec::run_command_in_dir("cargo", &args, "rust") {
        Ok(_) => println!("{}", "  ✓ Rust types OK".green()),
        Err(_) => {
            println!("{}", "  ✗ Rust type errors found".red());
            has_errors = true;
        }
    }

    if has_errors {
        println!("{}", "❌ Type checking failed!".red().bold());
        std::process::exit(1);
    } else {
        println!("{}", "✅ Type checking complete!".green().bold());
    }

    Ok(())
}
