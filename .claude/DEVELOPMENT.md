# Development Workflow — syntek-modules

**Last Updated**: 06/03/2026\
**Version**: 0.1.0\
**Language**: British English (en_GB)\
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Daily Workflow](#daily-workflow)
- [Code Quality](#code-quality)
- [Git Workflow](#git-workflow)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Overview

`syntek-modules` is a multi-stack library repository — **not a deployable app**. There is no Docker,
no DDEV, and no `manage.py`. Each layer has its own package manager and toolchain:

| Layer                    | Location             | Tool             |
| ------------------------ | -------------------- | ---------------- |
| Backend (Django/Python)  | `packages/backend/*` | `uv` + `.venv`   |
| Web frontend (React/TS)  | `packages/web/*`     | pnpm + Turborepo |
| Mobile (React Native)    | `mobile/*`           | pnpm + Turborepo |
| Rust (encryption crates) | `rust/*`             | cargo            |
| Shared types/GraphQL     | `shared/*`           | pnpm + Turborepo |

---

## Prerequisites

- **Git** with SSH key for Forgejo access
- **Python 3.14.3+** via pyenv or system package
- **uv** (latest) — replaces pip entirely
- **Node.js 24.x** + **pnpm 10.x**
- **Rust stable** (rustup)
- **maturin** — for building PyO3 extensions (`pip install maturin`)
- **cargo-watch** (optional, for Rust dev mode) — `cargo install cargo-watch`
- **basedpyright** — `npm install -g pyright` or via Zed LSP

---

## Getting Started

### 1. Clone and bootstrap

```bash
git clone git@git.syntek-studio.com:syntek/syntek-modules.git
cd syntek-modules
```

### 2. Python virtual environment

```bash
uv venv
source .venv/bin/activate

# Install a backend module for development (repeat for each module you work on)
uv pip install -e "packages/backend/syntek-auth[dev]"
```

### 3. TypeScript and mobile packages

```bash
pnpm install
```

### 4. Rust crates

```bash
cargo build
```

### 5. Start development mode

```bash
./dev.sh
```

This starts the TypeScript watch mode (all packages via Turborepo) and the Rust watcher if
`cargo-watch` is installed. Python does not need a running server — modules are imported directly.

---

## Daily Workflow

1. Pull latest from `main`
2. Create a feature branch: `<story-id>/<short-description>` (e.g., `us042/syntek-auth`)
3. Activate the Python venv: `source .venv/bin/activate`
4. Start watch mode: `./dev.sh`
5. Write tests first (TDD) — see [TESTING.md](TESTING.md)
6. Run `./test.sh` before committing
7. Commit with Conventional Commits format
8. Open a pull request on Forgejo

---

## Code Quality

### Python

```bash
# Format
ruff format packages/backend/

# Lint (includes security, import order, Django-specific rules)
ruff check packages/backend/

# Type checking (basedpyright — configured in pyrightconfig.json)
basedpyright packages/backend/
```

### TypeScript

```bash
# Lint all packages
pnpm lint

# Format all
pnpm format

# Type check all
pnpm type-check
```

### Rust

```bash
# Format
cargo fmt

# Lint (clippy — treat warnings as errors in CI)
cargo clippy --all-targets --all-features -- -D warnings
```

### Markdown

```bash
pnpm lint:md
```

### Run everything

```bash
./test.sh
```

---

## Git Workflow

### Branch naming

```
<story-id>/<short-description>

Examples:
  us001/syntek-crypto
  us042/syntek-auth
  fix/argon2-memory-cost
  chore/update-pyo3-0.24
```

### Commit messages (Conventional Commits)

```
<type>(<scope>): <subject>

Types: feat, fix, refactor, test, docs, chore, perf, style

Examples:
  feat(syntek-auth): add Argon2id password hashing via Rust bridge
  fix(syntek-crypto): correct nonce reuse in AES-256-GCM encrypt_field
  test(syntek-permissions): add integration tests for object-level RBAC
  docs(syntek-invoicing): document VAT calculation service
  chore(deps): upgrade strawberry-graphql to 0.308.0
```

**Rules:**

- Subject line under 72 characters
- Imperative mood: "Add feature" not "Added feature"
- Body explains _why_, not _what_
- Reference the story ID in the body: `Closes US-042`

### Pull requests

Every PR must include:

1. A clear title summarising the change
2. A description explaining what changed and why
3. Story ID reference (e.g., `Closes US-042`)
4. A testing section describing how to verify
5. Passing CI (tests, linting, type checking)

---

## Environment Variables

Consuming projects provide environment variables to the modules. This repo itself needs no `.env`
files during development — all secrets come from environment variables at runtime in consumer
projects.

For running integration tests against a real Postgres database, create `.env.test`:

```bash
# .env.test — not committed
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/syntek_test
REDIS_URL=redis://localhost:6379/1
```

For publishing to the Forgejo registries (CI only):

```bash
FORGEJO_REGISTRY_URL=https://git.syntek-studio.com
FORGEJO_TOKEN=<token>
```

---

## Troubleshooting

### `uv` can't find Python 3.14

```bash
pyenv install 3.14.0
pyenv local 3.14.0
uv venv
```

### PyO3 build fails

Ensure maturin and the active venv are in sync:

```bash
source .venv/bin/activate
pip install maturin
cd rust/syntek-pyo3
maturin develop
```

### pnpm workspace package not found

```bash
pnpm install  # re-link workspace packages
```

### Rust clippy warnings treated as errors

Fix the warning — do not suppress with `#[allow(...)]` unless the warning is a known false positive
in the crate's context.

### basedpyright reports Django model errors

Ensure `django-stubs` is installed in the venv:

```bash
uv pip install django-stubs[compatible-mypy]
```

The `pyrightconfig.json` at the root already sets `typeCheckingMode = "standard"` which works well
with django-stubs.
