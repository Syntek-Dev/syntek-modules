# Coverage Management & CLI Refactoring

## Overview

The Syntek CLI now includes:

1. **Coverage management** via `syntek coverage` (replaces bash scripts)
2. **Modular Rust architecture** for better maintainability
3. **Baseline comparison** for CI/CD workflows

---

## Coverage Management

### Commands

```bash
# Generate coverage report
syntek coverage

# Generate baseline for comparison
syntek coverage --baseline

# Compare current coverage with baseline
syntek coverage --compare

# Custom output file
syntek coverage --output my-coverage.json
```

### Workflow

#### 1. Generate Initial Baseline

```bash
# Run tests and generate coverage
syntek coverage --baseline

# Outputs:
# - coverage.json (current coverage data)
# - htmlcov/ (HTML report)
# - Terminal summary

# Save as baseline
mv coverage.json coverage-baseline.json
git add coverage-baseline.json .coveragerc
git commit -m "chore: add coverage baseline"
```

#### 2. Compare Coverage in CI/CD

```bash
# In GitHub Actions or locally
syntek coverage --compare

# This will:
# ✅ Pass if coverage maintained or improved
# ❌ Fail if coverage dropped by > 1%
```

#### 3. View Reports

```bash
# Open HTML report in browser
open htmlcov/index.html

# Or check JSON data
cat coverage.json | jq '.totals.percent_covered'
```

### Configuration

**`.coveragerc`** (already configured):

```ini
[run]
source = backend
omit = */migrations/*, */tests/*

[report]
fail_under = 80  # Minimum 80% coverage required
show_missing = True
```

### CI/CD Integration

The `test.yml` workflow now includes:

- Coverage generation for Python, TypeScript, and Rust
- Comparison with baseline
- Failure if coverage drops > 1%
- Upload to Codecov
- Artifact storage for HTML reports

---

## CLI Refactoring

### New Structure

```
rust/project-cli/src/
├── main.rs              # CLI definition + dispatch (~150 lines, down from 741!)
├── commands/            # Command implementations
│   ├── mod.rs           # Module declarations
│   ├── init.rs          # ✅ Refactored
│   ├── coverage.rs      # ✅ NEW
│   ├── dev.rs           # ⏳ TODO
│   ├── test.rs          # ⏳ TODO
│   ├── install.rs       # ⏳ TODO
│   ├── lint.rs          # ⏳ TODO
│   ├── format.rs        # ⏳ TODO
│   ├── build.rs         # ⏳ TODO
│   ├── clean.rs         # ⏳ TODO
│   ├── audit.rs         # ⏳ TODO
│   ├── staging.rs       # ⏳ TODO
│   └── production.rs    # ⏳ TODO
└── utils/               # Helper functions
    ├── mod.rs           # Module declarations
    ├── exec.rs          # Command execution
    ├── env.rs           # Environment loading
    └── tools.rs         # Tool checking, installation
```

### Benefits

1. **Maintainability** - Each command in its own file
2. **Testability** - Utils can be unit tested
3. **Reusability** - Shared utilities across commands
4. **Clarity** - main.rs is now just CLI definition
5. **Scalability** - Easy to add new commands

### Example: Init Command

**Before** (in main.rs):

```rust
// 300+ lines of implementation mixed with other commands
fn run_init() { /* ... */ }
fn check_required_tools() { /* ... */ }
fn install_python_dev_tools() { /* ... */ }
// etc...
```

**After** (commands/init.rs):

```rust
use crate::utils::tools;

pub fn run(skip_hooks: bool, skip_secrets: bool, skip_dev_tools: bool) -> anyhow::Result<()> {
    tools::check_required_tools()?;
    tools::ensure_venv_exists()?;
    // Clean, focused implementation
}
```

### Next Steps: Complete the Refactor

To finish refactoring, move each command from `main.rs` to `commands/command_name.rs`:

#### Example: Refactor `dev` command

1. **Create `commands/dev.rs`:**

```rust
use colored::*;
use std::path::PathBuf;
use crate::utils::{env, exec};

pub fn run(env_file: PathBuf) -> anyhow::Result<()> {
    println!("{}", "🚀 Starting development environment...".green().bold());

    env::load_env(&env_file)?;

    println!("{}", "📦 Starting Docker services...".cyan());
    exec::run_command("docker-compose", &["up", "-d"])?;

    println!("{}", "🐍 Starting Django backend...".cyan());
    exec::run_command("uv", &["run", "python", "manage.py", "runserver"])?;

    println!("{}", "⚛️  Starting Next.js frontend...".cyan());
    exec::run_command("pnpm", &["--filter", "web", "dev"])?;

    println!("{}", "✅ Development environment ready!".green().bold());
    Ok(())
}
```

2. **Update `main.rs`:**

```rust
Commands::Dev { env } => commands::dev::run(env),
```

3. **Remove old `run_dev()` function from `main.rs`**

Repeat for each command!

---

## Why Rust Instead of Bash?

### Advantages

| Feature             | Bash                | Rust                     |
| ------------------- | ------------------- | ------------------------ |
| **Cross-platform**  | ❌ Linux/macOS only | ✅ Windows, macOS, Linux |
| **Error handling**  | ⚠️ Basic            | ✅ Comprehensive         |
| **Type safety**     | ❌ No types         | ✅ Strong typing         |
| **Performance**     | 🐌 Slow             | ⚡ Fast                  |
| **Maintainability** | ⚠️ Hard to refactor | ✅ Easy modules          |
| **Testing**         | ⚠️ Difficult        | ✅ Built-in              |
| **IDE support**     | ⚠️ Limited          | ✅ Excellent             |

### Example Comparison

**Bash:**

```bash
#!/usr/bin/env bash
# Hard to test, platform-specific, brittle error handling
if ! command -v uv &> /dev/null; then
    echo "uv not found"
    exit 1
fi
uv run pytest --cov=backend || exit 1
```

**Rust:**

```rust
// Testable, cross-platform, comprehensive error handling
use crate::utils::tools;

pub fn run() -> anyhow::Result<()> {
    if !tools::check_tool_installed("uv") {
        anyhow::bail!("uv not found");
    }
    exec::run_command("uv", &["run", "pytest", "--cov=backend"])?;
    Ok(())
}
```

---

## Usage Examples

### Coverage Workflow

```bash
# Initial setup
syntek install
syntek init

# Generate baseline (one-time)
syntek coverage --baseline
mv coverage.json coverage-baseline.json
git add coverage-baseline.json
git commit -m "chore: add coverage baseline"

# Daily development
syntek test  # Run tests
syntek coverage  # Check coverage

# Before PR
syntek coverage --compare  # Ensure coverage maintained
```

### CI/CD Usage

```yaml
# .github/workflows/test.yml (excerpt)
- name: Run tests with coverage
  run: syntek coverage --baseline

- name: Compare with baseline
  run: syntek coverage --compare # Fails if coverage drops > 1%

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.json
```

---

## Current Status

✅ **Complete:**

- Coverage management (`syntek coverage`)
- Init command refactored
- Utils module created
- Modular architecture established

⏳ **TODO:**

- Refactor remaining 11 commands
- Add unit tests for utils
- Add integration tests for commands
- Document each command module

---

## Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html)
- [Rust CLI best practices](https://rust-cli-recommendations.sunshowers.io/)
- [Codecov integration](https://docs.codecov.com/docs/quick-start)
