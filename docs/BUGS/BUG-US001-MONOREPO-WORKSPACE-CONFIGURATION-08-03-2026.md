# BUG REPORT — US001: Monorepo Workspace Configuration

**Date:** 08-03-2026 **Reporter:** QA Analysis **Status:** Fixed

## Findings Fixed

### BUG-001: `rust/syntek-manifest` missing from test suite's EXPECTED_RUST_CRATES

- **Severity:** High
- **Location:** `tests/workspace/test_workspace_config.py`:62-66
- **Root Cause:** The `EXPECTED_RUST_CRATES` list was not updated when `rust/syntek-manifest` was
  added to `Cargo.toml` in US074. The crate directory parametrisation also used a hardcoded list
  instead of referencing the constant.
- **Fix Applied:** Added `"rust/syntek-manifest"` to `EXPECTED_RUST_CRATES` and changed
  `test_rust_crate_directory_exists` to use the `EXPECTED_RUST_CRATES` constant instead of a
  duplicate hardcoded list.
- **Tests Added:** No new tests — existing parametrised tests now cover the additional crate.

### BUG-002: `test_python_version_constraint` checks wrong field

- **Severity:** Medium
- **Location:** `tests/workspace/test_workspace_config.py`:51-54
- **Root Cause:** The test checked `ruff.target-version` instead of `project.requires-python`. These
  are independent settings — `ruff.target-version` controls linter checks while `requires-python`
  controls the actual Python version constraint for the workspace.
- **Fix Applied:** Split into two tests: one checking `requires-python` contains `3.14`, and a
  separate test verifying `ruff.target-version` is `py314`.
- **Tests Added:** Yes — added `test_ruff_target_version_matches` as a separate assertion.

### BUG-003: Turborepo `lint` and `type-check` tasks have no declared outputs

- **Severity:** Medium
- **Location:** `turbo.json`:9-14
- **Root Cause:** The `lint` and `type-check` tasks did not declare an `outputs` array. Without
  explicit `outputs: []`, Turborepo cannot cache the result of these tasks, causing them to re-run
  on every invocation regardless of input changes.
- **Fix Applied:** Added `"outputs": []` to both `lint` and `type-check` tasks. An empty array
  signals to Turborepo that these tasks produce no file output but their exit code can still be
  cached.
- **Tests Added:** No — this is a configuration fix, not a code fix.

### BUG-004: BDD test does not verify target directory exists before uv install

- **Severity:** Low
- **Location:** `tests/workspace/test_workspace_bdd.py`:83-92
- **Root Cause:** The `install_syntek_auth` BDD step attempted to install `syntek-auth` without
  first verifying the package directory exists. If the package has not been scaffolded, the test
  fails with a uv path resolution error rather than a descriptive assertion message.
- **Fix Applied:** Added an `assert package_path.is_dir()` guard before the `subprocess.run` call
  with a descriptive failure message.
- **Tests Added:** No — this is a test quality improvement to an existing test.

## Findings Not Fixed (with reason)

None — all findings from the QA report have been addressed.
