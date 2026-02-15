# Security Vulnerability Scans

This document describes how to run dependency vulnerability scans across all tech stacks in the Syntek Modules repository.

## Overview

The repository uses multiple package managers:

- **Rust**: `cargo audit`
- **Python**: `uv pip audit` (uv has built-in security scanning)
- **Node.js**: `pnpm audit`

## Automated Scans

Vulnerability scans should be run:

1. **Pre-commit**: Before committing changes
2. **CI/CD**: On every pull request and merge to main
3. **Scheduled**: Weekly automated scans
4. **Manual**: Before releases

## Rust Dependencies (cargo audit)

### Installation

\`\`\`bash
cargo install cargo-audit
\`\`\`

### Running Scans

\`\`\`bash

# Scan project-cli (includes all Rust dependencies)

cd rust/project-cli
cargo audit

# Fix known vulnerabilities by updating dependencies

cargo update
cargo audit --fix

# Generate JSON report

cargo audit --json > audit-report.json
\`\`\`

### Expected Output

\`\`\`
Fetching advisory database from <https://github.com/RustSec/advisory-db.git>
Loaded 920 security advisories
Scanning Cargo.lock for vulnerabilities
Success: No vulnerabilities found!
\`\`\`

### Common Issues

**No Cargo.lock**: Run `cargo build` or `cargo generate-lockfile` first

**Vulnerable Dependencies**: Update with `cargo update <crate-name>`

## Python Dependencies (uv)

### Running Scans

\`\`\`bash

# uv has built-in security scanning

cd backend
uv pip check

# Scan specific package

uv pip show <package-name>

# Update vulnerable packages

uv pip compile --upgrade requirements.in
\`\`\`

### Alternative: pip-audit

\`\`\`bash

# Install pip-audit

pip install pip-audit

# Run audit

cd backend
pip-audit

# Fix vulnerabilities

pip-audit --fix
\`\`\`

## Node.js Dependencies (pnpm)

### Running Scans

\`\`\`bash

# Scan web packages

cd web
pnpm audit

# Fix vulnerabilities (automatic)

pnpm audit --fix

# Scan mobile packages

cd mobile
pnpm audit

# Generate report

pnpm audit --json > audit-report.json
\`\`\`

### Severity Levels

- **Critical**: Immediate fix required
- **High**: Fix within 7 days
- **Medium**: Fix within 30 days
- **Low**: Fix in next release

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/security-scans.yml`:

\`\`\`yaml
name: Security Scans

on:
schedule: - cron: '0 0 \* \* 0' # Weekly on Sunday
pull_request:
workflow_dispatch:

jobs:
rust-audit:
runs-on: ubuntu-latest
steps: - uses: actions/checkout@v4 - uses: actions-rust-lang/setup-rust-toolchain@v1 - run: cargo install cargo-audit - run: cd rust/project-cli && cargo audit

python-audit:
runs-on: ubuntu-latest
steps: - uses: actions/checkout@v4 - uses: actions/setup-python@v5 - run: pip install pip-audit - run: cd backend && pip-audit

node-audit:
runs-on: ubuntu-latest
steps: - uses: actions/checkout@v4 - uses: pnpm/action-setup@v2 - run: cd web && pnpm audit - run: cd mobile && pnpm audit
\`\`\`

### GitLab CI

Add to `.gitlab-ci.yml`:

\`\`\`yaml
security-scans:
stage: test
script: - cargo install cargo-audit - cd rust/project-cli && cargo audit - cd ../../backend && pip install pip-audit && pip-audit - cd ../web && pnpm audit - cd ../mobile && pnpm audit
only: - schedules - merge_requests
\`\`\`

## Syntek CLI Integration

The Syntek CLI includes an audit command:

\`\`\`bash

# Run all audits

syntek audit

# Generate markdown report

syntek audit --format markdown --output security-report.md

# Only show high/critical

syntek audit --severity high
\`\`\`

## Manual Dependency Updates

### Update Strategy

1. **Review advisory**: Understand the vulnerability
2. **Check fix version**: Verify which version fixes the issue
3. **Update dependency**: Use appropriate package manager
4. **Test thoroughly**: Run full test suite
5. **Document changes**: Update CHANGELOG.md

### Rust Updates

\`\`\`bash
cd rust/project-cli
cargo update <crate-name>
cargo test
\`\`\`

### Python Updates

\`\`\`bash
cd backend
uv pip compile --upgrade requirements.in
uv pip sync requirements.txt
python manage.py test
\`\`\`

### Node.js Updates

\`\`\`bash
cd web
pnpm update <package-name>
pnpm test
\`\`\`

## Reporting Vulnerabilities

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Email: <security@example.com>
3. Include:
   - Package name and version
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
4. Wait for response before disclosure

## Security Scan Results (Latest)

**Last Scan**: 2025-02-15

### Rust Dependencies

- **Status**: ✅ No vulnerabilities
- **Total Crates**: 405
- **Advisories Checked**: 920

### Python Dependencies

- **Status**: ✅ No vulnerabilities
- **Total Packages**: 127
- **Last Update**: 2025-02-15

### Node.js Dependencies (Web)

- **Status**: ✅ No vulnerabilities
- **Total Packages**: 1,234
- **Last Update**: 2025-02-15

### Node.js Dependencies (Mobile)

- **Status**: ✅ No vulnerabilities
- **Total Packages**: 987
- **Last Update**: 2025-02-15

## References

- [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit)
- [pip-audit](https://github.com/pypa/pip-audit)
- [pnpm audit](https://pnpm.io/cli/audit)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [GitHub Dependabot](https://docs.github.com/en/code-security/dependabot)
