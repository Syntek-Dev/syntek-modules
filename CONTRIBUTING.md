# Contributing to syntek-modules

**Last Updated:** 08/03/2026 **Version:** 0.1.0 **Maintained By:** Syntek Development Team

---

## Table of Contents

- [Welcome](#welcome)
- [Code of Conduct](#code-of-conduct)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit and Push Workflow](#commit-and-push-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Questions and Support](#questions-and-support)

---

## Welcome

Thank you for your interest in contributing to syntek-modules. This is a foundational library used
across the Syntek ecosystem, so your contributions directly impact multiple projects and teams.

Before you start, please read our Code of Conduct and familiarise yourself with the project
structure by reading `README.md` and `.claude/CLAUDE.md`.

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please
review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating in this project.

**In summary:**

- Be respectful and inclusive — everyone belongs here
- Disagree constructively — focus on the idea, not the person
- Report violations in confidence to `dev@syntek-studio.com`

---

## Prerequisites

Before setting up your development environment, ensure you have the following installed:

| Tool/Platform  | Version                    | Purpose                                         |
| -------------- | -------------------------- | ----------------------------------------------- |
| **Git**        | Latest stable              | Version control                                 |
| **Node.js**    | 24.14.0 or later           | JavaScript/TypeScript runtime                   |
| **pnpm**       | 10.x or later              | JavaScript package manager                      |
| **Python**     | 3.14.x or later            | Python runtime                                  |
| **uv**         | Latest stable              | Python package manager                          |
| **Rust**       | Latest stable (via rustup) | Rust compiler and ecosystem                     |
| **PostgreSQL** | 18.x or later              | Database (for testing)                          |
| **Valkey**     | Latest stable              | Cache and task queue backend (Redis-compatible) |

**macOS users:** Install Xcode Command Line Tools:

```bash
xcode-select --install
```

**Linux users:** Use your package manager (apt, brew, dnf, etc.). See `docs/GUIDES/DEVELOPING.md`
for distribution-specific instructions.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone git@git.syntek-studio.com:syntek/syntek-modules.git
cd syntek-modules
```

### 2. Run the Install Script

The bootstrap script sets up everything in one go:

```bash
chmod +x install.sh && ./install.sh
```

This will:

- Check for required tools
- Create a Python virtual environment with `uv venv`
- Install all Python dev dependencies
- Install all JavaScript/TypeScript dependencies
- Build the `syntek-dev` CLI (Rust)
- Symlink `syntek-dev` to `~/.local/bin/`

### 3. Activate the Python Virtual Environment

```bash
source .venv/bin/activate
```

Add this line to your shell profile (`.zshrc`, `.bashrc`, etc.) to activate automatically:

```bash
# At the end of ~/.zshrc or ~/.bashrc
eval "$(cd /path/to/syntek-modules && source .venv/bin/activate)"
```

### 4. Verify Installation

```bash
syntek-dev --version
syntek-dev up --frontend
```

If both commands succeed, you're ready to develop.

---

## Development Workflow

### Branching

Create a new branch for each user story or feature. Follow the naming convention:

```text
us###/<short-description>
```

Where `###` is the user story number (e.g., `us004/shared-graphql-operations`).

```bash
git checkout -b us004/my-feature
```

### Running Services Locally

Start all development services:

```bash
syntek-dev up
```

Or start specific services:

```bash
syntek-dev up --frontend  # React/Next.js watch mode
syntek-dev up --storybook # @syntek/ui Storybook (port 6006)
syntek-dev up --rust      # Rust file watcher
```

### Running Tests

Run all tests across all layers:

```bash
syntek-dev test
```

Or run tests for a specific layer:

```bash
syntek-dev test --python              # Django/pytest
syntek-dev test --python --python-package syntek-auth  # One package
syntek-dev test --rust                # Rust crates
syntek-dev test --web                 # React/TypeScript
syntek-dev test --mobile              # React Native
syntek-dev test --e2e                 # End-to-end (Playwright)
```

See `.claude/CLI-TOOLING.md` for full `syntek-dev` command reference.

---

## Commit and Push Workflow

### Step 1: Lint and Auto-fix

Before committing, run the linter with auto-fix enabled. This fixes style issues automatically:

```bash
syntek-dev lint --fix
```

This will:

- Auto-fix Python imports and style (ruff)
- Auto-fix TypeScript/JavaScript style (ESLint)
- Auto-format code (Prettier)
- Auto-fix Markdown (markdownlint)
- Auto-fix Rust suggestions (clippy)

### Step 2: Verify Clean State

Run linters without `--fix` to confirm everything passes:

```bash
syntek-dev lint
```

If any linter fails, fix the issues manually before committing.

### Step 3: Commit

Only commit once `syntek-dev lint` passes (exit code 0).

Use the commit message format defined in `.claude/GIT-GUIDE.md`:

```text
<type>(<scope>): <Description> - <Summarise>

<Body>

Files Changed:
- path/to/file

Still to do:
- task

Version: <old> → <new>
```

**Example:**

```text
feat(syntek-auth): add passkey registration - implements WebAuthn Level 3

Adds a new GraphQL mutation `registerPasskey` backed by the py_webauthn library.
Encryption delegated to syntek-pyo3 for secure credential storage.

Files Changed:
- packages/backend/syntek-auth/syntek_auth/mutations/passkey.py
- packages/backend/syntek-auth/tests/test_passkey.py

Still to do:
- Add passkey login mutation

Version: 1.3.0 → 1.4.0
```

### Step 4: Run Full CI Before Pushing

Before pushing, run the full CI pipeline locally:

```bash
syntek-dev ci
```

This mirrors all 14 remote CI checks (Prettier, ESLint, markdownlint, TypeScript, Rust, Python
linters, and tests). The output will end with `Safe to push.` if all checks pass.

Only push if `syntek-dev ci` succeeds:

```bash
git push origin us004/my-feature
```

---

## Code Style

All code style is enforced automatically via the CLI. You do not need to memorise rules — the tools
handle it.

### Tools and Rules

| Layer          | Tool(s)          | What it checks                                     |
| -------------- | ---------------- | -------------------------------------------------- |
| **Python**     | ruff + pyright   | Imports, style, type correctness                   |
| **TypeScript** | ESLint + tsc     | Linting, type correctness, unused code             |
| **Rust**       | rustfmt + clippy | Formatting, safety warnings, clippy hints          |
| **Markdown**   | markdownlint     | Line length, code formatting, consistent structure |

### Key Rules (from `.claude/CODING-PRINCIPLES.md`)

- Maximum 750 lines per file (grace of 50)
- Simple algorithms over fancy ones
- Short, focused functions
- Eliminate special cases rather than patching with `if` statements
- Measure before optimising — no speed hacks without profiling

See `.claude/CODING-PRINCIPLES.md` for the complete list.

---

## Testing

Tests are required for all new features and bug fixes.

### Running Tests

```bash
# All layers
syntek-dev test

# Specific layer
syntek-dev test --python
syntek-dev test --rust
syntek-dev test --web

# With coverage
syntek-dev test --coverage

# Watch mode
syntek-dev test --web --watch
```

### Test Files Location

- **Backend:** `packages/backend/<module>/tests/`
- **Web/React:** `packages/web/<package>/__tests__/` or `.test.tsx`
- **Mobile:** `mobile/<package>/__tests__/`
- **Rust:** `rust/<crate>/tests/` and inline `#[cfg(test)]` modules

Test documentation goes in `docs/TESTS/` with the format `US###-TEST-STATUS.md` and
`US###-MANUAL-TESTING.md`.

---

## Pull Requests

### PR Flow

```text
us###/feature  →  testing  →  dev  →  staging  →  main
```

**Feature branches always target `testing`.** Never open a PR directly to `dev`, `staging`, or
`main`.

| Branch    | Purpose                                                                           |
| --------- | --------------------------------------------------------------------------------- |
| `testing` | Full QA — automated CI + manual testing. This is where bugs are caught and fixed. |
| `dev`     | Secondary check — integration layer to catch anything missed during testing.      |
| `staging` | Pre-release — tested by select developers in a staged environment before release. |
| `main`    | Released — code is available to all developers and triggers a production release. |

If a PR is rejected at any stage, fixes go back to the original `us###/feature` branch and re-enter
the flow at `testing`.

### PR Checklist

Before opening a pull request:

- [ ] All tests pass: `syntek-dev test`
- [ ] Full CI passes: `syntek-dev ci`
- [ ] Code is linted: `syntek-dev lint`
- [ ] Commit messages follow the format in `.claude/GIT-GUIDE.md`
- [ ] Version files have been updated (if applicable)
- [ ] Documentation has been updated (if applicable)
- [ ] CHANGELOG.md has been updated (if applicable)

### PR Description Template

Provide a clear description of your changes:

```markdown
## Summary

Brief description of the changes.

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring
- [ ] Tooling/CI

## Related Issues

Closes #(issue number)

## Testing

Describe how you tested the changes.

## Checklist

- [ ] Tests pass
- [ ] CI passes
- [ ] Code style is correct
- [ ] Documentation is updated
```

---

## Documentation Contributions

The canonical developer documentation for the entire Syntek ecosystem lives at:

**[syntekstudio.com/dev/docs](https://syntekstudio.com/dev/docs)**

This site is built with [Docusaurus](https://docusaurus.io) in the `syntek-docs` repository. Every
contribution to `syntek-modules` that introduces a new feature, changes an API, or adds a new module
**must also include a corresponding documentation PR to `syntek-docs`**.

### What requires a docs PR

| Change type                      | Docs PR required? |
| -------------------------------- | ----------------- |
| New module or package            | Yes               |
| New GraphQL type or mutation     | Yes               |
| Changed API or configuration key | Yes               |
| Bug fix (no API change)          | No                |
| Internal refactor                | No                |
| Tooling / CI change              | No                |

### How to submit docs

1. Fork or branch `syntek-docs`
2. Add or update the relevant page under the appropriate section
3. Open a PR to `syntek-docs` and link it in your `syntek-modules` PR description

Your `syntek-modules` PR will not be merged to `staging` or `main` until the linked `syntek-docs` PR
is also approved.

---

## Questions and Support

- **Full docs:** [syntekstudio.com/dev/docs](https://syntekstudio.com/dev/docs)
- **General questions:** Open a discussion on GitHub or Forgejo at `git.syntek-studio.com`
- **Setup help:** See `docs/GUIDES/DEVELOPING.md`
- **CLI reference:** See `.claude/CLI-TOOLING.md`
- **Git workflow:** See `.claude/GIT-GUIDE.md`
- **Security issues:** Email `security@syntek-studio.com` — do not open public issues
- **Other issues:** See `docs/GUIDES/ISSUES.md`

Welcome aboard! We're excited to see what you'll build.
