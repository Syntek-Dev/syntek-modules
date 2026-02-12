//! Development environment command
//!
//! Starts the complete development stack including:
//! - Docker services (PostgreSQL, Redis)
//! - Django backend (via uv)
//! - Next.js web frontend (via pnpm)
//!
//! This command loads environment variables from .env.dev (or custom file)
//! and starts all services in the correct order.

use crate::utils::{env, exec};
use colored::*;
use std::path::PathBuf;

/// Run the development environment
///
/// # Arguments
///
/// * `env_file` - Path to environment file (default: .env.dev)
///
/// # Returns
///
/// * `Ok(())` if all services start successfully
/// * `Err` if any service fails to start
pub fn run(env_file: PathBuf) -> anyhow::Result<()> {
    println!(
        "{}",
        "🚀 Starting development environment...".green().bold()
    );

    env::load_env(&env_file)?;

    println!("{}", "📦 Starting Docker services...".cyan());
    exec::run_command("docker-compose", &["up", "-d"])?;

    println!("{}", "🐍 Starting Django backend...".cyan());
    exec::run_command("uv", &["run", "python", "manage.py", "runserver"])?;

    println!("{}", "⚛️  Starting Next.js frontend...".cyan());
    exec::run_command("pnpm", &["--filter", "web", "dev"])?;

    println!("{}", "✅ Development environment ready!".green().bold());
    Ok(())
}
