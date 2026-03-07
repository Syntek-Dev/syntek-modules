# Releases

## v0.4.1 — 07/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: PATCH\
**Story**: Post-US004 tooling and housekeeping

### Highlights

- Markdownlint and ESLint configuration corrected — lint runs no longer flag generated files or
  `.claude/` internals
- Rust `syntek-dev` crate: Clippy warnings resolved (cleaner API signatures, flattened conditionals)
- TypeScript shared packages (`@syntek/graphql`, `@syntek/types`) normalised to consistent code style
- CI workflows (GitHub Actions + Forgejo) formatted consistently across all four pipeline files
- `pyrightconfig.json` simplified by removing settings that were redundant with pyproject.toml
- 144 documentation files reformatted for consistent Prettier output
- No functional or API changes — all existing tests remain green

### Verify

```bash
syntek-dev test --web
syntek-dev lint
cargo clippy -- -D warnings
```

---

## v0.4.0 — 06/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: MINOR\
**Story**: US004 — Shared GraphQL Operations Package

### Highlights

- `@syntek/graphql` — typed React Query hooks generated from the Syntek GraphQL schema
- `useLoginMutation`, `useCurrentUserQuery`, `useCurrentTenantQuery` with full TypeScript inference
- `pnpm codegen` regenerates types from `schema.graphql` SDL or a live schema URL
- `pnpm codegen:check` (CI + pre-commit) fails if generated files are out of date
- 29/29 Vitest tests green: codegen output verification + type-level assertions
- lefthook pre-commit hooks covering all four stack layers in parallel
- Per-layer CI workflows for GitHub and Forgejo (web, python, rust, graphql-drift)
- **Sprint 01 — Repository Foundation: 11/11 points complete** ✅

### Verify

```bash
syntek-dev test --web --web-package @syntek/graphql
# → Test Files  2 passed (2)
# → Tests  29 passed (29)
# → Type Errors  no errors
```

---

## v0.3.0 — 06/03/2026

**Branch**: `us002/shared-typescripts-package`\
**Type**: MINOR\
**Story**: US002 — Shared TypeScript Types Package

### Highlights

- `@syntek/types` — 14 TypeScript types exported from `shared/types/`
- 46/46 Vitest tests green: 37 type-assertion tests + 9 build-output tests
- `NotificationChannel` implemented as a proper discriminated union
- `tsc --noEmit && vitest run` chained test script — type errors block the suite
- Declaration files (`.d.ts`) generated via `pnpm --filter @syntek/types build`

### Verify

```bash
syntek-dev test --web --web-package @syntek/types
# → Test Files  2 passed (2)
# → Tests  46 passed (46)
```

---

## v0.2.0 — 06/03/2026

**Branch**: `us001/monorepo-workspace-config`\
**Type**: MINOR\
**Story**: US001 — Monorepo Workspace Configuration

### Highlights

- Full workspace test suite (39/39 passing via `syntek-dev test --python`)
- Python dependency lockfile (`uv.lock`) — `install.sh` now uses `uv sync` for reproducible installs
- PyO3 upgraded to 0.28.2 — all 4 Rust crates compile cleanly against Python 3.14.3
- `syntek-dev test --python` now discovers both `tests/` (workspace tests) and `packages/backend/`
  (module tests) automatically

### Install

```bash
git clone git@github-syntek:Syntek-Dev/syntek-modules
cd syntek-modules
./install.sh
source .venv/bin/activate
syntek-dev test --python
```

---

## v0.1.0 — 06/03/2026

**Branch**: `us001/monorepo-workspace-config`\
**Type**: MINOR\
**Story**: Initial scaffold

### Highlights

- Multi-stack monorepo scaffold (Python/uv, TypeScript/pnpm, Rust/cargo)
- `syntek-dev` CLI for `up`, `test`, `lint`, `format`, `db`, `check`, `open`
- 74 user stories across 8 epics, 45-sprint plan
- Full workspace configuration (pnpm, turbo, pyproject, Cargo)
