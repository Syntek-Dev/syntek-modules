# Releases

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
