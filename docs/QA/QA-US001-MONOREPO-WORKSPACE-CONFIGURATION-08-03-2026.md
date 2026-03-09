# QA Report: US001 — Monorepo Workspace Configuration

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US001 — Monorepo Workspace
Configuration **Branch:** main (completed story) **Scope:** `pnpm-workspace.yaml`, `turbo.json`,
`Cargo.toml`, `pyproject.toml`, `package.json`, `tests/workspace/` **Status:** ISSUES FOUND

---

## Summary

The US001 monorepo workspace configuration is broadly correct and all 39 declared tests pass.
However, the implementation contains three real gaps: `rust/syntek-manifest` has been added to
`Cargo.toml` but is absent from the US001 test suite, leaving workspace membership tests out of sync
with the actual workspace; the `test_python_version_constraint` test checks the wrong
`pyproject.toml` field and would not catch a downgrade of `requires-python`; and the BDD integration
test for the uv scenario does not guard against the target package being absent.

---

## CRITICAL (Blocks deployment)

None identified.

---

## HIGH (Must fix before production)

### 1. `rust/syntek-manifest` is in `Cargo.toml` but absent from the US001 test suite

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/Cargo.toml` line 9 **File:**
`/mnt/archive/OldRepos/syntek/syntek-modules/tests/workspace/test_workspace_config.py` lines 62–66

`Cargo.toml` declares five workspace members:

```toml
"rust/syntek-crypto",
"rust/syntek-pyo3",
"rust/syntek-graphql-crypto",
"rust/syntek-dev",
"rust/syntek-manifest",   # added post-US001
```

`EXPECTED_RUST_CRATES` in `test_workspace_config.py` lists only the original four crates.
`test_crate_member_declared` and `test_rust_crate_directory_exists` will never fire against
`rust/syntek-manifest`. If that crate is removed from `Cargo.toml` by a refactor, the tests will not
catch the regression. The test status document (US001-TEST-STATUS.md) claims 39/39 passing but
`rust/syntek-manifest` is not listed as a verified crate, creating a gap between the stated test
coverage and the actual workspace state.

**Impact:** Workspace membership tests do not reflect the current workspace. A developer could
remove `rust/syntek-manifest` from the workspace without any test failure.

**Reproduce:** Remove `"rust/syntek-manifest"` from `Cargo.toml`, run the test suite; all 39 tests
still pass even though the workspace has been broken.

---

## MEDIUM (Should fix)

### 2. `test_python_version_constraint` checks `ruff.target-version`, not `requires-python`

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/tests/workspace/test_workspace_config.py`
lines 51–54

```python
def test_python_version_constraint(self, root_pyproject: dict) -> None:
    target = root_pyproject["tool"]["ruff"].get("target-version", "")
    assert "py314" in target
```

This test confirms the `ruff` linter target version is `py314`, not that the uv workspace
`requires-python` constraint enforces Python 3.14. The `pyproject.toml` has
`requires-python = ">=3.14"` but this is not the field the test checks. If someone changed
`requires-python` to `">=3.12"` (allowing Python 3.12 installs across the workspace), this test
would still pass because `ruff.target-version` is a separate setting.

---

### 3. Turborepo `lint` and `type-check` tasks depend on `^build` but produce no declared outputs

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/turbo.json` lines 9–14

```json
"lint": {
  "dependsOn": ["^build"]
},
"type-check": {
  "dependsOn": ["^build"]
}
```

Neither `lint` nor `type-check` declares an `outputs` array. Turborepo will re-run both tasks on
every invocation even when inputs have not changed, because without declared outputs there is
nothing to cache. The story acceptance criterion mentions "Turborepo change detection" but does not
explicitly require caching for `lint`/`type-check`. This is a performance regression that will
compound as the number of packages grows.

---

## LOW (Consider fixing)

### 4. BDD test `install_syntek_auth` does not verify the target directory exists before installing

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/tests/workspace/test_workspace_bdd.py` lines
83–92

The BDD integration test attempts to install `packages/backend/syntek-auth` in editable mode
(`uv pip install -e "{package_path}[dev]"`). If `syntek-auth` has not yet been scaffolded at that
path, the test fails with a `uv` path resolution error rather than a descriptive assertion failure.
The test does not check that the package directory exists before issuing the install command. The
BDD scenario's AC is "When I run
`uv venv && ... uv pip install -e packages/backend/syntek-auth[dev]`, Then the backend package
installs with all dev dependencies" — a path-not-found error is a different kind of failure from a
dependency resolution failure, and the test does not distinguish between them.

---

## Test Scenarios Needed

- Verify that `rust/syntek-manifest` is present in `EXPECTED_RUST_CRATES` and that
  `test_crate_member_declared` and `test_rust_crate_directory_exists` both fire for it
- Verify that `pyproject.toml` `requires-python` enforces `>=3.14` directly (not via
  `ruff.target-version`)
- Verify that the BDD `install_syntek_auth` step asserts the package directory exists before
  attempting the uv install

---

## Implementation Files Reviewed

| File                                                                                   | Purpose                            |
| -------------------------------------------------------------------------------------- | ---------------------------------- |
| `/mnt/archive/OldRepos/syntek/syntek-modules/pnpm-workspace.yaml`                      | JS workspace declaration           |
| `/mnt/archive/OldRepos/syntek/syntek-modules/turbo.json`                               | Turborepo pipeline config          |
| `/mnt/archive/OldRepos/syntek/syntek-modules/Cargo.toml`                               | Rust workspace root                |
| `/mnt/archive/OldRepos/syntek/syntek-modules/pyproject.toml`                           | uv workspace root + ruff config    |
| `/mnt/archive/OldRepos/syntek/syntek-modules/package.json`                             | Root package, scripts, engine pins |
| `/mnt/archive/OldRepos/syntek/syntek-modules/tests/workspace/test_workspace_config.py` | Unit tests                         |
| `/mnt/archive/OldRepos/syntek/syntek-modules/tests/workspace/test_workspace_bdd.py`    | BDD integration tests              |
| `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US001-TEST-STATUS.md`          | Test status doc                    |

---

## Overall Risk Rating

**Low**

The workspace configuration is functionally sound and the 39 declared tests pass. The primary risk
is the gap between `EXPECTED_RUST_CRATES` and the actual Cargo workspace — a regression in crate
membership would go undetected. The other two findings are test quality issues rather than
configuration defects. No acceptance criteria are missed by the implementation itself.

---

## Handoff Signals

- Run `/syntek-dev-suite:test-writer` to add `rust/syntek-manifest` to `EXPECTED_RUST_CRATES` and
  add a test asserting `pyproject.toml` `requires-python` contains `3.14`.
- Run `/syntek-dev-suite:completion` to update QA status for US001 once the High item is resolved.
