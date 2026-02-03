# GitHub Workflows Documentation

## Overview

All GitHub workflows use the **unified Syntek CLI** (`rust/project-cli`) for consistent execution across local development and CI/CD environments. This ensures that what works locally works in CI, and vice versa.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Workflows                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CI     │  │   Lint   │  │   Test   │  │ Security │   │
│  │ Pipeline │  │ Unified  │  │ Unified  │  │  Audit   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │              │          │
│       └─────────────┴──────────────┴──────────────┘          │
│                           ▼                                   │
│              ┌─────────────────────────┐                     │
│              │   Syntek CLI (Rust)    │                     │
│              │  rust/project-cli      │                     │
│              └─────────────────────────┘                     │
│                           ▼                                   │
│       ┌──────────────┬───────────────┬──────────────┐       │
│       ▼              ▼               ▼              ▼        │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    │
│   │  NPM   │    │ Python │    │  Rust  │    │  All   │    │
│   │  pnpm  │    │   uv   │    │ Cargo  │    │Ecosys. │    │
│   └────────┘    └────────┘    └────────┘    └────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Available Workflows

### 1. CI/CD Pipeline (`ci.yml`)

**Main unified pipeline** - Runs on all pushes and PRs.

**Trigger:**

```yaml
on:
  push:
    branches: [main, develop, staging, testing]
  pull_request:
    branches: [main, develop, staging, testing]
```

**Jobs:**

- `setup` - Install dependencies, build CLI (cached)
- `lint` - Run `syntek lint` & `syntek format --check`
- `test` - Run `syntek test` with services (Postgres, Redis)
- `build` - Run `syntek build --mode production`
- `security` - Run `syntek audit`
- `summary` - Post CI/CD summary

**CLI Commands Used:**

```bash
syntek lint
syntek format --check
syntek test
syntek build --mode production
syntek audit --format json --output security-audit.json
```

### 2. Unified Lint (`lint.yml`)

**Complete linting** for all ecosystems in a single job.

**Trigger:**

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
```

**CLI Commands Used:**

```bash
syntek lint           # Lints Python, TypeScript, Rust
syntek format --check # Checks formatting across all files
```

**What it does:**

- Python: `ruff check .`
- TypeScript: ESLint on all packages
- Rust: `cargo clippy`
- All: Prettier/rustfmt formatting checks

### 3. TypeScript Lint (`lint-typescript.yml`)

**TypeScript-specific** linting with formatting and type checking.

**Trigger:** Changes to `*.ts`, `*.tsx`, `*.js`, `*.jsx` files

**CLI Commands Used:**

```bash
syntek format --check  # Check TypeScript formatting
```

**Additional checks:**

- ESLint on web/mobile/shared packages
- Prettier formatting
- TypeScript type checking (`pnpm typecheck`)

### 4. Python Lint (`lint-python.yml`)

**Python-specific** linting with Ruff and mypy.

**Trigger:** Changes to `*.py` files

**CLI Commands Used:**

```bash
syntek format --check  # Check Python formatting
```

**Additional checks:**

- Ruff linting and formatting
- mypy type checking

### 5. Rust Lint (`lint-rust.yml`)

**Rust-specific** linting with Clippy and rustfmt.

**Trigger:** Changes to `*.rs` files or `Cargo.toml`

**CLI Commands Used:**

```bash
syntek format --check  # Check Rust formatting
```

**Additional checks:**

- Clippy linting
- rustfmt formatting

### 6. Build (`build.yml`)

**Build all projects** for production.

**Trigger:**

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
```

**Jobs:**

- `build-all` - Unified build using `syntek build --mode production`
- `build-python-packages` - Build Python wheels for distribution
- `build-multi-arch-rust` - Build Rust for x86_64 & aarch64

**CLI Commands Used:**

```bash
syntek build --mode production
```

**Artifacts uploaded:**

- Web, mobile, shared builds
- Rust binaries (multi-architecture)
- Python wheel packages

### 7. Test (`test.yml`)

**Test all projects** with coverage reporting.

**Trigger:**

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
```

**Services:**

- PostgreSQL 18.1
- Redis 7

**CLI Commands Used:**

```bash
syntek test --env .env.test
```

**Coverage uploaded to:**

- Codecov (Python, TypeScript, Rust)
- GitHub Artifacts (HTML reports)

### 8. Security (`security.yml`)

**Comprehensive security scanning** across all ecosystems.

**Trigger:**

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM UTC
```

