//! Syntek Modules CLI
//!
//! A comprehensive command-line interface for managing the Syntek Modules monorepo.
//! This CLI provides commands for development, testing, building, deployment, and
//! maintenance across Python (Django), TypeScript (Next.js/React Native), and Rust ecosystems.
//!
//! # Commands
//!
//! - `dev` - Start development environment (Docker, Django, Next.js)
//! - `test` - Run test suite across all ecosystems
//! - `install` - Install dependencies (Python, Node, Rust)
//! - `init` - Initialize project (Git hooks, secrets, dev tools)
//! - `coverage` - Generate and manage code coverage reports
//! - `lint` - Lint code (Ruff, ESLint, Clippy)
//! - `typecheck` - Type check code (Pyright, tsc, cargo check)
//! - `validate` - Validate code (lint + typecheck combined)
//! - `format` - Format code (Ruff, Prettier, rustfmt)
//! - `build` - Build projects for development or production
//! - `clean` - Clean build artifacts and dependencies
//! - `audit` - Security audit across all package managers
//! - `staging` - Deploy to staging environment
//! - `production` - Deploy to production environment (with confirmation)
//!
//! # Architecture
//!
//! The CLI is organized into modules:
//! - `commands/` - Individual command implementations
//! - `utils/` - Shared utilities (exec, env, tools)
//!
//! This modular structure keeps the codebase maintainable and testable.

use clap::{Parser, Subcommand};
use std::path::PathBuf;

// Module declarations
mod commands;
mod utils;

#[derive(Parser)]
#[command(name = "syntek")]
#[command(about = "Syntek Modules CLI - Manage development, testing, and deployment", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Start development environment
    Dev {
        /// Environment file to use (default: .env.dev)
        #[arg(short, long, default_value = ".env.dev")]
        env: PathBuf,
    },

    /// Run test suite
    Test {
        /// Environment file to use (default: .env.test)
        #[arg(short, long, default_value = ".env.test")]
        env: PathBuf,

        /// Specific test module to run
        #[arg(short, long)]
        module: Option<String>,

        /// Run in watch mode
        #[arg(short, long)]
        watch: bool,
    },

    /// Deploy to staging
    Staging {
        /// Environment file to use (default: .env.staging)
        #[arg(short, long, default_value = ".env.staging")]
        env: PathBuf,
    },

    /// Deploy to production
    Production {
        /// Environment file to use (default: .env.production)
        #[arg(short, long, default_value = ".env.production")]
        env: PathBuf,

        /// Skip confirmation prompt (dangerous!)
        #[arg(long)]
        force: bool,
    },

    /// Install all dependencies
    Install {
        /// Install type
        #[arg(value_enum, default_value = "all")]
        target: InstallTarget,
    },

    /// Lint all code (style, security, best practices)
    Lint {
        /// Fix automatically where possible
        #[arg(short, long)]
        fix: bool,
    },

    /// Type check all code (static type safety)
    Typecheck,

    /// Validate all code (lint + typecheck)
    Validate {
        /// Fix linting issues automatically where possible
        #[arg(short, long)]
        fix: bool,
    },

    /// Format all code
    Format {
        /// Check formatting without modifying files
        #[arg(short, long)]
        check: bool,
    },

    /// Build all projects
    Build {
        /// Build mode
        #[arg(value_enum, default_value = "dev")]
        mode: BuildMode,
    },

    /// Clean build artifacts
    Clean {
        /// Also clean dependencies (node_modules, target, etc.)
        #[arg(long)]
        deps: bool,
    },

    /// Security audit - scan for vulnerabilities in all dependencies
    Audit {
        /// Output format (text, json, markdown)
        #[arg(short, long, value_enum, default_value = "text")]
        format: AuditFormat,

        /// Minimum severity level to report (low, moderate, high, critical)
        #[arg(short, long, default_value = "moderate")]
        severity: String,

        /// Generate a report file
        #[arg(short, long)]
        output: Option<PathBuf>,
    },

    /// Initialize project setup (Git hooks, secrets baseline, dev tools)
    Init {
        /// Skip pre-commit hooks setup
        #[arg(long)]
        skip_hooks: bool,

        /// Skip secrets baseline creation
        #[arg(long)]
        skip_secrets: bool,

        /// Skip dev tools installation
        #[arg(long)]
        skip_dev_tools: bool,
    },

    /// Generate and manage code coverage reports
    Coverage {
        /// Generate coverage baseline for comparison
        #[arg(long)]
        baseline: bool,

        /// Compare current coverage with baseline
        #[arg(long)]
        compare: bool,

        /// Output file for coverage report
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
}

#[derive(clap::ValueEnum, Clone)]
enum InstallTarget {
    All,
    Backend,
    Web,
    Mobile,
    Rust,
    Shared,
}

#[derive(clap::ValueEnum, Clone)]
enum BuildMode {
    Dev,
    Production,
}

#[derive(clap::ValueEnum, Clone)]
enum AuditFormat {
    Text,
    Json,
    Markdown,
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Dev { env } => commands::dev::run(env),
        Commands::Test { env, module, watch } => commands::test::run(env, module, watch),
        Commands::Staging { env } => commands::staging::run(env),
        Commands::Production { env, force } => commands::production::run(env, force),
        Commands::Install { target } => commands::install::run(target),
        Commands::Lint { fix } => commands::lint::run(fix),
        Commands::Typecheck => commands::typecheck::run(),
        Commands::Validate { fix } => commands::validate::run(fix),
        Commands::Format { check } => commands::format::run(check),
        Commands::Build { mode } => commands::build::run(mode),
        Commands::Clean { deps } => commands::clean::run(deps),
        Commands::Audit {
            format,
            severity,
            output,
        } => commands::audit::run(format, severity, output),
        Commands::Init {
            skip_hooks,
            skip_secrets,
            skip_dev_tools,
        } => commands::init::run(skip_hooks, skip_secrets, skip_dev_tools),
        Commands::Coverage {
            baseline,
            compare,
            output,
        } => commands::coverage::run(baseline, compare, output),
    }
}
