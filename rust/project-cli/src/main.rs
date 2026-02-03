use clap::{Parser, Subcommand};
use colored::*;
use std::path::PathBuf;
use std::process::Command;

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

    /// Lint all code
    Lint {
        /// Fix automatically where possible
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

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Dev { env } => run_dev(env),
        Commands::Test { env, module, watch } => run_test(env, module, watch),
        Commands::Staging { env } => run_staging(env),
        Commands::Production { env, force } => run_production(env, force),
        Commands::Install { target } => run_install(target),
        Commands::Lint { fix } => run_lint(fix),
        Commands::Format { check } => run_format(check),
        Commands::Build { mode } => run_build(mode),
        Commands::Clean { deps } => run_clean(deps),
    }
}

fn run_dev(env: PathBuf) -> anyhow::Result<()> {
    println!(
        "{}",
        "🚀 Starting development environment...".green().bold()
    );

    // Load environment
    load_env(&env)?;

    // Start Docker services
    println!("{}", "📦 Starting Docker services...".cyan());
    run_command("docker-compose", &["up", "-d"])?;

    // Start backend (uv)
    println!("{}", "🐍 Starting Django backend...".cyan());
    run_command("uv", &["run", "python", "manage.py", "runserver"])?;

    // Start web frontend (pnpm)
    println!("{}", "⚛️  Starting Next.js frontend...".cyan());
    run_command("pnpm", &["--filter", "web", "dev"])?;

    println!("{}", "✅ Development environment ready!".green().bold());
    Ok(())
}

fn run_test(env: PathBuf, module: Option<String>, watch: bool) -> anyhow::Result<()> {
    println!("{}", "🧪 Running test suite...".green().bold());

    load_env(&env)?;

    // Backend tests (pytest)
    println!("{}", "🐍 Running Python tests...".cyan());
    let mut args = vec!["run", "pytest"];
    if let Some(ref m) = module {
        args.push(m);
    }
    if watch {
        args.push("--watch");
    }
    run_command("uv", &args)?;

    // Web tests (vitest)
    println!("{}", "⚛️  Running web tests...".cyan());
    let mut args = vec!["--filter", "web", "test"];
    if watch {
        args.push("--watch");
    }
    run_command("pnpm", &args)?;

    // Rust tests
    println!("{}", "🦀 Running Rust tests...".cyan());
    run_command_in_dir("cargo", &["test", "--workspace"], "rust")?;

    println!("{}", "✅ All tests passed!".green().bold());
    Ok(())
}

fn run_staging(env: PathBuf) -> anyhow::Result<()> {
    println!("{}", "🚢 Deploying to staging...".yellow().bold());

    load_env(&env)?;

    // Build all projects
    println!("{}", "📦 Building projects...".cyan());
    run_build(BuildMode::Production)?;

    // Deploy logic here (placeholder)
    println!("{}", "🚀 Deploying to staging servers...".cyan());
    println!("{}", "   (Deployment logic to be implemented)".dimmed());

    println!("{}", "✅ Staging deployment complete!".green().bold());
    Ok(())
}

fn run_production(env: PathBuf, force: bool) -> anyhow::Result<()> {
    if !force {
        println!("{}", "⚠️  PRODUCTION DEPLOYMENT".red().bold());
        println!("{}", "This will deploy to production servers.".yellow());
        print!("Are you sure? [y/N]: ");

        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;

        if !input.trim().eq_ignore_ascii_case("y") {
            println!("{}", "❌ Deployment cancelled.".red());
            return Ok(());
        }
    }

    println!("{}", "🚀 Deploying to production...".red().bold());

    load_env(&env)?;

    // Build all projects
    println!("{}", "📦 Building projects...".cyan());
    run_build(BuildMode::Production)?;

    // Deploy logic here (placeholder)
    println!("{}", "🚀 Deploying to production servers...".cyan());
    println!("{}", "   (Deployment logic to be implemented)".dimmed());

    println!("{}", "✅ Production deployment complete!".green().bold());
    Ok(())
}

fn run_install(target: InstallTarget) -> anyhow::Result<()> {
    println!("{}", "📦 Installing dependencies...".green().bold());

    match target {
        InstallTarget::All => {
            install_backend()?;
            install_pnpm_workspace()?;
            install_rust()?;
        }
        InstallTarget::Backend => install_backend()?,
        InstallTarget::Web | InstallTarget::Mobile | InstallTarget::Shared => {
            install_pnpm_workspace()?;
        }
        InstallTarget::Rust => install_rust()?,
    }

    println!("{}", "✅ Dependencies installed!".green().bold());
    Ok(())
}

fn install_backend() -> anyhow::Result<()> {
    println!("{}", "🐍 Installing Python dependencies...".cyan());
    run_command("uv", &["sync"])?;
    Ok(())
}

fn install_pnpm_workspace() -> anyhow::Result<()> {
    println!(
        "{}",
        "📦 Installing pnpm workspace (web/mobile/shared)...".cyan()
    );
    run_command("pnpm", &["install"])?;
    Ok(())
}

