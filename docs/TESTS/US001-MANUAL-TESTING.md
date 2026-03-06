# Manual Testing Guide — US001 Monorepo Workspace Configuration

**Story**: US001 — Monorepo Workspace Configuration\
**Last Updated**: 2026-03-06\
**Tested against**: Python 3.14.3 / Node.js 24.13.0 / Rust stable (PyO3 0.28.2)

---

## Overview

This guide verifies that a contributor can clone the repository and immediately
develop across all package layers (Python, TypeScript, Rust) from a single root
using consistent tooling — no per-layer setup beyond tool installation.

---

## Prerequisites

- [ ] `git`, `uv`, `pnpm`, `cargo`, `node` installed and on PATH
- [ ] Repository cloned: `git clone <repo-url> && cd syntek-modules`
- [ ] No `.venv`, `node_modules`, or `target/` from a previous install

---

## Test Scenarios

---

### Scenario 1 — pnpm workspace installation

**What this tests**: All TypeScript packages resolve from a single `pnpm install`

#### Steps

1. `pnpm install`
2. Verify no errors in output
3. `ls node_modules/.pnpm/` — confirm packages are present
4. `pnpm --filter '@syntek/*' list` — confirm all workspace packages are listed

#### Expected Result

- [ ] `pnpm install` exits 0
- [ ] All `packages/web/*`, `mobile/*`, `shared/*` packages are listed as workspace members
- [ ] No `ERR_PNPM_NO_MATCHING_VERSION` errors

---

### Scenario 2 — uv backend package installation

**What this tests**: A backend Django module installs with all dev dependencies

#### Setup

```bash
uv venv && source .venv/bin/activate
```

#### Steps

1. `uv pip install -e "packages/backend/syntek-auth[dev]"`
2. `python -c "import syntek_auth; print('OK')"`

#### Expected Result

- [ ] `uv pip install` exits 0
- [ ] `import syntek_auth` succeeds
- [ ] Dev dependencies (pytest, pytest-django, factory-boy) are importable

---

### Scenario 3 — Rust crate compilation

**What this tests**: All Rust crates compile from the workspace root

#### Steps

1. `cargo build`
2. Verify `target/debug/` contains compiled artefacts

#### Expected Result

- [ ] `cargo build` exits 0
- [ ] No compilation errors in output
- [ ] `syntek-crypto`, `syntek-pyo3`, `syntek-graphql-crypto`, `syntek-dev` all compiled

---

### Scenario 4 — Dev watch mode

**What this tests**: `./dev.sh` orchestrates watch modes for all active layers

#### Steps

1. `./dev.sh`
2. Observe terminal output for all layers starting
3. Press `Ctrl+C` to stop

#### Expected Result

- [ ] Script is executable (`ls -la dev.sh` shows `-rwxr-xr-x`)
- [ ] Watch mode starts for TypeScript (turborepo dev)
- [ ] Watch mode starts for Rust (cargo watch, if applicable)
- [ ] No unhandled errors on startup

---

### Scenario 5 — Full test suite

**What this tests**: `./test.sh` runs all tests across all layers and reports combined pass/fail

#### Steps

1. `./test.sh`
2. Observe output for each layer's test run
3. Verify combined exit code

#### Expected Result

- [ ] Script is executable
- [ ] Python tests run (pytest)
- [ ] TypeScript tests run (vitest via turbo)
- [ ] Rust tests run (cargo test)
- [ ] Final exit code reflects combined pass/fail

---

## Regression Checklist

- [x] All automated tests pass: `syntek-dev test --python` → 39/39
- [x] `pnpm install` completes without errors (frozen lockfile)
- [x] `syntek-auth` stub installs via `uv pip install -e packages/backend/syntek-auth[dev]`
- [x] `cargo build` exits 0 for all 4 crates (PyO3 0.28.2 / Python 3.14)
- [x] `syntek-dev up` subcommand is registered and listed in `--help`
- [x] `syntek-dev test` subcommand is registered and listed in `--help`

---

## Known Issues

| Issue | Workaround | Story |
| ----- | ---------- | ----- |
| `packages/backend/syntek-auth` is a minimal stub | Full module scaffolded in subsequent stories | US002+ |
