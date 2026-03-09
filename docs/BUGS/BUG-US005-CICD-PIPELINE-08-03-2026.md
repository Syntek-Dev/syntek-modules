# BUG REPORT — US005: CI/CD Pipeline (Forgejo Actions)

**Date:** 08-03-2026 **Reporter:** QA Analysis **Status:** Fixed

## Findings Fixed

### BUG-001: `cargo audit` denies only `unsound` and `yanked` — known CVEs not denied

- **Severity:** High
- **Location:** `.forgejo/workflows/rust.yml`:43
- **Root Cause:** `cargo audit --deny unsound --deny yanked` does not deny CVE advisories classified
  as `vulnerability`. A crate with a known CVE would not fail CI. The story AC explicitly requires
  high/critical vulnerability detection.
- **Fix Applied:** Changed to `cargo audit --deny warnings` which denies all advisory categories
  including vulnerabilities, unmaintained crates, unsound code, and yanked crates.
- **Tests Added:** No new tests — existing `test_cargo_audit_deny_flag_present` and
  `test_cargo_audit_denies_vulnerabilities` tests already verify the `--deny` flag is present with a
  valid category. Updated the test docstring to reflect the new configuration.

### BUG-002: `pip-audit` invoked via `uvx` — audits ephemeral environment, not project venv

- **Severity:** High
- **Location:** `.forgejo/workflows/python.yml`:46
- **Root Cause:** `uvx pip-audit` creates an isolated ephemeral environment and audits its own
  dependencies, not the project's installed packages from `uv sync --all-extras`. The actual project
  dependencies go unaudited.
- **Fix Applied:** Changed from `uvx pip-audit` to `uv run pip-audit` which runs pip-audit within
  the project's virtual environment, auditing the correct set of installed packages.
- **Tests Added:** No new tests — existing `test_pip_audit_uses_uv_run` already accepts
  `uv run pip-audit` as valid.

### BUG-003: `cargo-audit` and `cargo-llvm-cov` installed without version pins

- **Severity:** High
- **Location:** `.forgejo/workflows/rust.yml`:41-48
- **Root Cause:** `cargo install cargo-audit` and `cargo install cargo-llvm-cov` install whatever
  the latest version is at runtime. A breaking change in either tool would break CI without any code
  change in the repository.
- **Fix Applied:** Pinned both tools to specific versions: `cargo install cargo-audit@0.21.1` and
  `cargo install cargo-llvm-cov@0.6.16`.
- **Tests Added:** No — this is a configuration fix. The existing tests verify the install commands
  are present.

### BUG-004: `.github/workflows/` mirror untested for divergence

- **Severity:** Medium
- **Location:** `.github/workflows/` (all three mirrored files)
- **Root Cause:** No test verified that the `.github/workflows/` mirror files were identical to the
  canonical `.forgejo/workflows/` files. A developer editing one directory and forgetting to update
  the other would not be caught.
- **Fix Applied:** Created `tests/ci/test_workflow_mirror.py` with parametrised tests that verify
  each mirrored workflow file is byte-identical to its canonical source. Also re-synced all four
  mirrored files.
- **Tests Added:** Yes — 8 new tests (existence and identity checks for 4 workflow files).

### BUG-005: `MishaKav/pytest-coverage-comment@main` unpinned

- **Severity:** Medium
- **Location:** `.forgejo/workflows/python.yml`:111
- **Root Cause:** Pinning to `@main` uses whatever the latest commit on the third-party action's
  main branch is at run time. A breaking change or security compromise would affect CI immediately.
- **Fix Applied:** Changed from `@main` to `@v1.1.54` (a specific release tag).
- **Tests Added:** No — this is a configuration fix.

### BUG-006: `fetch-depth: 0` in `python.yml` undocumented

- **Severity:** Medium
- **Location:** `.forgejo/workflows/python.yml`:23-25
- **Root Cause:** The `fetch-depth: 0` flag is required for the three-dot diff
  (`git diff "$BASE"...HEAD`) in the changed-package detection step, but this was not documented. A
  future maintainer could remove it unknowingly, breaking affected-package detection.
- **Fix Applied:** Added an inline YAML comment above `fetch-depth: 0` explaining that full history
  is required for the three-dot diff in the changed-package detection step.
- **Tests Added:** No — this is a documentation fix.

## Findings Not Fixed (with reason)

### `concurrency.cancel-in-progress: true` can cancel main branch runs

- **Reason:** Low severity. The current setting is not incorrect per the AC. Changing to
  `cancel-in-progress: ${{ github.event_name != 'push' || github.ref != 'refs/heads/main' }}` would
  add complexity. Documented for awareness but not changed as rapid merges to main are rare in this
  project's workflow.
