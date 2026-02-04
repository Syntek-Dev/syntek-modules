//! Validation command
//!
//! Runs comprehensive code validation including:
//! - Linting (style, security, best practices)
//! - Type checking (static type safety)
//!
//! This is the recommended command for CI/CD pipelines and pre-commit checks
//! as it ensures both code quality and type safety.

use colored::*;

pub fn run(fix: bool) -> anyhow::Result<()> {
    println!("{}", "🔍 Validating code...".green().bold());
    println!();

    // Run linting first
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".cyan());
    println!("{}", "  STEP 1: Linting".cyan().bold());
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".cyan());
    println!();

    if let Err(e) = super::lint::run(fix) {
        println!();
        println!("{}", "❌ Linting failed!".red().bold());
        return Err(e);
    }

    println!();
    println!();

    // Run type checking
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".cyan());
    println!("{}", "  STEP 2: Type Checking".cyan().bold());
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".cyan());
    println!();

    if let Err(e) = super::typecheck::run() {
        println!();
        println!("{}", "❌ Type checking failed!".red().bold());
        return Err(e);
    }

    println!();
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".green());
    println!("{}", "  ✅ ALL VALIDATION PASSED!".green().bold());
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".green());

    Ok(())
}
