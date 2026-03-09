# Developer Guide — syntek-modules

**Last Updated:** 08/03/2026 | **Audience:** Module contributors and maintainers\
**Language:** British English (en_GB)

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Environment Setup](#environment-setup)
- [Daily Development Workflow](#daily-development-workflow)
- [syntek-dev CLI Reference](#syntek-dev-cli-reference)
- [Running Tests](#running-tests)
- [Linting and Formatting](#linting-and-formatting)
- [Adding a New Module or Package](#adding-a-new-module-or-package)
- [IDE Configuration](#ide-configuration)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Runtimes and tooling

| Tool           | Minimum Version | Purpose                                         |
| -------------- | --------------- | ----------------------------------------------- |
| **Git**        | Latest stable   | Version control                                 |
| **Node.js**    | 24.14.0         | TypeScript / JavaScript runtime                 |
| **pnpm**       | 10.31.0         | JavaScript package manager                      |
| **Python**     | 3.14.x          | Django backend packages                         |
| **uv**         | Latest stable   | Python package and venv manager                 |
| **Rust**       | Latest stable   | Encryption crates + syntek-dev CLI              |
| **PostgreSQL** | 18.x            | Database (integration tests)                    |
| **Valkey**     | Latest stable   | Cache and task queue (Redis-compatible drop-in) |

### Frontend framework versions (managed via pnpm workspace)

| Package          | Minimum Version | Purpose                                  |
| ---------------- | --------------- | ---------------------------------------- |
| **Next.js**      | 16.1.6          | React framework for all web packages     |
| **React**        | 19.2            | UI library                               |
| **TypeScript**   | 5.9.x           | Static typing across all JS/TS packages  |
| **Tailwind CSS** | 4.2             | Utility-first CSS — web packages         |
| **React Native** | 0.84.x          | Mobile framework for all mobile packages |
| **NativeWind**   | 4.x             | Tailwind CSS for React Native            |

> These versions are declared in each package's `package.json` and managed via pnpm workspaces. You
> do not install them manually — `./install.sh` handles everything.
>
> This repository does **not** use Docker or DDEV. All services run natively.

---

## Environment Setup

### 1. Clone

```bash
git clone git@github.com:Syntek-Dev/syntek-modules.git
# or (when Forgejo self-hosting is live):
git clone git@git.syntek-studio.com:syntek/syntek-modules.git
cd syntek-modules
```

### 2. Bootstrap

Run the install script — it handles everything in one go:

```bash
chmod +x install.sh && ./install.sh
```

This will:

- Verify all system prerequisites
- Create a Python virtual environment with `uv venv`
- Install all Python dev dependencies from `uv.lock`
- Install all JavaScript/TypeScript workspace dependencies via `pnpm install`
- Build the `syntek-dev` CLI from source (Rust)
- Symlink `syntek-dev` to `~/.local/bin/`

### 3. Activate the Python virtual environment

```bash
source .venv/bin/activate
```

Add to your shell profile to activate automatically on `cd`:

```bash
# ~/.zshrc or ~/.bashrc
cd /path/to/syntek-modules && source .venv/bin/activate
```

### 4. Verify

```bash
syntek-dev --version
syntek-dev --help
```

---

## Daily Development Workflow

```bash
# Start watch services
syntek-dev up --frontend

# Make changes...

# Before committing: fix all linting
syntek-dev lint --fix

# Verify clean state
syntek-dev lint

# Commit

# Before pushing: run full CI
syntek-dev ci

# Push
git push origin us###/my-branch
```

---

## syntek-dev CLI Reference

All development tasks use the `syntek-dev` CLI. See [CLI Tooling](.claude/CLI-TOOLING.md) for the
full command reference.

| Command                 | What it does                                                            |
| ----------------------- | ----------------------------------------------------------------------- |
| `syntek-dev up`         | Start development services (frontend, Storybook, Rust watcher)          |
| `syntek-dev test`       | Run the full test suite across all layers                               |
| `syntek-dev lint`       | Run all linters (ruff, pyright, ESLint, Prettier, clippy, markdownlint) |
| `syntek-dev lint --fix` | Auto-fix all linting issues                                             |
| `syntek-dev format`     | Format all code (Prettier, ruff format, cargo fmt)                      |
| `syntek-dev ci`         | Run all 14 CI checks locally                                            |
| `syntek-dev check`      | Quick quality check — lint + type-check only                            |
| `syntek-dev db migrate` | Run Django migrations                                                   |
| `syntek-dev open api`   | Open the GraphQL playground in the browser                              |

> **Rule:** Always use `syntek-dev <command>` instead of running `pnpm`, `cargo`, `pytest`, or
> `ruff` directly. The CLI handles paths, venv activation, and flags correctly.

---

## Running Tests

```bash
# All layers
syntek-dev test

# Python / Django only
syntek-dev test --python

# One backend package
syntek-dev test --python --python-package syntek-auth

# Rust
syntek-dev test --rust

# TypeScript / React
syntek-dev test --web

# One web package
syntek-dev test --web --web-package @syntek/ui-auth

# React Native / mobile
syntek-dev test --mobile

# End-to-end (Playwright)
syntek-dev test --e2e

# With coverage
syntek-dev test --coverage

# Watch mode (web and mobile)
syntek-dev test --web --watch
```

### Test file locations

| Layer     | Location                                       |
| --------- | ---------------------------------------------- |
| Backend   | `packages/backend/<module>/tests/`             |
| Web       | `packages/web/<package>/src/__tests__/`        |
| Mobile    | `mobile/<package>/__tests__/`                  |
| Rust      | `rust/<crate>/tests/` or inline `#[cfg(test)]` |
| Test docs | `docs/TESTS/US###-TEST-STATUS.md`              |

---

## Linting and Formatting

```bash
# Auto-fix everything (run before every commit)
syntek-dev lint --fix

# Check only (no writes — run to verify before pushing)
syntek-dev lint

# Individual layers
syntek-dev lint --ruff       # Python lint
syntek-dev lint --pyright    # Python type checking
syntek-dev lint --eslint     # TypeScript / JS
syntek-dev lint --prettier   # Prettier format check
syntek-dev lint --clippy     # Rust
syntek-dev lint --markdown   # Markdown

# Format only (writes, no checks)
syntek-dev format --python   # ruff format
syntek-dev format --ts       # Prettier
syntek-dev format --rust     # cargo fmt
```

---

## Adding a New Module or Package

### Backend (Django)

1. Create `packages/backend/syntek-<name>/`
2. Add `pyproject.toml`, `syntek_<name>/`, and `tests/`
3. Register in root `pyproject.toml` under `[tool.uv.workspace]`
4. Follow the pattern of existing modules (e.g., `syntek-auth`)

### Web (React / TypeScript)

1. Create `packages/web/<name>/` with `package.json` and `src/`
2. Publish name: `@syntek/<name>`
3. Add to `pnpm-workspace.yaml`
4. Add a `turbo.json` pipeline entry if needed

### Mobile (React Native)

1. Create `mobile/<name>/` with `package.json` and `src/`
2. Publish name: `@syntek/mobile-<name>`
3. Add to `pnpm-workspace.yaml`

### Rust Crate

1. Create `rust/<name>/` with `Cargo.toml` and `src/lib.rs`
2. Add to the `[workspace]` members list in root `Cargo.toml`
3. Use `version.workspace = true` in the crate's `Cargo.toml`

> Use `/syntek-dev-suite:add-module` (Claude Code skill) to scaffold new modules automatically.

---

## IDE Configuration

### Zed

Project-level Zed settings are in `.zed/settings.json`. LSP configuration:

- **Python:** basedpyright (not standard pyright)
- **TypeScript:** tsserver (bundled with Zed)
- **Rust:** rust-analyzer

### VS Code / Cursor

Recommended extensions (not pre-configured in this repo):

- ESLint, Prettier, Ruff, rust-analyzer, Even Better TOML

### basedpyright notes

- Requires `django-stubs` for Django model type inference
- Config: `pyrightconfig.json` at repo root
- Mode: `standard`
- Venv: `.venv`

---

## Troubleshooting

### `syntek-dev: command not found`

The CLI binary is not on your PATH. Run:

```bash
./install.sh
# Then check:
echo $PATH | grep -o "$HOME/.local/bin"
# If missing:
export PATH="$HOME/.local/bin:$PATH"
```

### Python venv not active

```bash
source .venv/bin/activate
python --version  # should show 3.14.x
```

### pnpm install fails

```bash
# Check node version
node --version   # should be 24.x
# Reinstall
pnpm install --frozen-lockfile
```

### Rust build fails

```bash
rustup update stable
cargo clean
cargo build --release -p syntek-dev
```

### Prettier fails on markdown files

Run `syntek-dev lint --fix` — Prettier is included in the fix pass and will reformat the files. If
markdownlint also fails after Prettier, check that headings have blank lines above and below them.

---

## Related Guides

| Guide                                                        | Purpose                                 |
| ------------------------------------------------------------ | --------------------------------------- |
| `CONTRIBUTING.md`                                            | Contribution guidelines and PR workflow |
| [`.claude/CLI-TOOLING.md`](.claude/CLI-TOOLING.md)           | Full syntek-dev command reference       |
| [`.claude/GIT-GUIDE.md`](.claude/GIT-GUIDE.md)               | Commit and push workflow                |
| [`.claude/VERSIONING-GUIDE.md`](.claude/VERSIONING-GUIDE.md) | Versioning rules and root files         |
| `docs/GUIDES/ISSUES.md`                                      | How to report bugs and request features |
