# Test Status — US001 Monorepo Workspace Configuration

**Story**: US001 — Monorepo Workspace Configuration\
**Last Run**: `2026-03-06T16:30:00Z`\
**Run by**: Claude Code / local dev\
**Overall Result**: `PASS`\
**Coverage**: N/A (configuration tests — no production code paths)

---

## Summary

| Suite             | Tests  | Passed | Failed | Skipped |
| ----------------- | ------ | ------ | ------ | ------- |
| Unit              | 34     | 34     | 0      | 0       |
| Integration (BDD) | 5      | 5      | 0      | 0       |
| E2E               | 0      | 0      | 0      | 0       |
| **Total**         | **39** | **39** | **0**  | **0**   |

---

## Unit Tests

### pnpm Workspace

- [x] `test_web_packages_declared` — packages/web/\* is declared in pnpm-workspace.yaml
- [x] `test_mobile_packages_declared` — mobile/\* is declared in pnpm-workspace.yaml
- [x] `test_shared_packages_declared` — shared/\* is declared in pnpm-workspace.yaml

### uv Workspace

- [x] `test_uv_workspace_section_exists` — [tool.uv.workspace] section present
- [x] `test_backend_members_glob` — packages/backend/\* in uv workspace members
- [x] `test_python_version_constraint` — ruff target-version is py314

### Cargo Workspace

- [x] `test_workspace_resolver_v2` — Cargo uses resolver = "2"
- [x] `test_edition_2024` — workspace edition is "2024"
- [x] `test_crate_member_declared[rust/syntek-crypto]` — crate in workspace
- [x] `test_crate_member_declared[rust/syntek-pyo3]` — crate in workspace
- [x] `test_crate_member_declared[rust/syntek-graphql-crypto]` — crate in workspace
- [x] `test_crate_member_declared[rust/syntek-dev]` — crate in workspace
- [x] `test_encryption_deps_declared` — aes-gcm, argon2, hmac, sha2, zeroize present
- [x] `test_release_profile_lto` — LTO enabled in release profile

### Turborepo Pipeline

- [x] `test_task_declared[build]` — build task declared
- [x] `test_task_declared[test]` — test task declared
- [x] `test_task_declared[lint]` — lint task declared
- [x] `test_task_declared[type-check]` — type-check task declared
- [x] `test_task_declared[dev]` — dev task declared
- [x] `test_build_depends_on_upstream` — build depends on ^build
- [x] `test_test_task_has_coverage_output` — test task outputs coverage
- [x] `test_dev_is_persistent` — dev is persistent
- [x] `test_dev_not_cached` — dev has cache=false

### Directory Structure

- [x] `test_directory_exists[packages/backend]` — directory present
- [x] `test_directory_exists[packages/web]` — directory present
- [x] `test_directory_exists[mobile]` — directory present
- [x] `test_directory_exists[rust]` — directory present
- [x] `test_directory_exists[shared]` — directory present
- [x] `test_directory_exists[docs]` — directory present
- [x] `test_rust_crate_directory_exists[rust/syntek-crypto]` — crate directory present
- [x] `test_rust_crate_directory_exists[rust/syntek-pyo3]` — crate directory present
- [x] `test_rust_crate_directory_exists[rust/syntek-graphql-crypto]` — crate directory present
- [x] `test_rust_crate_directory_exists[rust/syntek-dev]` — crate directory present
- [x] `test_rust_crate_has_cargo_toml` — all crates have Cargo.toml

---

## Integration Tests (BDD)

- [x] `TypeScript packages are resolvable via pnpm` — pnpm install exits 0
- [x] `Backend package installs via uv` — uv pip install syntek-auth[dev] exits 0
- [x] `Rust crates compile via cargo` — cargo build exits 0 (PyO3 0.28.2, Python 3.14)
- [x] `Dev watch mode is available via the CLI` — syntek-dev --help lists "up" subcommand
- [x] `Test runner is available via the CLI` — syntek-dev --help lists "test" subcommand

---

## Known Failures

None.

---

## How to Run

```bash
# First-time setup
./install.sh
source .venv/bin/activate

# Unit tests only (fast, no subprocess calls)
syntek-dev test --python -m unit

# BDD integration tests
syntek-dev test --python -m integration

# Full workspace test suite
syntek-dev test --python
```
