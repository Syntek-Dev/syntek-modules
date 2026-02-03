# Security Audit Guide

## Overview

The `syntek audit` command provides unified security vulnerability scanning across all three ecosystems in the Syntek Modules repository:

- **NPM/PNPM** - JavaScript/TypeScript dependencies (web, mobile, shared)
- **Python/uv** - Python dependencies (backend, graphql)
- **Rust/Cargo** - Rust dependencies (rust crates)

## Quick Start

```bash
# Basic audit (text output, moderate+ severity)
syntek audit

# Audit with JSON output
syntek audit --format json

# Save report to file
syntek audit --format markdown --output audit-report.md

# Only show critical vulnerabilities
syntek audit --severity critical
```

## Command Options

| Option             | Description                                             | Default            |
| ------------------ | ------------------------------------------------------- | ------------------ |
| `--format`, `-f`   | Output format: `text`, `json`, `markdown`               | `text`             |
| `--severity`, `-s` | Minimum severity: `low`, `moderate`, `high`, `critical` | `moderate`         |
| `--output`, `-o`   | Save report to file (path)                              | None (stdout only) |

## Output Formats

### Text Format

Human-readable output with colored output and emoji indicators:

```bash
syntek audit --format text
```

### JSON Format

Machine-readable JSON for CI/CD integration:

```bash
syntek audit --format json --output report.json
```

### Markdown Format

Documentation-friendly format for reports and PRs:

```bash
syntek audit --format markdown --output SECURITY-REPORT.md
```

## What Gets Checked

### NPM/PNPM Ecosystem

- Runs `pnpm audit` against all workspace packages
- Checks web/packages/_, mobile/packages/_, shared
- Reports known CVEs from npm advisory database
- Suggests updates for vulnerable packages

### Python Ecosystem

- Runs `pip-audit` (automatically installed if missing)
- Scans all uv-managed dependencies
- Checks backend/ and graphql/ modules
- Reports CVEs and security advisories

### Rust Ecosystem

- Runs `cargo-audit` (automatically installed if missing)
- Scans rust/Cargo.toml dependencies
- Checks RustSec Advisory Database
- Reports unmaintained crates and known vulnerabilities

## Exit Codes

| Code | Meaning                               |
| ---- | ------------------------------------- |
| 0    | Success - no vulnerabilities found    |
| 1    | Vulnerabilities found or audit failed |

Note: Individual ecosystem failures don't stop the audit - all three will run regardless.

## CI/CD Integration

### GitHub Actions

The security workflow uses `syntek audit`:

```yaml
- name: Run unified security audit
  run: syntek audit --format json --severity moderate --output security-audit.json

- name: Upload audit report
  uses: actions/upload-artifact@v4
  with:
    name: security-audit-report
    path: security-audit.json
```

### Local Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running security audit..."
syntek audit --severity high

if [ $? -ne 0 ]; then
    echo "⚠️  Security vulnerabilities found!"
    echo "Run 'syntek audit' for details."
    echo "Use 'git commit --no-verify' to skip (not recommended)."
    exit 1
fi
```

### Daily Scheduled Audits

GitHub Actions cron (already configured in `.github/workflows/security.yml`):

```yaml
on:
  schedule:
    - cron: "0 2 * * *" # 2 AM UTC daily
```

## Severity Levels

| Level        | Description                                   | Action                 |
| ------------ | --------------------------------------------- | ---------------------- |
| **low**      | Minor issues, no immediate risk               | Review when convenient |
| **moderate** | Known vulnerabilities with low exploitability | Update within sprint   |
| **high**     | Serious vulnerabilities requiring attention   | Update within 48 hours |
| **critical** | Actively exploited or severe vulnerabilities  | **Update immediately** |

## Handling Vulnerabilities

### 1. Review the Report

```bash
syntek audit --format markdown --output AUDIT.md
```

Review the report to understand:

- Which packages are affected
- Severity of vulnerabilities
- Available patches/updates

### 2. Update Dependencies

For specific ecosystems:

```bash
# NPM packages
pnpm update [package-name]
pnpm audit --fix  # Auto-fix if possible

# Python packages
uv pip install --upgrade [package-name]
uv sync

# Rust packages
cargo update [crate-name]
```

Or update all at once:

```bash
syntek install  # Reinstalls all dependencies
```

### 3. Test After Updates

```bash
syntek test  # Run full test suite
```

### 4. Verify Fix

```bash
syntek audit  # Re-run audit
```

## Troubleshooting

### "Command not found: syntek"

Install the CLI:

```bash
./install-cli.sh
```

Or manually:

```bash
cd rust/project-cli
cargo install --path .
```

### "pip-audit not found"

The audit command automatically installs `pip-audit`. If it fails:

```bash
uv pip install pip-audit
```

### "cargo-audit not found"

The audit command automatically installs `cargo-audit`. If it fails:

```bash
cargo install cargo-audit
```

### False Positives

If a vulnerability is a false positive or not applicable:

1. **Document the decision** in `SECURITY.md`
2. **Add to ignore list** (ecosystem-specific):
   - NPM: `.npmrc` with `audit-level`
   - Python: `pip-audit --ignore-vuln`
   - Rust: `cargo-deny` configuration

## Best Practices

1. **Run regularly** - Integrate into CI/CD and run locally before commits
2. **Update promptly** - Don't accumulate security debt
3. **Document exceptions** - If you can't update, document why
4. **Test updates** - Always run tests after security updates
5. **Monitor advisories** - Subscribe to security mailing lists for your dependencies

## Additional Security Checks

Beyond dependency auditing, the repository also runs:

- **CodeQL** - Static analysis for code vulnerabilities
- **Gitleaks** - Secret scanning in git history
- **Ruff Security** - Python code security linting
- **ESLint Security** - JavaScript security patterns
- **Cargo Deny** - Rust supply chain security

Run all security checks:

```bash
# In CI
.github/workflows/security.yml

# Locally
syntek lint  # Includes security linting
syntek audit # Dependency scanning
```

## Resources

- [npm Advisory Database](https://github.com/advisories)
- [Python Security Advisories](https://github.com/pypa/advisory-database)
- [RustSec Advisory Database](https://rustsec.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Syntek Security Compliance](./.claude/SECURITY-COMPLIANCE.md)
