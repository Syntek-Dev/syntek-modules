//! Project build command
//!
//! Builds all projects for specified mode (dev or production):
//! - Web: Next.js build
//! - Mobile: React Native build
//! - Rust: Cargo build (with --release for production)
//!
//! Production builds include optimizations and are ready for deployment.

use crate::utils::exec;
use colored::*;

pub fn run(mode: crate::BuildMode) -> anyhow::Result<()> {
    println!("{}", "🔨 Building projects...".green().bold());

    // Build web
    println!("{}", "⚛️  Building web...".cyan());
    let args = match mode {
        crate::BuildMode::Dev => vec!["--filter", "web", "build:dev"],
        crate::BuildMode::Production => vec!["--filter", "web", "build"],
    };
    exec::run_command("pnpm", &args)?;

    // Build mobile
    println!("{}", "📱 Building mobile...".cyan());
    let args = match mode {
        crate::BuildMode::Dev => vec!["--filter", "mobile", "build:dev"],
        crate::BuildMode::Production => vec!["--filter", "mobile", "build"],
    };
    exec::run_command("pnpm", &args)?;

    // Build Rust
    println!("{}", "🦀 Building Rust...".cyan());
    let args = match mode {
        crate::BuildMode::Dev => vec!["build", "--workspace"],
        crate::BuildMode::Production => vec!["build", "--workspace", "--release"],
    };
    exec::run_command("cargo", &args)?;

    println!("{}", "✅ Build complete!".green().bold());
    Ok(())
}
