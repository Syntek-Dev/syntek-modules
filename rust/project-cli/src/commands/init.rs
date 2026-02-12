//! Project initialization command
//!
//! This module handles the `syntek init` command which sets up a development
//! environment for the Syntek Modules repository. It performs the following tasks:
//!
//! 1. Verifies required tools are installed (uv, git, node, pnpm, cargo)
//! 2. Ensures Python virtual environment exists
//! 3. Installs Python development tools (pytest, pre-commit, detect-secrets)
//! 4. Installs Rust components (rustfmt, clippy)
//! 5. Installs Node dependencies (including pyright)
//! 6. Sets up Git pre-commit hooks
//! 7. Creates secrets baseline for secret scanning
//!
//! Each step can be skipped via command-line flags for CI/CD environments.

use crate::utils::tools;
use colored::*;

/// Run the init command to set up the development environment
///
/// # Arguments
///
/// * `skip_hooks` - Skip Git hooks installation
/// * `skip_secrets` - Skip secrets baseline creation
/// * `skip_dev_tools` - Skip development tools installation
///
/// # Returns
///
/// * `Ok(())` if initialization succeeds
/// * `Err` if any step fails (missing tools, installation failure, etc.)
pub fn run(skip_hooks: bool, skip_secrets: bool, skip_dev_tools: bool) -> anyhow::Result<()> {
    println!("{}", "🚀 Initializing project setup...".green().bold());
    println!();

    // Step 1: Check for required tools
    println!("{}", "🔍 Checking required tools...".cyan());
    check_required_tools()?;
    println!();

    // Step 2: Ensure venv exists
    println!("{}", "🐍 Ensuring Python virtual environment...".cyan());
    tools::ensure_venv_exists()?;
    println!();

    // Step 3: Install dev tools (unless skipped)
    if !skip_dev_tools {
        println!("{}", "📦 Installing development tools...".cyan());
        tools::install_python_dev_tools()?;
        tools::install_rust_components()?;
        tools::install_node_dependencies()?;
        println!();
    } else {
        println!("{}", "⏭️  Skipping dev tools installation".yellow());
        println!();
    }

    // Step 4: Setup Git hooks (unless skipped)
    if !skip_hooks {
        println!("{}", "🪝 Setting up Git hooks...".cyan());
        tools::setup_git_hooks()?;
        println!();
    } else {
        println!("{}", "⏭️  Skipping Git hooks setup".yellow());
        println!();
    }

    // Step 5: Create secrets baseline (unless skipped)
    if !skip_secrets {
        println!("{}", "🔒 Creating secrets baseline...".cyan());
        tools::create_secrets_baseline()?;
        println!();
    } else {
        println!("{}", "⏭️  Skipping secrets baseline creation".yellow());
        println!();
    }

    // Step 6: Final message
    println!("{}", "━".repeat(60).dimmed());
    println!("{}", "✅ Project initialization complete!".green().bold());
    println!();
    println!("{}", "Next steps:".cyan().bold());
    println!(
        "{}",
        "  1. Review .secrets.baseline for false positives".dimmed()
    );
    println!("{}", "  2. Run 'syntek dev' to start development".dimmed());
    println!("{}", "  3. Make a commit to test pre-commit hooks".dimmed());
    println!("{}", "━".repeat(60).dimmed());

    Ok(())
}

fn check_required_tools() -> anyhow::Result<()> {
    let tools_list = vec![
        ("uv", "Python package manager"),
        ("git", "Version control"),
        ("node", "JavaScript runtime"),
        ("pnpm", "Node package manager"),
        ("cargo", "Rust build tool"),
    ];

    let mut all_found = true;

    for (tool, description) in tools_list {
        if tools::check_tool_installed(tool) {
            println!("   {} {} ({})", "✓".green(), tool, description.dimmed());
        } else {
            println!(
                "   {} {} ({}) - not found",
                "✗".red(),
                tool,
                description.dimmed()
            );
            all_found = false;
        }
    }

    if !all_found {
        anyhow::bail!("Some required tools are missing. Please install them and try again.");
    }

    Ok(())
}
