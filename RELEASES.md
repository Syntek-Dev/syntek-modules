# Releases

## v0.5.1 — 08/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: PATCH\
**Story**: Fix `.gitignore` `lib/` pattern incorrectly excluding `src/lib/fetcher.ts` from CI

### Highlights

- `.gitignore` — bare `lib/` and `lib64/` entries removed; these were silently excluding TypeScript
  `src/lib/` directories from the repository (Python virtualenv lib paths are already covered by
  `.venv/`, `venv/`, `env/`, and `build/`)
- `shared/graphql/src/lib/fetcher.ts` — file restored to the repository; was gitignored since US004
  landed, causing CI TypeScript build failures (`TS2307: Cannot find module`)
- No functional changes — `fetcher.ts` content is unchanged; all 29/29 graphql tests remain green

### Verify

```bash
syntek-dev test --web --web-package @syntek/graphql
pnpm type-check
```

---

## v0.5.0 — 07/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: MINOR\
**Story**: Add `syntek-dev ci` command, fix CI lint, add coverage, upgrade lefthook

### Highlights

- `syntek-dev ci` — run the full CI pipeline locally with a single command: Prettier, ESLint,
  markdownlint, type-check, Vitest (all packages), Rust fmt/clippy/test in sequence
- 175 markdownlint CI failures resolved — MD036 disabled for intentional user story bold convention;
  MD040/MD031/MD034 violations corrected across documentation and workflow files
- `@vitest/coverage-v8` added to `@syntek/graphql` for TypeScript test coverage reporting; coverage
  step added to `web.yml` in both GitHub Actions and Forgejo pipelines
- lefthook upgraded from `^1.0.0` to `^2.1.0` (installed 2.1.3)
- No API or schema changes — all 29/29 graphql tests and 46/46 types tests remain green

### Verify

```bash
syntek-dev ci
pnpm lint:md
syntek-dev test --web
```

---

## v0.4.2 — 07/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: PATCH\
**Story**: CI fixes, coverage tooling, lefthook upgrade

### Highlights

- 175 markdownlint CI failures resolved — MD036 disabled, MD040/MD031/MD034 violations corrected
  across documentation and CI configuration files
- `@vitest/coverage-v8` added to `@syntek/graphql` for TypeScript test coverage reporting
- Coverage report step added to `web.yml` in both GitHub Actions and Forgejo pipelines
- lefthook upgraded from `^1.0.0` to `^2.1.0` (installed 2.1.3)
- No functional or API changes — all existing tests remain green

### Verify

```bash
pnpm lint:md
syntek-dev test --web
```

---

## v0.4.1 — 07/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: PATCH\
**Story**: Post-US004 tooling and housekeeping

### Highlights

- Markdownlint and ESLint configuration corrected — lint runs no longer flag generated files or
  `.claude/` internals
- Rust `syntek-dev` crate: Clippy warnings resolved (cleaner API signatures, flattened conditionals)
- TypeScript shared packages (`@syntek/graphql`, `@syntek/types`) normalised to consistent code
  style
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
