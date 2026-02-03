# Syntek Modules - Quick Start Guide

Get up and running with the Syntek Modules repository in minutes.

---

## Prerequisites

Ensure you have the following installed:

- **Python 3.14** (via pyenv, uv, or system package manager)
- **Node.js 24.13** (via nvm, fnm, or system package manager)
- **Rust 1.92.0** (via rustup)
- **pnpm 9+** (via npm or standalone installer)
- **uv** (Python package manager)
- **Docker & Docker Compose** (for local services)

---

## 1. Clone the Repository

```bash
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules
```

---

## 2. Install the Rust CLI Tool (Bootstrap)

The Syntek CLI (`syntek`) is a Rust-based tool that replaces traditional shell scripts. **You must install the CLI first** before you can use `syntek` commands.

### Quick Install (Recommended)

```bash
chmod +x install-cli.sh
./install-cli.sh
```

### Manual Install

```bash
cd rust/project-cli
cargo install --path .
cd ../..
```

### Verify Installation

```bash
syntek --help
```

Expected output:

```
Syntek Modules CLI - Manage development, testing, and deployment

Usage: syntek <COMMAND>

Commands:
  dev         Start development environment
  test        Run test suite
  staging     Deploy to staging
  production  Deploy to production
  install     Install all dependencies
  init        Initialize project setup (Git hooks, secrets baseline, dev tools)
  lint        Lint all code
  format      Format all code
  build       Build all projects
  clean       Clean build artifacts
  audit       Security audit
  help        Print this message or the help of the given subcommand(s)
```

---

## 3. Install All Dependencies

Use the Rust CLI to install all dependencies at once:

```bash
syntek install
```

This will:

- Install Python dependencies with `uv` (creates venv automatically)
- Install Node.js dependencies with `pnpm`
- Build Rust crates
- Generate lock files

**Alternatively, install manually:**

```bash
# Python
uv sync

# Node.js (web, mobile, shared)
pnpm install

# Rust
cd rust && cargo build && cd ..
```

---

## 4. Initialize Project Setup

Set up Git hooks, secrets baseline, and development tools:

```bash
syntek init
```

This will:

- Check for required tools (uv, git, node, pnpm, cargo)
- Ensure Python virtual environment exists
- Install Python dev tools:
  - `pre-commit` - Git hooks framework
  - `detect-secrets` - Secret scanning
  - `pytest` - Testing framework (TDD)
  - `pytest-bdd` - BDD support (Gherkin scenarios)
  - `pytest-cov` - Coverage reporting
  - `pytest-django` - Django integration
- Install Rust components (rustfmt, clippy)
- Install Node dependencies (including `pyright` for Python type checking)
- Setup pre-commit Git hooks
- Create `.secrets.baseline` for secret scanning

**Optional: Skip specific steps:**

```bash
syntek init --skip-hooks      # Skip Git hooks setup
syntek init --skip-secrets    # Skip secrets baseline
syntek init --skip-dev-tools  # Skip dev tools installation
```

> **Note:** This replaces the old `scripts/setup-pre-commit.sh` script with a cross-platform Rust implementation.

---

## 5. Set Up Environment Files

Copy example environment files:

```bash
cp .env.dev.example .env.dev
cp .env.test.example .env.test
cp .env.staging.example .env.staging
cp .env.production.example .env.production
```

**Edit `.env.dev` with your local settings:**

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/syntek_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=true

# Add your specific configuration...
```

---

## 6. Start Development Environment

### Using the Rust CLI (Recommended)

```bash
syntek dev
```

This will:

1. Load `.env.dev`
2. Start Docker services (PostgreSQL, Redis)
3. Start Django backend (`uv run python manage.py runserver`)
4. Start Next.js frontend (`pnpm --filter web dev`)

### Manual Start

```bash
# Start Docker services
docker-compose up -d

# Start backend
uv run python manage.py runserver

# Start frontend (in another terminal)
pnpm --filter web dev
```

---

## 7. Run Tests

```bash
# All tests
syntek test

# Specific module
syntek test --module backend/security-core

# Watch mode
syntek test --watch
```

**Manual testing:**

```bash
# Python tests
uv run pytest

# Web tests
pnpm --filter web test

# Rust tests
cd rust && cargo test
```

---

## 8. Lint and Format Code

### Lint

```bash
# Lint all code
syntek lint

# Lint and auto-fix
syntek lint --fix
```

### Format

```bash
# Format all code
syntek format