fn install_rust() -> anyhow::Result<()> {
    println!("{}", "🦀 Building Rust crates...".cyan());
    run_command_in_dir("cargo", &["build", "--workspace"], "rust")?;
    Ok(())
}

fn run_lint(fix: bool) -> anyhow::Result<()> {
    println!("{}", "🔍 Linting code...".green().bold());

    // Python (ruff)
    println!("{}", "🐍 Linting Python...".cyan());
    let mut args = vec!["run", "ruff", "check", "."];
    if fix {
        args.push("--fix");
    }
    run_command("uv", &args)?;

    // TypeScript (ESLint)
    println!("{}", "⚛️  Linting TypeScript...".cyan());
    let mut args = vec!["--filter", "web", "lint"];
    if fix {
        args.push("--fix");
    }
    run_command("pnpm", &args)?;

    // Rust (clippy)
    println!("{}", "🦀 Linting Rust...".cyan());
    let mut args = vec!["clippy", "--workspace", "--all-targets"];
    if fix {
        args.push("--fix");
        args.push("--allow-dirty");
    }
    run_command_in_dir("cargo", &args, "rust")?;

    println!("{}", "✅ Linting complete!".green().bold());
    Ok(())
}

fn run_format(check: bool) -> anyhow::Result<()> {
    println!("{}", "✨ Formatting code...".green().bold());

    // Python (ruff)
    println!("{}", "🐍 Formatting Python...".cyan());
    let mut args = vec!["run", "ruff", "format"];
    if check {
        args.push("--check");
    }
    args.push(".");
    run_command("uv", &args)?;

    // TypeScript (Prettier)
    println!("{}", "⚛️  Formatting TypeScript...".cyan());
    let mut args = vec!["--filter", "web", "format"];
    if check {
        args.push("--check");
    }
    run_command("pnpm", &args)?;

    // Rust (rustfmt)
    println!("{}", "🦀 Formatting Rust...".cyan());
    let mut args = vec!["fmt", "--all"];
    if check {
        args.push("--check");
    }
    run_command_in_dir("cargo", &args, "rust")?;

    println!("{}", "✅ Formatting complete!".green().bold());
    Ok(())
}

fn run_build(mode: BuildMode) -> anyhow::Result<()> {
    println!("{}", "🔨 Building projects...".green().bold());

    // Build web
    println!("{}", "⚛️  Building web...".cyan());
    let args = match mode {
        BuildMode::Dev => vec!["--filter", "web", "build:dev"],
        BuildMode::Production => vec!["--filter", "web", "build"],
    };
    run_command("pnpm", &args)?;

    // Build mobile
    println!("{}", "📱 Building mobile...".cyan());
    let args = match mode {
        BuildMode::Dev => vec!["--filter", "mobile", "build:dev"],
        BuildMode::Production => vec!["--filter", "mobile", "build"],
    };
    run_command("pnpm", &args)?;

    // Build Rust
    println!("{}", "🦀 Building Rust...".cyan());
    let args = match mode {
        BuildMode::Dev => vec!["build", "--workspace"],
        BuildMode::Production => vec!["build", "--workspace", "--release"],
    };
    run_command("cargo", &args)?;

    println!("{}", "✅ Build complete!".green().bold());
    Ok(())
}

fn run_clean(deps: bool) -> anyhow::Result<()> {
    println!("{}", "🧹 Cleaning build artifacts...".green().bold());

    // Clean Python
    println!("{}", "🐍 Cleaning Python...".cyan());
    run_command(
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
    run_command("find", &[".", "-type", "f", "-name", "*.pyc", "-delete"])?;

    // Clean Node
    println!("{}", "⚛️  Cleaning Node...".cyan());
    run_command("pnpm", &["--filter", "web", "clean"])?;
    run_command("pnpm", &["--filter", "mobile", "clean"])?;

    if deps {
        run_command("rm", &["-rf", "node_modules"])?;
    }

    // Clean Rust
    println!("{}", "🦀 Cleaning Rust...".cyan());
    run_command("cargo", &["clean"])?;

    println!("{}", "✅ Clean complete!".green().bold());
    Ok(())
}

fn load_env(env_file: &PathBuf) -> anyhow::Result<()> {
    if env_file.exists() {
        dotenvy::from_path(env_file)?;
        println!(
            "{} {}",
            "📝 Loaded environment:".dimmed(),
            env_file.display().to_string().cyan()
        );
    } else {
        println!(
            "{} {}",
            "⚠️  Environment file not found:".yellow(),
            env_file.display()
        );
        println!("{}", "   Continuing without environment file...".dimmed());
    }
    Ok(())
}

fn run_command(cmd: &str, args: &[&str]) -> anyhow::Result<()> {
    let status = Command::new(cmd).args(args).status()?;

    if !status.success() {
        anyhow::bail!("Command failed: {} {}", cmd, args.join(" "));
    }

    Ok(())
}

fn run_command_in_dir(cmd: &str, args: &[&str], dir: &str) -> anyhow::Result<()> {
    let status = Command::new(cmd).args(args).current_dir(dir).status()?;

    if !status.success() {
        anyhow::bail!("Command failed: {} {} (in {})", cmd, args.join(" "), dir);
    }

    Ok(())
}
