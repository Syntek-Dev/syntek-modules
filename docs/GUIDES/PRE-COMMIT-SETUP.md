# Pre-commit Setup Guide

This repository uses [pre-commit](https://pre-commit.com/) to automatically check code quality before commits.

## What Gets Checked

### All Files

- ✅ Trailing whitespace removal
- ✅ End-of-file fixer
- ✅ Line ending normalisation (LF)
- ✅ YAML/JSON/TOML validation
- ✅ Merge conflict detection
- ✅ Large file detection (>1MB)
- ✅ Private key detection
- ✅ Secret scanning

### Python (Django)

- ✅ **Ruff** - Fast linting (replaces flake8, isort, pyupgrade)
- ✅ **Ruff Format** - Code formatting (replaces black)
- ✅ **Pyright** - Modern static type checking (faster than mypy)
- ✅ **pytest** - Testing framework (TDD/BDD with pytest-bdd)
- ✅ Security checks via Ruff's `S` rules (flake8-bandit)

### JavaScript/TypeScript (Next.js, React Native)

- ✅ **ESLint** - Linting for JS/TS/React
- ✅ **Prettier** - Code formatting
- ✅ **TypeScript** - Type checking (tsc)

### Rust

- ✅ **cargo fmt** - Code formatting
- ✅ **cargo clippy** - Linting
- ✅ **cargo test** - Unit tests (manual stage)

### Django-specific

- ✅ `python manage.py check --deploy` (manual stage)
- ✅ `python manage.py makemigrations --check` (manual stage)

### Markdown

- ✅ **markdownlint** - Documentation formatting

### Commit Messages

- ✅ **Conventional Commits** - Enforces `type(scope): message` format

---

## Installation

### Quick Setup (Recommended)

Use the `syntek init` command for automated setup:

```bash
# Install all dependencies first
syntek install

# Initialize pre-commit hooks, secrets baseline, and dev tools
syntek init
```

This will:

- ✅ Check for required tools (uv, git, node, pnpm, cargo)
- ✅ Ensure Python virtual environment exists
- ✅ Install Python dev tools (pre-commit, detect-secrets, pyright, django-stubs)
- ✅ Install Rust components (rustfmt, clippy)
- ✅ Install Node dependencies
- ✅ Setup pre-commit Git hooks
- ✅ Create `.secrets.baseline` for secret scanning

**Optional: Skip specific steps:**

```bash
syntek init --skip-hooks      # Skip Git hooks setup
syntek init --skip-secrets    # Skip secrets baseline
syntek init --skip-dev-tools  # Skip dev tools installation
```

### Manual Setup (Alternative)

If you prefer to set up manually:

#### 1. Install pre-commit

```bash
# Install pre-commit tool
pip install pre-commit

# Or via uv (recommended)
uv pip install pre-commit
```

#### 2. Install Git hooks

```bash
# Install the pre-commit hooks into .git/hooks/
pre-commit install

# Also install commit-msg hook for conventional commits
pre-commit install --hook-type commit-msg
```

#### 3. Install language-specific dependencies

##### Python

```bash
uv pip install pytest pytest-bdd pytest-cov pytest-django pre-commit detect-secrets
```

##### JavaScript/TypeScript (includes pyright for Python type checking)

```bash
pnpm install  # Installs all dev dependencies including ESLint, Prettier, pyright
```

##### Rust

```bash
# Rust tools are already installed with Rust toolchain
rustup component add rustfmt clippy
```

---

## Usage

### Automatic (on git commit)

Once installed, pre-commit hooks run automatically when you commit:

```bash
git add .
git commit -m "feat(auth): add TOTP support"
# Pre-commit hooks run automatically here
```

### Manual run (all files)

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run all hooks including manual stages
pre-commit run --all-files --hook-stage manual
```

### Manual run (specific hooks)

```bash
# Run only Python linting
pre-commit run ruff --all-files

# Run only TypeScript checks
pre-commit run typescript-check --all-files

# Run only Rust formatting
pre-commit run rust-fmt --all-files
```

### Manual run (staged files only)

```bash
# Run on currently staged files
pre-commit run
```

---

## Bypassing Hooks (Emergency Use Only)

**⚠️ Not recommended - use only in emergencies!**

```bash
# Skip all pre-commit hooks
git commit --no-verify -m "emergency fix"

# Skip specific hook
SKIP=eslint git commit -m "fix: urgent patch"
```

---

## Hook Stages

Some hooks are set to **manual stage** and only run when explicitly requested:

| Hook                      | Stage  | Reason                           |
| ------------------------- | ------ | -------------------------------- |
| `rust-test`               | Manual | Slow - run in CI instead         |
| `django-check`            | Manual | Requires Django settings         |
| `django-migrations-check` | Manual | Requires database connection     |
| `pip-audit`               | Manual | Slow CVE scan - run periodically |

To run manual hooks:

```bash
pre-commit run --hook-stage manual --all-files
```

---

## Updating Hooks

Update to latest versions of all hooks:

```bash
pre-commit autoupdate
```

This updates the `rev:` fields in `.pre-commit-config.yaml`.

---

## Configuration Files

| File                      | Purpose                       |
| ------------------------- | ----------------------------- |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |
| `.secrets.baseline`       | Baseline for detect-secrets   |
| `.markdownlint.json`      | Markdown linting rules        |
| `pyproject.toml`          | Python tool configuration     |
| `eslint.config.js`        | ESLint configuration          |
| `.prettierrc`             | Prettier configuration        |

---

## Troubleshooting

### Hook fails but no error shown

```bash
# Run in verbose mode
pre-commit run --all-files --verbose
```

### Ruff/ESLint keeps failing

```bash
# Auto-fix issues
pre-commit run ruff --all-files
pre-commit run eslint --all-files
```

### Pyright type errors

```bash
# Check specific file with pyright
pnpm run typecheck:python

# Or check specific module
cd backend && pyright path/to/module/
```

### TypeScript errors

```bash
# Check web packages
cd web && pnpm typecheck

# Check mobile packages
cd mobile && pnpm typecheck
```

### Rust clippy warnings

```bash
# Check with detailed output
cd rust && cargo clippy --all-targets --all-features
```

### Django checks fail

```bash
# Run Django checks manually with settings
cd backend && DJANGO_SETTINGS_MODULE=your.settings python manage.py check --deploy
```

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit install --hook-type commit-msg
```

### Secret detected (false positive)

```bash
# Update baseline to allow specific secrets
detect-secrets scan --baseline .secrets.baseline

# Or add inline comment to ignore
API_KEY = "not-a-real-secret-example"  # pragma: allowlist secret
```

---

## CI/CD Integration

The same hooks run in CI/CD pipelines:

```yaml
# .github/workflows/ci.yml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files --hook-stage manual
```

This ensures consistency between local development and CI.

---

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes
- `perf`: Performance improvement
- `ci`: CI/CD changes
- `revert`: Revert previous commit

### Examples

```bash
git commit -m "feat(auth): add TOTP MFA support"
git commit -m "fix(payments): resolve Stripe webhook timeout"
git commit -m "docs(readme): update installation instructions"
git commit -m "refactor(api): simplify GraphQL resolvers"
```

**Note:** The pre-commit hook enforces this format and requires a scope!

---

## Performance Tips

### Speed up hooks

```bash
# Skip slow hooks during active development
SKIP=pyright,typescript-check,rust-clippy git commit -m "wip: testing"

# Run full checks before pushing
pre-commit run --all-files
```

### Parallel execution

Pre-commit runs hooks in parallel where possible. You'll see multiple hooks running simultaneously.

---

## Best Practices

1. **Run hooks before committing** - Fix issues early
2. **Keep commits small** - Faster hook execution
3. **Update hooks regularly** - `pre-commit autoupdate` monthly
4. **Don't bypass hooks** - They catch issues early
5. **Fix root causes** - Don't just disable failing hooks
6. **Review auto-fixes** - Check what was changed by formatters

---

## Getting Help

If pre-commit hooks are causing issues:

1. Run hooks manually: `pre-commit run --all-files --verbose`
2. Check specific tool: `ruff check backend/` or `eslint web/`
3. Read hook output carefully - it usually explains the issue
4. Consult tool documentation:
   - [Ruff](https://docs.astral.sh/ruff/)
   - [ESLint](https://eslint.org/docs/)
   - [Pyright](https://microsoft.github.io/pyright/)
   - [Prettier](https://prettier.io/docs/)
   - [Clippy](https://doc.rust-lang.org/clippy/)

---

## Summary

Pre-commit hooks ensure:

- ✅ Consistent code style across languages
- ✅ Security best practices
- ✅ No secrets committed
- ✅ Type safety (Python, TypeScript)
- ✅ Valid commit messages
- ✅ Passing linters before CI

**Install once, benefit forever!**
