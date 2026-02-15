//! Syntek CLI main entry point
//!
//! Command-line interface for installing and managing Syntek modules.

use clap::{Parser, Subcommand};
use colored::Colorize;
use std::process;
use syntek_cli::commands::{init, install, verify, InitArgs, InstallArgs, VerifyArgs};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Syntek CLI - Install and manage Syntek modules
#[derive(Debug, Parser)]
#[command(name = "syntek")]
#[command(version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Enable verbose logging
    #[arg(short, long, global = true)]
    verbose: bool,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Initialize Syntek in a project
    Init(InitArgs),

    /// Install Syntek modules
    Install(InstallArgs),

    /// Verify Syntek installation
    Verify(VerifyArgs),
}

fn main() {
    // Parse command-line arguments
    let cli = Cli::parse();

    // Initialize logging
    init_logging(cli.verbose);

    // Set up graceful shutdown handler
    setup_shutdown_handler();

    // Execute command
    let result = match cli.command {
        Commands::Init(args) => init(args),
        Commands::Install(args) => install(args),
        Commands::Verify(args) => verify(args),
    };

    // Handle result
    match result {
        Ok(_) => {
            process::exit(0);
        }
        Err(e) => {
            eprintln!("\n{} {}", "Error:".red().bold(), e);

            // Print suggestions based on error type
            print_error_suggestions(&e);

            process::exit(1);
        }
    }
}

/// Initialize logging based on verbosity
fn init_logging(verbose: bool) {
    let env_filter = if verbose {
        tracing_subscriber::EnvFilter::new("syntek_cli=debug")
    } else {
        tracing_subscriber::EnvFilter::new("syntek_cli=info")
    };

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer())
        .init();
}

/// Set up graceful shutdown handler
fn setup_shutdown_handler() {
    ctrlc::set_handler(move || {
        println!("\n\n{}", "Interrupted. Cleaning up...".yellow());
        process::exit(130); // Standard exit code for SIGINT
    })
    .expect("Error setting Ctrl-C handler");
}

/// Print helpful suggestions based on error type
fn print_error_suggestions(error: &syntek_cli::CliError) {
    use syntek_cli::CliError;

    match error {
        CliError::ConfigNotFound(_) => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!("  Run {} to initialize Syntek in this project", "syntek init".cyan());
        }
        CliError::PackageNotFound(pkg) => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!(
                "  Ensure syntek-modules repository is accessible and contains {}",
                pkg.cyan()
            );
            eprintln!(
                "  Use {} to specify the path",
                "--syntek-modules-path /path/to/syntek-modules".cyan()
            );
        }
        CliError::MissingDependency(dep, module) => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!("  Install {} required by {}", dep.cyan(), module.cyan());
        }
        CliError::AlreadyInstalled(path) => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!(
                "  Use {} to overwrite existing configuration at {}",
                "--force".cyan(),
                path.display()
            );
        }
        CliError::CommandFailed(cmd) => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!("  Ensure {} is installed and available in PATH", cmd.cyan());
        }
        CliError::ValidationFailed(msg) if msg.contains("package.json") => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!(
                "  Run {} in the appropriate directory to initialize",
                "npm init".cyan()
            );
        }
        CliError::ValidationFailed(msg) if msg.contains("import") => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!("  Run {} to verify installation", "syntek verify auth".cyan());
            eprintln!("  Check Python/Node.js dependencies are installed");
        }
        CliError::InsecurePermissions {
            path,
            mode: _mode,
            recommended,
        } => {
            eprintln!("\n{}", "Suggestion:".yellow().bold());
            eprintln!(
                "  Fix permissions: {}",
                format!("chmod {:o} {:?}", recommended, path).cyan()
            );
        }
        _ => {
            eprintln!("\n{}", "For more help:".yellow().bold());
            eprintln!("  Run {} for command help", "syntek --help".cyan());
            eprintln!(
                "  See documentation at {}",
                "docs/authentication/".cyan()
            );
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cli_parsing() {
        let cli = Cli::parse_from(["syntek", "init", "--name", "test-project"]);
        assert!(matches!(cli.command, Commands::Init(_)));
    }

    #[test]
    fn test_install_command_parsing() {
        let cli = Cli::parse_from(["syntek", "install", "auth", "--full"]);
        assert!(matches!(cli.command, Commands::Install(_)));
    }

    #[test]
    fn test_verify_command_parsing() {
        let cli = Cli::parse_from(["syntek", "verify", "auth"]);
        assert!(matches!(cli.command, Commands::Verify(_)));
    }
}
