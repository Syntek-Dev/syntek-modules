# Changelog

All notable changes to `syntek-modules` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] — 06/03/2026

### Added

- **`shared/types/`** — `@syntek/types` package with full TypeScript type definitions (US002)
  - Base types: `ID`, `Timestamp`, `PaginatedResponse<T>`, `ApiError`
  - Auth types: `Permission`, `Role`, `User`, `Session`
  - Tenant types: `Tenant`, `TenantSettings`
  - Notification types: `NotificationChannel` (discriminated union), `Notification`
- **`shared/types/src/__tests__/`** — 46 Vitest type-assertion and build-output tests (all passing)
- **`shared/types/features/`** — BDD Gherkin scenarios for all US002 acceptance criteria
- **`shared/types/dist/`** — compiled `.d.ts` declaration files and ES module output (gitignored, built on demand)
- **`docs/TESTS/US002-TEST-STATUS.md`** — 46/46 PASS
- **`docs/TESTS/US002-MANUAL-TESTING.md`** — all scenarios verified

### Changed

- **`docs/STORIES/US002.md`** — status updated to Completed; all tasks ticked
- **`docs/SPRINTS/SPRINT-01.md`** — US002 marked Completed; sprint progress 8/11 points

---

## [0.2.0] — 06/03/2026

### Added

- **Test infrastructure** — root-level `tests/workspace/` suite (39 pytest tests) covering pnpm, uv, Cargo, and Turborepo workspace configuration (US001)
- **BDD tests** — `pytest-bdd` Gherkin scenarios matching all US001 acceptance criteria
- **`packages/backend/syntek-auth/`** — minimal pyproject.toml stub to enable uv workspace resolution
- **`uv.lock`** — deterministic Python dependency lock file (51 packages, Python 3.14)
- **`VERSION`**, **`CHANGELOG.md`**, **`VERSION-HISTORY.md`**, **`RELEASES.md`** — version tracking files
- **`[project]` section in `pyproject.toml`** — enables `uv sync` via `[dependency-groups]`
- **`[dependency-groups]` in `pyproject.toml`** — replaces ad-hoc `uv pip install` list in install.sh

### Changed

- **`Cargo.toml`** — PyO3 upgraded from `0.23` to `0.28.2` (adds Python 3.14 support)
- **`install.sh`** — Python setup now uses `uv sync --group dev` from the lockfile; venv activation consolidated; end-of-script reminder made prominent
- **`rust/syntek-dev/src/commands/test.rs`** — `syntek-dev test --python` now respects `testpaths` in `pyproject.toml` (discovers `tests/` and `packages/backend/` without an explicit path override)
- **`pyproject.toml`** — removed invalid `python-version` field from `[tool.uv]`; added `testpaths = ["tests", "packages/backend"]`
- **`docs/SPRINTS/SPRINT-01.md`** — sprint status updated to In Progress; US001 marked complete (5/11 points)
- **`docs/STORIES/US001.md`** — status updated to Completed; all tasks ticked

### Fixed

- **`Cargo.lock`** — updated to resolve PyO3 0.28.2 (previously 0.23.5 which blocked Python 3.14 builds)

---

## [0.1.0] — 06/03/2026

### Added

- Initial monorepo scaffold — `pnpm-workspace.yaml`, `turbo.json`, root `package.json`, `pyproject.toml`, `Cargo.toml`
- Rust workspace: `syntek-crypto`, `syntek-pyo3`, `syntek-graphql-crypto`, `syntek-dev` crates
- `syntek-dev` Rust CLI — `up`, `test`, `lint`, `format`, `db`, `check`, `open` commands
- Editor, formatter, and linter configuration (`.editorconfig`, `.prettierrc`, `eslint.config.mjs`, `ruff`, `basedpyright`)
- Package directory scaffolding (`packages/backend/`, `packages/web/`, `mobile/`, `shared/`)
- 74 user stories across 8 epics (`docs/STORIES/`)
- 45-sprint plan (`docs/SPRINTS/`)
- Architecture documentation (`docs/PLANS/SYNTEK-ARCHITECTURE.md`)
- `install.sh` — one-command dev environment bootstrap
- `.zed/settings.json` — project-level Zed IDE overrides