**Jobs:**

- `unified-security-audit` - Run `syntek audit` for all ecosystems
- `ruff-security-linting` - Python security rules
- `cargo-deny` - Rust supply chain security
- `dependency-review` - GitHub's dependency review (PRs only)
- `codeql` - CodeQL static analysis
- `secret-scan` - Gitleaks secret scanning
- `security-summary` - Aggregate results

**CLI Commands Used:**

```bash
syntek audit --format text --severity moderate
syntek audit --format json --output security-audit-report.json
syntek audit --format markdown --output SECURITY-AUDIT-REPORT.md
```

**Artifacts uploaded:**

- JSON audit report
- Markdown audit report

## Workflow File Mapping

| Workflow        | File                  | Primary CLI Command     |
| --------------- | --------------------- | ----------------------- |
| CI/CD Pipeline  | `ci.yml`              | All commands            |
| Unified Lint    | `lint.yml`            | `syntek lint`           |
| TypeScript Lint | `lint-typescript.yml` | `syntek format --check` |
| Python Lint     | `lint-python.yml`     | `syntek format --check` |
| Rust Lint       | `lint-rust.yml`       | `syntek format --check` |
| Build           | `build.yml`           | `syntek build`          |
| Test            | `test.yml`            | `syntek test`           |
| Security        | `security.yml`        | `syntek audit`          |

## CLI Caching Strategy

All workflows cache the syntek CLI binary to avoid rebuilding:

```yaml
- name: Cache syntek CLI
  uses: actions/cache@v4
  with:
    path: rust/project-cli/target/release/syntek
    key: ${{ runner.os }}-syntek-cli-${{ hashFiles('rust/project-cli/src/**') }}
```

**Cache invalidation:** Automatically rebuilds when CLI source code changes.

## Environment Setup Pattern

All workflows follow this pattern:

```yaml
1. Checkout code
2. Install Rust
3. Install Python + uv
4. Install Node.js + pnpm
5. Install dependencies (uv sync, pnpm install)
6. Cache & build syntek CLI
7. Install syntek CLI globally
8. Run syntek commands
```

## Local Development Equivalents

| Workflow       | Local Command                                |
| -------------- | -------------------------------------------- |
| CI Pipeline    | `syntek lint && syntek test && syntek build` |
| Lint           | `syntek lint`                                |
| Format Check   | `syntek format --check`                      |
| Format Fix     | `syntek format`                              |
| Test           | `syntek test`                                |
| Build (Dev)    | `syntek build --mode dev`                    |
| Build (Prod)   | `syntek build --mode production`             |
| Security Audit | `syntek audit`                               |
| Install Deps   | `syntek install`                             |
| Clean          | `syntek clean`                               |

## Workflow Status Badges

Add to README.md:

```markdown
[![CI/CD](https://github.com/syntek-dev/syntek-modules/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/syntek-dev/syntek-modules/actions)
[![Security](https://github.com/syntek-dev/syntek-modules/workflows/Security%20Scan/badge.svg)](https://github.com/syntek-dev/syntek-modules/actions)
[![Build](https://github.com/syntek-dev/syntek-modules/workflows/Build/badge.svg)](https://github.com/syntek-dev/syntek-modules/actions)
[![Tests](https://github.com/syntek-dev/syntek-modules/workflows/Test/badge.svg)](https://github.com/syntek-dev/syntek-modules/actions)
```

## Troubleshooting

### CLI Cache Issues

If the CLI behaves unexpectedly in CI:

1. Check cache key in workflow logs
2. Manually invalidate cache by modifying CLI source
3. Or clear GitHub Actions cache in repository settings

### Workflow Failures

**Common issues:**

1. **CLI not found**
   - Check if `cargo install --path rust/project-cli` succeeded
   - Verify `$HOME/.cargo/bin` is in PATH

2. **Dependencies missing**
   - Ensure `uv sync` and `pnpm install` ran successfully
   - Check for lockfile conflicts

3. **Test failures**
   - Verify services (Postgres, Redis) are healthy
   - Check environment variables

4. **Build failures**
   - Ensure all dependencies are installed
   - Check for syntax errors or linting issues first

### Debugging Workflows

Add debug output:

```yaml
- name: Debug environment
  run: |
    echo "Syntek CLI location: $(which syntek)"
    syntek --version
    echo "PATH: $PATH"
```

## Performance Optimization

**Current optimizations:**

