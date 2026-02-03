# Syntek CLI

A Rust-based command-line tool for managing the Syntek Modules development, testing, and deployment workflow.

## Installation

### Build from Source

```bash
cd rust/project-cli
cargo build --release
cargo install --path .
```

The `syntek` binary will be installed to `~/.cargo/bin/syntek`.

### Add to PATH

Ensure `~/.cargo/bin` is in your PATH:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
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

### Installation

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
