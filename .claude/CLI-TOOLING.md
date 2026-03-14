# CLI Tooling — syntek-dev

**IMPORTANT:** Always use `syntek-dev <command>` for development tasks. Do not invoke `pnpm`,
`cargo`, `pytest`, or `ruff` directly when an equivalent CLI command exists.

---

## Table of Contents

- [Overview](#overview)
- [Installation and Rebuild](#installation-and-rebuild)
- [Command Reference](#command-reference)
  - [up](#up)
  - [test](#test)
  - [lint](#lint)
  - [format](#format)
  - [check](#check)
  - [ci](#ci)
  - [db](#db)
  - [open](#open)
  - [audit](#audit)
- [Source Location](#source-location)

---

## Overview

`syntek-dev` is a Rust binary that wraps the multi-layer toolchain into a single, consistent
interface. It handles all development tasks across Python (uv/pytest/ruff), TypeScript
(pnpm/Vitest), Rust (cargo), and Markdown (markdownlint).

---

## Installation and Rebuild

**First-time setup** (run once after cloning):

```bash
chmod +x install.sh && ./install.sh
```

`install.sh` does the following:

1. Checks that `rustup`, `cargo`, `uv`, `node`, `pnpm`, and `git` are available.
2. Creates `.venv` with Python 3.14 via `uv venv`.
3. Installs Python dev dependencies via `uv sync --group dev`.
4. Installs JS/TS dependencies via `pnpm install`.
5. Builds the CLI with `cargo build --release -p syntek-dev`.
6. Symlinks `target/release/syntek-dev` to `~/.local/bin/syntek-dev`.

**Rebuild after source changes** to `rust/syntek-dev/`:

```bash
cargo build --release -p syntek-dev
```

The symlink at `~/.local/bin/syntek-dev` points to the compiled binary, so a rebuild is sufficient —
no re-run of `install.sh` is needed.

**PATH requirement:** `~/.local/bin` must be on your `PATH`. If it is not:

```bash
export PATH="$HOME/.local/bin:$PATH"
# Add the above line to ~/.zshrc or ~/.bashrc to persist it.
```

**Activate the Python venv** before running any command (required for Python-layer tools):

```bash
source .venv/bin/activate
```

---

## Command Reference

### up

Start development services in watch mode. With no flags, starts all available services.

```
syntek-dev up [--frontend] [--storybook] [--rust]
```

| Flag          | What it does                                                                          |
| ------------- | ------------------------------------------------------------------------------------- |
| `--frontend`  | Starts all frontend packages in watch mode via Turborepo (`pnpm dev`)                 |
| `--storybook` | Starts Storybook for `@syntek/ui` on port 6006 (`pnpm --filter @syntek/ui storybook`) |
| `--rust`      | Starts the Rust file watcher via `cargo-watch` (requires `cargo install cargo-watch`) |

With no flags all three services are started concurrently. Press `Ctrl+C` to stop all services.

**Prerequisite warnings:**

- If `.venv` does not exist: `No .venv found — run: uv venv && source .venv/bin/activate`
- If `pnpm` is not found: `install with: npm install -g pnpm@10`
- If `cargo-watch` is not installed: `run: cargo install cargo-watch`

**Examples:**

```bash
# Start everything (frontend + Storybook + Rust watcher)
syntek-dev up

# Start only the frontend watch mode
syntek-dev up --frontend

# Start only Storybook
syntek-dev up --storybook

# Start only the Rust watcher
syntek-dev up --rust
```

---

### build

Build packages across one or more layers. With no flags, builds all layers.

```
syntek-dev build [--rust] [--rust-crate <CRATE>]
                 [--python] [--python-package <PACKAGE>]
                 [--web] [--web-package <PACKAGE>]
                 [--mobile]
```

| Flag                       | What it does                                                              |
| -------------------------- | ------------------------------------------------------------------------- |
| `--rust`                   | Build all Rust crates in release mode (`cargo build --release --all`)     |
| `--rust-crate CRATE`       | Build a specific crate, e.g. `syntek-pyo3` (`cargo build --release -p`)   |
| `--python`                 | Dev-install all Python packages into venv (`uv sync --group dev`)         |
| `--python-package PACKAGE` | Build a specific package wheel, e.g. `syntek-auth` (`uv build --package`) |
| `--web`                    | Build all web packages via Turborepo (`pnpm turbo run build`)             |
| `--web-package PACKAGE`    | Build a specific web package, e.g. `@syntek/ui-auth`                      |
| `--mobile`                 | Build all mobile packages (`pnpm --filter "@syntek/mobile-*" build`)      |

**Examples:**

```bash
# Build all layers
syntek-dev build

# Rebuild all Rust crates (release)
syntek-dev build --rust

# Rebuild a specific Rust crate — e.g. after a version bump
syntek-dev build --rust --rust-crate syntek-pyo3

# Dev-install all Python packages
syntek-dev build --python

# Build a specific Python package wheel
syntek-dev build --python --python-package syntek-auth

# Build all web packages
syntek-dev build --web

# Build a specific web package
syntek-dev build --web --web-package @syntek/ui-auth

# Build mobile packages
syntek-dev build --mobile
```

---

### test

Run the test suite across one or more layers. With no flags, runs all layers.

```
syntek-dev test [--python] [--python-package <PACKAGE>]
                [--rust]
                [--web] [--web-package <PACKAGE>]
                [--mobile]
                [--e2e]
                [-m <MARKER>] [-k <PATTERN>]
                [--watch] [--coverage]
```

| Flag                       | What it does                                                      |
| -------------------------- | ----------------------------------------------------------------- |
| `--python`                 | Run Python/Django tests via `pytest`                              |
| `--python-package PACKAGE` | Restrict pytest to a specific backend package, e.g. `syntek-auth` |
| `--rust`                   | Run Rust tests via `cargo test --all`                             |
| `--web`                    | Run TypeScript/web tests via Vitest (pnpm Turborepo)              |
| `--web-package PACKAGE`    | Restrict Vitest to a specific web package, e.g. `@syntek/ui-auth` |
| `--mobile`                 | Run mobile tests via Jest + React Native Testing Library          |
| `--e2e`                    | Run E2E tests via Playwright (`pnpm test:e2e`)                    |
| `-m MARKER`                | pytest marker filter: `unit`, `integration`, `e2e`, `slow`        |
| `-k PATTERN`               | pytest or Vitest keyword/pattern filter                           |
| `--watch`                  | Enable watch mode (web and mobile only)                           |
| `--coverage`               | Generate coverage reports                                         |

**Note:** E2E tests (`--e2e`) are never included in the "run all" default — they must be requested
explicitly.

**Python coverage** uses `--cov --cov-report=html`. **TypeScript/mobile coverage** passes
`-- --coverage` to the underlying test runner.

**Examples:**

```bash
# Run all layers (Python + Rust + web + mobile)
syntek-dev test

# Run only Python tests
syntek-dev test --python

# Run Python tests for a single backend package
syntek-dev test --python --python-package syntek-auth

# Run only unit-marked Python tests
syntek-dev test --python -m unit

# Run Python tests matching a keyword
syntek-dev test --python -k login

# Run only Rust tests
syntek-dev test --rust

# Run web tests for a specific package in watch mode
syntek-dev test --web --web-package @syntek/ui-auth --watch

# Run all web tests with coverage
syntek-dev test --web --coverage

# Run mobile tests
syntek-dev test --mobile

# Run E2E tests (Playwright)
syntek-dev test --e2e
```

---

### lint

Run linters and type checkers across all layers. With no flags, runs all linters.

```
syntek-dev lint [--ruff] [--pyright] [--eslint] [--clippy]
                [--markdown] [--prettier]
                [--fix] [PACKAGE]
```

| Flag/Arg     | What it does                                                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `--ruff`     | Run `ruff check packages/backend/` (Python lint + import sorting)                                                             |
| `--pyright`  | Run `basedpyright packages/backend/` (Python type checking, falls back to pyright)                                            |
| `--eslint`   | Run ESLint on TypeScript/JS (`pnpm lint`)                                                                                     |
| `--prettier` | Run Prettier format check (`pnpm format:check`)                                                                               |
| `--clippy`   | Run `cargo clippy --all-targets --all-features -- -D warnings` (Rust)                                                         |
| `--markdown` | Run markdownlint (`pnpm lint:md`)                                                                                             |
| `--fix`      | Auto-fix where possible: ruff `--fix`, ESLint `--fix`, Prettier `--write`, markdownlint `--fix`, clippy `--fix --allow-dirty` |
| `PACKAGE`    | Positional — restrict ruff and basedpyright to `packages/backend/<PACKAGE>`                                                   |

**`--fix` behaviour per tool:**

| Tool         | Fix behaviour                                |
| ------------ | -------------------------------------------- |
| ruff         | `ruff check --fix`                           |
| basedpyright | No auto-fix (type errors require code edits) |
| ESLint       | `eslint --fix`                               |
| Prettier     | Runs `pnpm format` (Prettier `--write`)      |
| clippy       | `cargo clippy --fix --allow-dirty`           |
| markdownlint | `pnpm lint:md:fix`                           |

**Examples:**

```bash
# Run all linters
syntek-dev lint

# Run all linters and auto-fix what can be fixed
syntek-dev lint --fix

# Run only ruff
syntek-dev lint --ruff

# Run ruff on a specific backend package
syntek-dev lint --ruff syntek-auth

# Run only ESLint with auto-fix
syntek-dev lint --eslint --fix

# Run only clippy
syntek-dev lint --clippy

# Run only Prettier check
syntek-dev lint --prettier

# Run only markdownlint with auto-fix
syntek-dev lint --markdown --fix
```

---

### format

Format code across all layers. With no flags, formats all layers.

```
syntek-dev format [--python] [--ts] [--rust] [--check]
```

| Flag       | What it does                                                                                                           |
| ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--python` | Format Python with `ruff format packages/backend/`                                                                     |
| `--ts`     | Format TypeScript/JS/JSON/YAML/Markdown with `pnpm prettier --write .`                                                 |
| `--rust`   | Format Rust with `cargo fmt --all`                                                                                     |
| `--check`  | Check only — do not write files (adds `--check` to ruff and `--` `--check` to cargo fmt, passes `--check` to Prettier) |

**Examples:**

```bash
# Format all layers
syntek-dev format

# Format all layers — check only (no writes)
syntek-dev format --check

# Format only Python
syntek-dev format --python

# Format only TypeScript/JS/JSON/YAML/Markdown
syntek-dev format --ts

# Format only Rust
syntek-dev format --rust

# Check Rust formatting without writing
syntek-dev format --rust --check
```

---

### check

Quick quality check — runs lint and type checking only. Does not run tests.

```
syntek-dev check [<same flags as lint>]
```

`check` accepts identical flags to `lint` and delegates to the same linting logic. Use this for a
fast pre-commit sanity check when you do not want to run the full test suite.

**Example:**

```bash
syntek-dev check
```

---

### ci

Run the full CI pipeline locally, mirroring all four Forgejo/GitHub workflow files. All 14 steps
must pass before pushing.

```
syntek-dev ci
```

No flags. The pipeline is fixed and mirrors the remote CI exactly.

**14 steps executed in order:**

| Step | Workflow            | What runs                                                                                        |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------ |
| 1    | `web.yml`           | Prettier format check (`pnpm format:check`)                                                      |
| 2    | `web.yml`           | ESLint (`pnpm lint`)                                                                             |
| 3    | `web.yml`           | Markdownlint (`pnpm lint:md`)                                                                    |
| 4    | `web.yml`           | TypeScript type-check (`pnpm type-check`)                                                        |
| 5    | `web.yml`           | TypeScript tests (`pnpm test`)                                                                   |
| 6    | `web.yml`           | TypeScript coverage (`pnpm test -- --coverage`)                                                  |
| 7    | `graphql-drift.yml` | GraphQL schema drift check (`pnpm --filter @syntek/graphql codegen:check`)                       |
| 8    | `python.yml`        | ruff check (`uv run ruff check packages/backend/`)                                               |
| 9    | `python.yml`        | ruff format check (`uv run ruff format --check packages/backend/`)                               |
| 10   | `python.yml`        | basedpyright (`uv run basedpyright packages/backend/`)                                           |
| 11   | `python.yml`        | pytest (`uv run pytest packages/backend/ -x -q`) — exit code 5 (no tests collected) is tolerated |
| 12   | `rust.yml`          | cargo fmt check (`cargo fmt --all -- --check`)                                                   |
| 13   | `rust.yml`          | clippy (`cargo clippy --all-targets --all-features -- -D warnings`)                              |
| 14   | `rust.yml`          | cargo test (`cargo test --all`)                                                                  |

If all 14 steps pass, the output shows `Safe to push.`

If any step fails, the failing step names are listed and the process exits with a non-zero code.

**Example:**

```bash
syntek-dev ci
```

---

### db

Database management commands. All subcommands require `sandbox/manage.py` to exist. See
`docs/GUIDES/SANDBOX.md` for sandbox setup instructions.

```
syntek-dev db <subcommand> [args]
```

#### db migrate

Apply pending migrations.

```
syntek-dev db migrate [MODULE]
```

| Argument | Description                                                      |
| -------- | ---------------------------------------------------------------- |
| `MODULE` | Optional. Django app label, e.g. `syntek_auth`. Omit to run all. |

**Examples:**

```bash
# Migrate all modules
syntek-dev db migrate

# Migrate a specific module
syntek-dev db migrate syntek_auth
```

#### db makemigrations

Create new migration files for a module.

```
syntek-dev db makemigrations [MODULE]
```

| Argument | Description                                                        |
| -------- | ------------------------------------------------------------------ |
| `MODULE` | Optional. Django app label, e.g. `syntek_auth`. Omit for all apps. |

**Examples:**

```bash
# Generate migrations for all apps
syntek-dev db makemigrations

# Generate migrations for a specific module
syntek-dev db makemigrations syntek_auth
```

#### db rollback

Roll back migrations for a module to a target state.

```
syntek-dev db rollback [MODULE] [--to TARGET]
```

| Argument      | Description                                                                      |
| ------------- | -------------------------------------------------------------------------------- |
| `MODULE`      | Optional. Module name. Required in practice — exits with error if omitted.       |
| `--to TARGET` | Target migration number, e.g. `0003`, or `zero` to unapply all. Default: `zero`. |

**Examples:**

```bash
# Roll back all migrations for syntek_auth
syntek-dev db rollback syntek_auth

# Roll back to a specific migration
syntek-dev db rollback syntek_auth --to 0003
```

#### db status

Show migration status for all modules or a specific one.

```
syntek-dev db status [MODULE]
```

**Examples:**

```bash
# Show migration status for all modules
syntek-dev db status

# Show migration status for a specific module
syntek-dev db status syntek_auth
```

#### db seed

Seed the database with development mock data. Calls the `seed_dev` Django management command, which
each backend module must implement using `factory_boy`.

```
syntek-dev db seed
```

#### db seed-test

Seed the database with test-specific mock data. Calls the `seed_test` management command.

```
syntek-dev db seed-test [SCENARIO]
```

| Argument   | Description                                            |
| ---------- | ------------------------------------------------------ |
| `SCENARIO` | Optional. Named scenario, e.g. `payments`, `auth-mfa`. |

**Examples:**

```bash
# Seed with default test data
syntek-dev db seed-test

# Seed with a named scenario
syntek-dev db seed-test payments
syntek-dev db seed-test auth-mfa
```

#### db reset

Drop and recreate the test database, then run all migrations. Internally runs Django
`flush --noinput` followed by `migrate`.

```
syntek-dev db reset
```

#### db shell

Open a `psql` shell to the local database via Django `dbshell`. Exit with `Ctrl+D` or `\q`.

```
syntek-dev db shell
```

---

### open

Open a local service in the browser.

```
syntek-dev open <TARGET>
```

| Target      | URL                             |
| ----------- | ------------------------------- |
| `api`       | `http://localhost:8000/graphql` |
| `frontend`  | `http://localhost:3000`         |
| `storybook` | `http://localhost:6006`         |
| `admin`     | `http://localhost:8000/admin`   |

**Examples:**

```bash
syntek-dev open api
syntek-dev open frontend
syntek-dev open storybook
syntek-dev open admin
```

---

### audit

Scan all dependency manifests for known vulnerabilities and (optionally) outdated packages. With no
layer flags, audits all three layers.

```
syntek-dev audit [--python] [--rust] [--js] [--outdated]
```

| Flag         | What it does                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------- |
| `--python`   | Run `pip-audit` via `uv run --with pip-audit pip-audit` against `pyproject.toml` / `uv.lock`  |
| `--rust`     | Run `cargo audit --deny unsound --deny yanked` against `Cargo.toml` / `Cargo.lock`            |
| `--js`       | Run `pnpm audit --audit-level=moderate` against `package.json` / `pnpm-lock.yaml`             |
| `--outdated` | Also report outdated packages for each selected layer (informational — does not fail the run) |
| `--update`   | Apply safe (semver-compatible) updates and regenerate lock files for each selected layer      |

**Prerequisites:**

- Python audit: `uv` must be on PATH (`pip-audit` is injected ephemerally — no install needed)
- Rust audit: `cargo-audit` must be installed — `cargo install cargo-audit`
- Rust outdated: `cargo-outdated` must be installed — `cargo install cargo-outdated`
- JS audit: `pnpm` must be on PATH

**What "safe updates" means per layer:**

| Layer  | Command             | What it updates                                                                                             |
| ------ | ------------------- | ----------------------------------------------------------------------------------------------------------- |
| Python | `uv sync --upgrade` | All packages to the latest version allowed by `pyproject.toml` ranges; regenerates `uv.lock`                |
| Rust   | `cargo update`      | All crates to the latest semver-compatible version; regenerates `Cargo.lock` only (no `Cargo.toml` changes) |
| JS/TS  | `pnpm update`       | All packages to the latest version within `package.json` ranges; regenerates `pnpm-lock.yaml`               |

**Exit codes:**

- Exits non-zero if any vulnerability scan reports findings at or above the threshold, or if an
  `--update` command itself fails.
- Outdated-package checks are informational — they print a warning but do not cause a non-zero exit
  on their own.

**Examples:**

```bash
# Audit all layers for vulnerabilities
syntek-dev audit

# Audit all layers for vulnerabilities and outdated packages
syntek-dev audit --outdated

# Audit only Python
syntek-dev audit --python

# Audit only Rust
syntek-dev audit --rust

# Audit JS/TS and also show outdated packages
syntek-dev audit --js --outdated

# Apply safe updates across all layers
syntek-dev audit --update

# Audit everything, show outdated, and apply safe updates in one pass
syntek-dev audit --outdated --update
```

---

## Source Location

| File                                     | Purpose                                              |
| ---------------------------------------- | ---------------------------------------------------- |
| `rust/syntek-dev/src/cli.rs`             | Clap command/flag definitions (authoritative source) |
| `rust/syntek-dev/src/main.rs`            | Entry point                                          |
| `rust/syntek-dev/src/commands/audit.rs`  | `audit` implementation                               |
| `rust/syntek-dev/src/commands/up.rs`     | `up` implementation                                  |
| `rust/syntek-dev/src/commands/test.rs`   | `test` implementation                                |
| `rust/syntek-dev/src/commands/lint.rs`   | `lint` and `check` implementation                    |
| `rust/syntek-dev/src/commands/format.rs` | `format` implementation                              |
| `rust/syntek-dev/src/commands/ci.rs`     | `ci` implementation                                  |
| `rust/syntek-dev/src/commands/db.rs`     | `db` subcommand implementations                      |
| `rust/syntek-dev/src/config.rs`          | Root detection, venv path helpers                    |
| `rust/syntek-dev/src/process.rs`         | Process spawning utilities                           |
| `rust/syntek-dev/src/ui.rs`              | Terminal output formatting                           |