1. **CLI caching** - Avoids rebuilding on every run (~2-3 min saved)
2. **Cargo caching** - Caches Rust dependencies (~1-2 min saved)
3. **pnpm caching** - Caches Node dependencies (~30s-1min saved)
4. **Parallel jobs** - Lint, test, build run in parallel
5. **Conditional execution** - Workflows only run on relevant file changes

**Expected workflow times:**

- Lint: ~2-3 minutes
- Test: ~5-7 minutes (with services)
- Build: ~3-5 minutes
- Security: ~4-6 minutes
- Full CI/CD: ~8-12 minutes (parallel)

## Best Practices

1. **Always use syntek CLI** - Don't run tools directly in workflows
2. **Test locally first** - Run `syntek` commands before pushing
3. **Keep CLI updated** - Update CLI when adding new functionality
4. **Monitor workflow times** - Optimize slow steps
5. **Use continue-on-error** - For non-critical checks (type checking, etc.)
6. **Upload artifacts** - For debugging and distribution
7. **Add summaries** - Use `$GITHUB_STEP_SUMMARY` for readability

---

## Pre-commit Framework

### Why `.pre-commit-config.yaml`?

For this multi-language repository (Python, TypeScript/JavaScript, Rust), we use the **pre-commit framework** for local development and CI/CD consistency.

#### Language-Agnostic

- Works seamlessly across all languages
- Single tool to manage hooks for the entire repository
- No need for language-specific hook managers (husky, cargo-husky)

#### Industry Standard

- Most widely adopted multi-language hook framework
- Over 1M+ repositories use it
- Extensive ecosystem of pre-built hooks
- Active maintenance and community support

#### Performance

- Runs only on changed files by default
- Parallel execution of independent hooks
- Smart caching of tool environments
- Can skip expensive checks locally and run in CI

#### Developer Experience

- Simple installation: `pip install pre-commit && pre-commit install`
- Consistent interface across all tools
- Clear error messages with fix suggestions
- Easy to update: `pre-commit autoupdate`

#### CI/CD Integration

- Same configuration runs locally and in CI (`.github/workflows/pre-commit.yml`)
- Ensures consistency between environments
- Can run different hook stages (pre-commit, manual)
- Caches hook environments for faster CI runs

### Comparison: Alternatives

#### Husky (JavaScript/Node)

- ❌ Node.js only (doesn't work well with Python/Rust)
- ❌ Requires npm/yarn/pnpm in all contexts
- ❌ Less mature Python/Rust integration
- ✅ Popular in JS ecosystem

#### cargo-husky (Rust)

- ❌ Rust only
- ❌ Limited hook library
- ❌ Not well-suited for monorepos
- ✅ Native Cargo integration

#### Custom Git Hooks

- ❌ Manual maintenance
- ❌ No automatic updates
- ❌ Hard to share across team
- ❌ No caching or optimization
- ✅ Complete control

#### lefthook (Go-based)

- ✅ Fast and parallel
- ✅ Multi-language support
- ❌ Smaller ecosystem
- ❌ Less mature than pre-commit
- ❌ Fewer pre-built hooks

### Pre-commit Advantages for Syntek Modules

#### 1. Unified Tooling

All languages use the same hook system:

- Python: ruff, mypy
- JS/TS: eslint, prettier
- Rust: cargo fmt, clippy
- Markdown: markdownlint
- Secrets: detect-secrets

#### 2. Flexible Execution

```bash
# Run all hooks
pre-commit run --all-files

# Run specific language
pre-commit run ruff --all-files       # Python only
pre-commit run eslint --all-files     # JS/TS only
pre-commit run rust-fmt --all-files   # Rust only

# Skip expensive checks
SKIP=mypy,typescript-check git commit -m "wip"
```

#### 3. Stage-based Hooks

- **Default stage** - Runs on every commit (lint, format)
- **Manual stage** - Run explicitly or in CI (tests, migrations, security scans)
- **Commit-msg stage** - Validates commit messages (conventional commits)

See [PRE-COMMIT-SETUP.md](PRE-COMMIT-SETUP.md) for detailed setup and usage.

---

## Future Enhancements

- [ ] Add deployment workflows (staging, production)
- [ ] Implement release automation
- [ ] Add performance benchmarking
- [ ] Integrate with project management tools
- [ ] Add automated dependency updates (Dependabot/Renovate)
- [ ] Implement preview deployments for PRs
- [ ] Add more granular test parallelization
