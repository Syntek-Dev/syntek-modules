# Getting Started — syntek-modules Contributors

**Last Updated**: 06/03/2026\
**Audience**: Module contributors and maintainers\
**Language**: British English (en_GB)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Bootstrap the Environment](#bootstrap-the-environment)
- [Project Structure](#project-structure)
- [The syntek-dev CLI](#the-syntek-dev-cli)
  - [Starting Development Services](#starting-development-services)
  - [Running Tests](#running-tests)
  - [Linting](#linting)
  - [Formatting](#formatting)
  - [Database Management](#database-management)
  - [Opening Services in the Browser](#opening-services-in-the-browser)
- [Daily Development Workflow](#daily-development-workflow)
- [dist/ and Build Artefacts](#dist-and-build-artefacts)
- [Python Virtual Environment](#python-virtual-environment)
- [Adding a New Module](#adding-a-new-module)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure all of the following are installed before running `install.sh`:

| Tool             | Minimum version | Install                                            |
| ---------------- | --------------- | -------------------------------------------------- |
| **Rust / cargo** | stable          | [rustup.rs](https://rustup.rs)                     |
| **uv**           | latest          | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js**      | 24.x            | [nodejs.org](https://nodejs.org)                   |
| **pnpm**         | 10.x            | `npm install -g pnpm@10`                           |
| **Git**          | 2.x             | via package manager                                |

Optional but recommended:

| Tool             | Install                     | Used for                                          |
| ---------------- | --------------------------- | ------------------------------------------------- |
| **cargo-watch**  | `cargo install cargo-watch` | Rust auto-recompile on file change                |
| **maturin**      | `uv pip install maturin`    | Building PyO3 extensions (included in install.sh) |
| **basedpyright** | Bundled in Zed LSP          | Python type checking                              |

---

## Bootstrap the Environment

Run this once after cloning:

```bash
git clone git@git.syntek-studio.com:syntek/syntek-modules.git
cd syntek-modules

chmod +x install.sh && ./install.sh
```

`install.sh` does the following in order:

1. Checks that all required tools are installed
2. Creates a Python 3.14 virtual environment at `.venv/`
3. Installs Python dev tooling: `ruff`, `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`,
   `testcontainers`, `hypothesis`, `django-stubs`, `maturin`
4. Runs `pnpm install` to install all TypeScript/JavaScript dependencies
5. Builds the `syntek-dev` CLI binary via `cargo build --release -p syntek-dev`
6. Symlinks the binary to `~/.local/bin/syntek-dev`

After install completes:

```bash
source .venv/bin/activate   # activate Python venv (add to your shell profile if preferred)
syntek-dev --help            # verify the CLI is available
```

If `~/.local/bin` is not on your `PATH`, add this to `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## Project Structure

```text
syntek-modules/
├── packages/
│   ├── backend/          Django / Python modules (uv workspace members)
│   └── web/              React / TypeScript packages (pnpm workspace)
├── mobile/               React Native packages (pnpm workspace)
├── rust/
│   ├── syntek-crypto/    AES-256-GCM, Argon2id, HMAC-SHA256
│   ├── syntek-pyo3/      PyO3 Django bindings
│   ├── syntek-graphql-crypto/  GraphQL middleware
│   └── syntek-dev/       This CLI tool (binary crate)
├── shared/
│   ├── types/            Shared TypeScript types
│   └── graphql/          Shared GraphQL operations
├── docs/GUIDES/          Developer guides and templates
├── install.sh            Bootstrap script (run once)
├── pyproject.toml        uv workspace root + ruff + pytest config
├── pyrightconfig.json    basedpyright configuration
├── Cargo.toml            Rust workspace
├── pnpm-workspace.yaml   pnpm workspace
├── package.json          Root tooling (turbo, eslint, prettier)
└── turbo.json            Turborepo build pipeline
```

---

## The syntek-dev CLI

The `syntek-dev` CLI manages all development operations across all four layers of this monorepo. It
replaces the old shell scripts.

Run from anywhere inside the repository — it locates the workspace root automatically.

```bash
syntek-dev --help
syntek-dev <command> --help
```

---

### Starting Development Services

```bash
# Start all services (pnpm dev watch + Storybook + Rust watcher if available)
syntek-dev up

# Start only specific services
syntek-dev up --frontend       # pnpm dev (Turborepo watch mode for all TS packages)
syntek-dev up --storybook      # @syntek/ui Storybook at http://localhost:6006
syntek-dev up --rust           # cargo-watch (Rust incremental check on file change)
```

Press `Ctrl+C` to stop all services cleanly.

---

### Running Tests

```bash
# Run the full test suite across all layers
syntek-dev test

# Run only one layer
syntek-dev test --python
syntek-dev test --rust
syntek-dev test --web
syntek-dev test --mobile
syntek-dev test --e2e          # Playwright end-to-end tests

# Target a specific package
syntek-dev test --python-package syntek-auth
syntek-dev test --web-package @syntek/ui-auth

# Filter by pytest marker
syntek-dev test -m unit
syntek-dev test -m integration
syntek-dev test -m "unit or integration"

# Filter by keyword (pytest -k / vitest --grep)
syntek-dev test -k "login"

# Coverage reports
syntek-dev test --coverage

# Watch mode (web and mobile only)
syntek-dev test --web --watch
```

---

### Linting

```bash
# Run all linters
syntek-dev lint

# Run specific linters
syntek-dev lint --ruff          # Python lint (ruff check)
syntek-dev lint --pyright       # Python type checking (basedpyright)
syntek-dev lint --eslint        # TypeScript / JS (ESLint 9)
syntek-dev lint --clippy        # Rust (cargo clippy -D warnings)
syntek-dev lint --markdown      # Markdown (markdownlint-cli2)

# Auto-fix where possible
syntek-dev lint --fix           # ruff --fix + eslint --fix

# Restrict to one package
syntek-dev lint syntek-auth

# Quick check (lint + type-check, no tests) — fast pre-commit check
syntek-dev check
```

---

### Formatting

```bash
# Format everything
syntek-dev format

# Check only (CI mode — do not write files)
syntek-dev format --check

# Format specific layer
syntek-dev format --python      # ruff format
syntek-dev format --ts          # prettier
syntek-dev format --rust        # cargo fmt
```

---

### Database Management

The `db` commands require `sandbox/manage.py` — a minimal Django project that has all backend
modules installed for local development and testing. See the sandbox setup section in
`docs/GUIDES/SANDBOX.md` once it is created.

```bash
# Migrations
syntek-dev db migrate                   # Run all pending migrations
syntek-dev db migrate syntek-auth       # Run migrations for one module
syntek-dev db makemigrations syntek-auth
syntek-dev db rollback syntek-auth --to 0003
syntek-dev db rollback syntek-auth --to zero
syntek-dev db status                    # Show migration status

# Seeding
syntek-dev db seed                      # Seed with dev mock data (factory_boy)
syntek-dev db seed-test                 # Seed with default test scenario
syntek-dev db seed-test payments        # Seed with named scenario

# Reset
syntek-dev db reset                     # flush + migrate (keeps schema)

# Database shell
syntek-dev db shell                     # Opens psql via Django dbshell
```

---

### Opening Services in the Browser

```bash
syntek-dev open api         # GraphQL playground — http://localhost:8000/graphql
syntek-dev open frontend    # Frontend dev server — http://localhost:3000
syntek-dev open storybook   # Storybook — http://localhost:6006
syntek-dev open admin       # Django admin — http://localhost:8000/admin
```

---

## Daily Development Workflow

1. **Activate the Python venv**: `source .venv/bin/activate`
2. **Pull latest**: `git pull origin main`
3. **Create a branch**: `git checkout -b us042/syntek-payments`
4. **Start dev services**: `syntek-dev up`
5. **Write failing test first** (TDD — see `TEST-STATUS.md` and `MANUAL-TESTING.md` in each package
   directory)
6. **Write implementation** to make the test pass
7. **Quick check before commit**: `syntek-dev check`
8. **Full suite before PR**: `syntek-dev test`
9. **Commit**: follow Conventional Commits format (see [Development Guide](.claude/DEVELOPMENT.md))
10. **Open PR** on Forgejo

---

## dist/ and Build Artefacts

**`dist/` is gitignored.** This is correct and intentional.

This repository is a **package library**, not a deployable application:

- Each backend module (`packages/backend/syntek-<name>/`) builds to its own `dist/` as Python wheel
  files (`.whl`) when publishing to the Forgejo PyPI registry.
- Each web package (`packages/web/<name>/`) builds to its own `dist/` as JavaScript/ TypeScript
  output when publishing to the Forgejo npm registry.
- These are **ephemeral build artefacts** — the source of truth is always the source files + the
  published version in the registry.
- **No `.next/` folder exists** in this repo. There is no Next.js application here. Web packages are
  pure React component libraries, not Next.js apps. The `.next/` entry in `.gitignore` is a
  precaution for any sandbox app that may be added later.
- Mobile packages build to `dist/` for npm publishing, same pattern.

The distinction from a full app: in a deployed Next.js app, `.next/` is the deployment artefact.
Here, `dist/` is a transient staging directory used during `cargo build --release` → `maturin build`
→ `uv build` → publish cycle.

---

## Python Virtual Environment

Always activate before doing Python work:

```bash
source .venv/bin/activate
```

To install a backend module in editable mode (for active development on that module):

```bash
uv pip install -e "packages/backend/syntek-auth[dev]"
```

To run type checking manually:

```bash
basedpyright packages/backend/syntek-auth/
```

---

## Adding a New Module

Use the `/add-module` skill in Claude Code:

```text
/add-module
```

Or follow the manual steps:

1. Create `packages/backend/syntek-<name>/` with `pyproject.toml`, `syntek_<name>/`, `tests/`,
   `TEST-STATUS.md`, and `docs/MANUAL-TESTING.md`
2. Copy templates from `docs/GUIDES/templates/`
3. Register the module in `.claude/CLAUDE.md` Module Registry
4. Add it to `pnpm-workspace.yaml` if it has a web component

---

## Troubleshooting

### `syntek-dev: command not found`

```bash
# Ensure ~/.local/bin is on your PATH
export PATH="$HOME/.local/bin:$PATH"

# Rebuild and re-symlink
cargo build --release -p syntek-dev
ln -sf "$(pwd)/target/release/syntek-dev" ~/.local/bin/syntek-dev
```

### Python venv issues

```bash
rm -rf .venv
uv venv --python 3.14
source .venv/bin/activate
uv pip install ruff pytest pytest-django pytest-cov factory-boy testcontainers hypothesis django-stubs maturin
```

### pnpm workspace package not resolving

```bash
pnpm install   # re-link all workspace packages
```

### Rust build fails

```bash
rustup update stable
cargo clean
cargo build -p syntek-dev
```

### basedpyright reports Django model errors

```bash
uv pip install "django-stubs[compatible-mypy]"
```

`pyrightconfig.json` at the root already points to the correct venv. Restart the Zed LSP if the
errors persist (`Zed: Restart Language Server` from the command palette).
