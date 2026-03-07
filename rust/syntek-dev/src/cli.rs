use clap::{Args, Parser, Subcommand, ValueEnum};

#[derive(Parser)]
#[command(
    name = "syntek-dev",
    about = "Syntek development CLI — manage services, tests, linting, and the database",
    version,
    propagate_version = true
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Start development services (frontend watch, Storybook, Rust watcher)
    Up(UpArgs),

    /// Run the test suite
    Test(TestArgs),

    /// Run linting and type checking
    Lint(LintArgs),

    /// Format code across all layers
    Format(FormatArgs),

    /// Database management (migrate, seed, reset, shell)
    Db {
        #[command(subcommand)]
        command: DbCommand,
    },

    /// Quick quality check — lint + type-check only, no tests
    Check(LintArgs),

    /// Run the full CI pipeline locally (format check, lint, type-check, test)
    Ci,

    /// Open a local service in the browser
    Open(OpenArgs),
}

// ---------------------------------------------------------------------------
// Up
// ---------------------------------------------------------------------------

#[derive(Args)]
pub struct UpArgs {
    /// Start frontend packages in watch mode via Turborepo (pnpm dev)
    #[arg(long)]
    pub frontend: bool,

    /// Start Storybook for @syntek/ui (port 6006)
    #[arg(long)]
    pub storybook: bool,

    /// Start Rust file watcher (requires cargo-watch)
    #[arg(long)]
    pub rust: bool,
}

// ---------------------------------------------------------------------------
// Test
// ---------------------------------------------------------------------------

#[derive(Args)]
pub struct TestArgs {
    /// Run Python / Django tests (pytest)
    #[arg(long)]
    pub python: bool,

    /// Specific backend package, e.g. syntek-auth
    #[arg(long, value_name = "PACKAGE")]
    pub python_package: Option<String>,

    /// Run Rust tests (cargo test)
    #[arg(long)]
    pub rust: bool,

    /// Run TypeScript / web tests (Vitest)
    #[arg(long)]
    pub web: bool,

    /// Specific web package, e.g. @syntek/ui-auth
    #[arg(long, value_name = "PACKAGE")]
    pub web_package: Option<String>,

    /// Run mobile tests (Jest + RNTL)
    #[arg(long)]
    pub mobile: bool,

    /// Run E2E tests (Playwright)
    #[arg(long)]
    pub e2e: bool,

    /// pytest marker filter: unit | integration | e2e | slow
    #[arg(short = 'm', value_name = "MARKER")]
    pub marker: Option<String>,

    /// pytest / vitest keyword / pattern filter
    #[arg(short = 'k', value_name = "PATTERN")]
    pub pattern: Option<String>,

    /// Run in watch mode (web and mobile only)
    #[arg(long)]
    pub watch: bool,

    /// Generate coverage reports
    #[arg(long)]
    pub coverage: bool,
}

// ---------------------------------------------------------------------------
// Lint
// ---------------------------------------------------------------------------

#[derive(Args, Clone)]
pub struct LintArgs {
    /// Run ruff lint (Python)
    #[arg(long)]
    pub ruff: bool,

    /// Run basedpyright type checking (Python)
    #[arg(long)]
    pub pyright: bool,

    /// Run ESLint (TypeScript / JS)
    #[arg(long)]
    pub eslint: bool,

    /// Run clippy (Rust)
    #[arg(long)]
    pub clippy: bool,

    /// Run markdownlint
    #[arg(long)]
    pub markdown: bool,

    /// Auto-fix where possible (ruff --fix, eslint --fix)
    #[arg(long)]
    pub fix: bool,

    /// Restrict to a specific backend package, e.g. syntek-auth
    #[arg(value_name = "PACKAGE")]
    pub package: Option<String>,
}

// ---------------------------------------------------------------------------
// Format
// ---------------------------------------------------------------------------

#[derive(Args)]
pub struct FormatArgs {
    /// Format Python (ruff format)
    #[arg(long)]
    pub python: bool,

    /// Format TypeScript / JS / JSON / YAML / Markdown (prettier)
    #[arg(long)]
    pub ts: bool,

    /// Format Rust (cargo fmt)
    #[arg(long)]
    pub rust: bool,

    /// Check only — do not write files
    #[arg(long)]
    pub check: bool,
}

// ---------------------------------------------------------------------------
// Db
// ---------------------------------------------------------------------------

#[derive(Subcommand)]
pub enum DbCommand {
    /// Apply pending migrations (all modules or a specific one)
    Migrate {
        /// Module name, e.g. syntek-auth. Omit to run all.
        module: Option<String>,
    },

    /// Create new migrations for a module
    Makemigrations {
        /// Module name, e.g. syntek-auth
        module: Option<String>,
    },

    /// Roll back migrations to a target
    Rollback {
        /// Module name
        module: Option<String>,
        /// Target migration, e.g. 0003 or zero
        #[arg(long, default_value = "zero")]
        to: String,
    },

    /// Show migration status for all modules (or a specific one)
    Status {
        /// Module name
        module: Option<String>,
    },

    /// Seed the database with development mock data
    Seed,

    /// Seed the database with test-specific mock data
    SeedTest {
        /// Named scenario, e.g. payments or auth-mfa
        scenario: Option<String>,
    },

    /// Drop and recreate the test database, then run migrations
    Reset,

    /// Open a psql shell to the local database
    Shell,
}

// ---------------------------------------------------------------------------
// Open
// ---------------------------------------------------------------------------

#[derive(Args)]
pub struct OpenArgs {
    /// Service to open in the browser
    #[arg(value_enum)]
    pub target: OpenTarget,
}

#[derive(ValueEnum, Clone)]
pub enum OpenTarget {
    /// GraphQL playground at http://localhost:8000/graphql
    Api,
    /// Frontend dev server at http://localhost:3000
    Frontend,
    /// Storybook at http://localhost:6006
    Storybook,
    /// Django admin at http://localhost:8000/admin
    Admin,
}