# Check formatting without modifying
syntek format --check
```

---

## 9. Build for Production

```bash
syntek build --mode production
```

This builds:

- Web packages (Next.js)
- Mobile packages (React Native)
- Rust crates (release mode)

---

## 🎯 Common Commands

### First-Time Setup

| Step | Task                    | Command            |
| ---- | ----------------------- | ------------------ |
| 1    | Install CLI (bootstrap) | `./install-cli.sh` |
| 2    | Install dependencies    | `syntek install`   |
| 3    | Initialize project      | `syntek init`      |

### Daily Development

| Task             | Command                          |
| ---------------- | -------------------------------- |
| Start dev server | `syntek dev`                     |
| Run tests        | `syntek test`                    |
| Lint code        | `syntek lint --fix`              |
| Format code      | `syntek format`                  |
| Build production | `syntek build --mode production` |
| Security audit   | `syntek audit`                   |
| Clean artifacts  | `syntek clean`                   |

---

## 🔧 Directory Structure

```
syntek-modules/
├── backend/           # Django modules (44 modules)
│   ├── security-core/     # Security bundle (middleware, headers, CORS, CSRF, rate limiting, cache)
│   ├── security-auth/     # Auth bundle (authentication, sessions, cookies, JWT, API keys)
│   ├── security-input/    # Input security (validation, SQL injection, content filtering)
│   ├── security-network/  # Network security (IP filtering, request signing, secrets)
│   └── ...                # Feature modules (profiles, media, logging, etc.)
│
├── web/packages/      # Next.js/React packages (15 packages)
│   ├── security-core/     # Web security bundle
│   ├── security-auth/     # Web auth bundle
│   ├── ui-auth/           # Authentication UI
│   └── ...                # Other UI components
│
├── mobile/packages/   # React Native packages (9 packages)
│   ├── security-core/     # Mobile security bundle
│   ├── security-auth/     # Mobile auth bundle
│   └── ...                # Mobile features
│
├── shared/            # Cross-platform shared library
│   ├── components/        # Shared components
│   ├── hooks/             # Shared hooks
│   └── utils/             # Shared utilities
│
├── rust/              # Rust crates (6 crates)
│   ├── encryption/        # AES-256-GCM, ChaCha20-Poly1305
│   ├── security/          # Memory safety, zeroization
│   ├── hashing/           # Argon2id, bcrypt
│   ├── llm_gateway/       # LLM abstraction layer
│   ├── pyo3_bindings/     # PyO3 bridge for Django
│   └── project-cli/       # Syntek CLI tool
│
├── graphql/           # GraphQL encryption middleware
│   ├── middleware/        # Encrypt/decrypt middleware
│   └── schema/            # Custom directives
│
├── docs/              # Documentation
│   ├── METRICS/           # Self-learning metrics system
│   ├── architecture/      # Architecture decisions
│   ├── security/          # Security compliance docs
│   └── guides/            # Integration guides
│
├── examples/          # Example integrations
│
├── .github/workflows/ # CI/CD workflows
│
├── CHANGELOG.md       # Release notes
├── QUICK-START.md     # This file
└── README.md          # Project overview
```

---

## 📚 Documentation

- **[README.md](README.md)** - Project overview and architecture
- **[CHANGELOG.md](CHANGELOG.md)** - Release history
- **[docs/SETUP-STATUS.md](docs/SETUP-STATUS.md)** - Detailed setup status
- **[.claude/CLAUDE.md](.claude/CLAUDE.md)** - Complete project context and module details
- **[rust/project-cli/README.md](rust/project-cli/README.md)** - CLI documentation
- **[docs/security/](docs/security/)** - Security compliance documentation

---

## 🔒 Security

This project implements:

- **OWASP Top 10** protection
- **NIST Cybersecurity Framework** alignment
- **GDPR compliance** (data subject rights, encryption)
- **Field-level encryption** via Rust (AES-256-GCM)
- **Memory safety** with automatic zeroization
- **Security scanning** in CI/CD (CodeQL, Gitleaks, dependency audits)

See `.claude/SECURITY-COMPLIANCE.md` for full details.

---

## 🐛 Troubleshooting

### Python version mismatch

```bash
# Install Python 3.14
uv python install 3.14

# Or use pyenv
pyenv install 3.14
pyenv local 3.14
```

### Node version mismatch

```bash
# Using nvm
nvm install 24.13
nvm use 24.13

# Or using fnm
fnm install 24.13
fnm use 24.13
```

### Rust version mismatch

```bash
rustup install 1.92.0
rustup default 1.92.0
```

### Docker services not starting

```bash
# Check Docker status
docker --version
docker-compose --version

# Restart Docker daemon
sudo systemctl restart docker
```

### Lock file conflicts

```bash
# Regenerate all lock files
syntek clean --deps
syntek install
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `syntek test`
4. Lint and format: `syntek lint --fix && syntek format`
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a pull request

All pull requests trigger CI/CD workflows for linting, testing, and security scanning.

---

## 📞 Support

- **Documentation:** See `docs/` directory
- **Security:** See `.claude/SECURITY-COMPLIANCE.md`
- **CLI Help:** Run `syntek --help` or `syntek <command> --help`

---

## 🚀 Next Steps

1. Explore the codebase: `tree -L 2`
2. Read module READMEs (e.g., `backend/security-auth/README.md`)
3. Check CI/CD workflows in `.github/workflows/`
4. Review security compliance in `docs/security/`
5. Start developing your first feature

---

**Happy coding! 🎉**
