# Pre-commit Hooks Summary

## Quick Setup

```bash
# Automated setup (recommended)
./scripts/setup-pre-commit.sh

# Or manual setup
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

## What Gets Checked

✅ **Python** - Ruff (lint + format), MyPy (types), Security rules
✅ **JavaScript/TypeScript** - ESLint, Prettier, TypeScript compiler
✅ **Rust** - cargo fmt, clippy
✅ **All Files** - Trailing whitespace, line endings, YAML/JSON validation
✅ **Security** - Secret scanning, private key detection
✅ **Commit Messages** - Conventional commits format

## Usage

```bash
# Automatic (on every commit)
git commit -m "feat(auth): add TOTP support"

# Manual (all files)
pre-commit run --all-files

# Manual (specific hook)
pre-commit run ruff --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "emergency fix"
```

## Commit Message Format

We enforce [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `revert`

**Examples:**

```bash
git commit -m "feat(auth): add TOTP MFA support"
git commit -m "fix(payments): resolve Stripe webhook timeout"
git commit -m "docs(readme): update installation instructions"
```

## Files Created

| File                               | Purpose                   |
| ---------------------------------- | ------------------------- |
| `.pre-commit-config.yaml`          | Hook configuration        |
| `.secrets.baseline`                | Secrets scanning baseline |
| `.markdownlint.json`               | Markdown linting rules    |
| `docs/PRE-COMMIT-SETUP.md`         | Detailed documentation    |
| `scripts/setup-pre-commit.sh`      | Automated setup script    |
| `.github/workflows/pre-commit.yml` | CI/CD integration         |

## Troubleshooting

**Hooks not running?**

```bash
pre-commit uninstall
pre-commit install
pre-commit install --hook-type commit-msg
```

**Auto-fix issues:**

```bash
pre-commit run --all-files  # Ruff, ESLint, Prettier auto-fix
```

**Skip slow checks during development:**

```bash
SKIP=mypy,typescript-check git commit -m "wip: testing"
```

## Documentation

- **Full setup guide:** [docs/PRE-COMMIT-SETUP.md](docs/PRE-COMMIT-SETUP.md)
- **Workflow documentation:** [docs/WORKFLOWS.md](docs/WORKFLOWS.md)
- **Main README:** [README.md](README.md)

## Why `.pre-commit-config.yaml`?

For multi-language repositories (Python, TypeScript, Rust), `.pre-commit-config.yaml` is the **industry standard** because:

1. ✅ **Language-agnostic** - Works across all languages
2. ✅ **Large ecosystem** - 1M+ repos use it
3. ✅ **Fast** - Parallel execution + smart caching
4. ✅ **CI integration** - Same config for local + CI
5. ✅ **Easy maintenance** - `pre-commit autoupdate`

**Alternatives considered:**

- ❌ **Husky** - Node.js only, poor Python/Rust support
- ❌ **cargo-husky** - Rust only, not suitable for monorepos
- ❌ **Custom hooks** - Manual maintenance, no optimization

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for detailed comparison.
