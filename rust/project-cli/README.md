# Syntek CLI

A Rust-based command-line tool for managing the Syntek Modules development, testing, and deployment workflow.

## Installation

> **Note:** You must install the CLI first (bootstrap) before you can use any `syntek` commands.

### Quick Install (Recommended)

From the repository root:

```bash
./install-cli.sh
```

### Manual Installation

```bash
cd rust/project-cli
cargo build --release
cargo install --path .
```

The `syntek` binary will be installed to `~/.cargo/bin/syntek`.

### Verify Installation

Ensure `~/.cargo/bin` is in your PATH:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

Then verify:

```bash
syntek --help
```

### First-Time Setup

After installing the CLI, run:

```bash
syntek install  # Install all dependencies
syntek init     # Setup Git hooks, secrets, dev tools
```

## Usage

```bash
syntek --help
```

### Development

Start the development environment (Docker, Django backend, Next.js frontend):

```bash
syntek dev
```

With custom environment file:

```bash
syntek dev --env .env.custom
```

### Testing

Run all tests:

```bash
syntek test
```

Run specific module:

```bash
syntek test --module backend/security-core
```

Watch mode:

```bash
syntek test --watch
```

### Deployment

Deploy to staging:

```bash
syntek staging
```

Deploy to production (with confirmation prompt):

```bash
syntek production
```

Force production deployment (skip confirmation):

```bash
syntek production --force
```

### Installation & Setup

Install all dependencies:

```bash
syntek install
```

Install specific target:

```bash
syntek install backend
syntek install web
syntek install mobile
syntek install rust
syntek install shared
```

Initialize project setup (Git hooks, secrets baseline, dev tools):

```bash
syntek init
```

This will:

- Check for required tools (uv, git, node, pnpm, cargo)
- Ensure Python virtual environment exists
- Install Python dev tools (pre-commit, detect-secrets, pytest, pytest-bdd)
- Install Rust components (rustfmt, clippy)
- Install Node dependencies (including pyright for Python type checking)
- Setup pre-commit Git hooks
- Create `.secrets.baseline` for secret scanning

Skip specific initialization steps:

```bash
syntek init --skip-hooks      # Skip Git hooks setup
syntek init --skip-secrets    # Skip secrets baseline creation
syntek init --skip-dev-tools  # Skip dev tools installation
```

> **Note:** `syntek init` replaces the deprecated `scripts/setup-pre-commit.sh` script with a cross-platform Rust implementation.

### Code Quality

Lint all code:

```bash
syntek lint
```

Lint and auto-fix:

```bash
syntek lint --fix
```

Format all code:

```bash
syntek format
```

Check formatting without modifying:

```bash
syntek format --check
```

### Building

Build for development:

```bash
syntek build --mode dev
```

Build for production:

```bash
syntek build --mode production
```

### Cleaning

Clean build artifacts:

```bash
syntek clean
```

Also clean dependencies (node_modules, target, etc.):

```bash
syntek clean --deps
```

### Security Auditing

Run security audits across all ecosystems:

```bash
syntek audit
```

With custom severity level:

```bash
syntek audit --severity high
```

Generate a report:

```bash
syntek audit --output audit-report.md --format markdown
```

Available formats:

- `text` - Plain text output (default)
- `json` - JSON format for tooling integration
- `markdown` - Markdown format for documentation

The audit command checks:

- **NPM/pnpm packages** - Using `pnpm audit`
- **Python packages** - Using `pip-audit`
- **Rust crates** - Using `cargo-audit`

### Coverage Management

Generate and manage code coverage reports:

```bash
# Generate coverage report
syntek coverage

# Generate baseline for CI/CD comparison
syntek coverage --baseline

# Compare current coverage with baseline
syntek coverage --compare

# Custom output file
syntek coverage --output my-coverage.json
```

Workflow:

1. Generate baseline: `syntek coverage --baseline`
2. Save baseline: `mv coverage.json coverage-baseline.json`
3. Compare in CI/CD: `syntek coverage --compare`
4. View HTML report: `open htmlcov/index.html`

See `docs/GUIDES/COVERAGE-AND-CLI-REFACTOR.md` for details.

## Environment Files

The CLI respects the standard environment files:

- `.env.dev` - Development environment
- `.env.test` - Test environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment

Environment files are loaded automatically based on the command.

## Architecture

The CLI is built with:

- **clap** - Command-line argument parsing
- **colored** - Terminal output coloring
- **tokio** - Async runtime for process management
- **dotenvy** - Environment file loading
- **anyhow** - Error handling

## Development

Run the CLI in development mode:

```bash
cargo run -- dev
cargo run -- test
cargo run -- lint --fix
```

Run tests:

```bash
cargo test
```

## Integration

The CLI integrates with:

- **uv** - Python dependency management
- **pnpm** - Node.js package management
- **cargo** - Rust build system
- **docker-compose** - Container orchestration
- **pytest** - Python testing
- **vitest** - TypeScript testing
- **ruff** - Python linting and formatting
- **ESLint/Prettier** - TypeScript linting and formatting
- **clippy/rustfmt** - Rust linting and formatting

## Future Enhancements

- [ ] Parallel execution of independent tasks
- [ ] Progress bars for long-running operations
- [ ] Health checks before deployment
- [ ] Rollback functionality
- [ ] Environment variable validation
- [ ] Database migration management
- [ ] Log aggregation and viewing
- [ ] Performance profiling
- [ ] Security scanning integration
- [ ] Deployment to cloud providers (AWS, Digital Ocean, etc.)
