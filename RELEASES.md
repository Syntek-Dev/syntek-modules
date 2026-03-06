# Releases

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
- `syntek-dev test --python` now discovers both `tests/` (workspace tests) and `packages/backend/` (module tests) automatically

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
