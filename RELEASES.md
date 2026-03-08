# Releases

## v0.9.0 — 08/03/2026

**Branch**: `us005/ci-cd-pipeline`\
**Type**: MINOR\
**Story**: US005 — CI/CD Pipeline (Forgejo Actions)

### Highlights

- Full CI/CD pipeline now active across all three stacks (Python, TypeScript/Web, Rust). Every PR
  automatically runs lint, type-check, tests, and a dependency vulnerability audit before merge is
  permitted.
- **Dependency security scanning** — `pip-audit` (Python), `pnpm audit` (TypeScript/JS), and
  `cargo audit` (Rust) execute on every PR and fail the pipeline when any HIGH or CRITICAL CVE is
  detected, with a human-readable report visible in the Actions log.
- **Affected-only test runs** — the web layer uses Turborepo's `--affected` flag so that only
  packages touched by a commit are tested. The Python layer uses changed-files detection to scope
  `pytest` to the specific backend packages that changed, rather than running the full
  `packages/backend/` suite every time.
- **Coverage PR comments** — after each successful run, coverage data is posted directly to the PR
  as a bot comment (MishaKav/pytest-coverage-comment for Python, davelosert/vitest-coverage-report-action
  for TypeScript, lcov-reporter-action for Rust). Comments are guarded to only appear on PRs, not
  plain pushes.
- **43/43 CI validation tests** pass on branch `us005/ci-cd-pipeline` (08/03/2026). Test suite
  in `tests/ci/` validates YAML structure of all three workflow files against the US005 acceptance
  criteria.
- Sprint 02 (Design Tokens, CI/CD & Manifest Framework) is now fully complete — 20/20 points.

### Verify

```bash
# Run CI workflow structure tests
source .venv/bin/activate
uv run pytest tests/ci/ -v

# Full lint and type-check
syntek-dev check

# Full CI pipeline locally
syntek-dev ci
```

---

## v0.8.0 — 08/03/2026

**Branch**: `us003/design-token-system`\
**Type**: MINOR\
**Story**: US003 — Design Token System

### Highlights

- `shared/tokens/` (`@syntek/tokens`) — the canonical design token package for the entire Syntek UI
  ecosystem. Exports typed TypeScript constants covering colours, spacing, typography, font
  families, border radii, shadows, breakpoints, z-index, and opacity. Also ships a `tokens.css` file
  with CSS custom properties for web packages and a `nativewind.ts` export with a
  NativeWind-compatible theme object for React Native.
- `eslint-rules/no-hardcoded-design-values.js` — a custom ESLint rule enforcing that developers
  import design values from `@syntek/tokens` rather than scattering raw hex codes, magic spacing
  values, or hardcoded font sizes through component files. Applied globally to all `packages/web`
  and `mobile` source via `eslint.config.mjs`.
- `docs/GUIDES/TOKENS-INTEGRATION.md` — a practical integration guide covering how to consume
  `@syntek/tokens` from web and mobile packages, including import patterns, CSS variable usage, and
  NativeWind configuration.
- Sprint 02 (Design Tokens, CI/CD & Manifest Framework) completed 08/03/2026. US003 is the sole
  story in Sprint 02 and is now fully verified with Vitest unit tests and a Cucumber BDD feature
  spec.

### Verify

```bash
# Type-check the tokens package
pnpm --filter @syntek/tokens type-check

# Run the Vitest test suite
pnpm --filter @syntek/tokens test

# Confirm the ESLint rule loads without errors
pnpm lint
```

---

## v0.7.0 — 08/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: MINOR\
**Story**: Security infrastructure — SAST scanning, dependency automation, vulnerability disclosure

### Highlights

- `SECURITY.md` — public vulnerability disclosure policy; GitHub private vulnerability reporting,
  90-day response SLA, scope definitions, and dependency security notes
- `renovate.json` — Renovate dependency automation for all four stacks (npm, pip, cargo,
  github-actions); weekly Monday schedule; Europe/London timezone
- `.github/dependabot.yml` — Dependabot fallback for GitHub; all four ecosystems, same schedule
- `.github/workflows/codeql.yml` — CodeQL SAST scanning Python and TypeScript on push/PR and weekly;
  catches security vulnerabilities before they reach production
- `.forgejo/workflows/semgrep.yml` — Semgrep SAST for Forgejo CI; separate jobs for Python/Django
  and TypeScript/React
- `.forgejo/workflows/renovate.yml` — Renovate self-hosted workflow for Forgejo registry
- `docs/GUIDES/BRANCH-PROTECTION.md` — branch protection reference guide for maintainers
- `.github/setup-branch-protection.sh` removed — branch protection rules are now managed via web UI
  only to prevent unreviewed scripted changes

### Verify

```bash
# No executable verification — workflows run in CI on push/PR
# Manually: review .github/workflows/codeql.yml and .forgejo/workflows/semgrep.yml
```

---

## v0.6.0 — 08/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: MINOR\
**Story**: Extend `syntek-dev lint --fix` to cover Prettier and markdownlint auto-fix

### Highlights

- `syntek-dev lint --fix` now runs `pnpm format` (Prettier `--write`) and `pnpm lint:md:fix`
  (markdownlint-cli2 `--fix`) in addition to ruff and ESLint; one command now cleans the entire
  codebase across all linters
- New `--prettier` flag added — run Prettier in isolation without triggering all other linters:
  `syntek-dev lint --prettier` (check) or `syntek-dev lint --prettier --fix` (write)
- `lint:md:fix` script added to root `package.json` to wire markdownlint auto-fix into the CLI
- Sprint 01 (Repository Foundation) formally documented as complete — 114/114 tests passing across
  US001, US002, and US004

### Verify

```bash
syntek-dev lint --fix          # runs all linters with auto-fix
syntek-dev lint --prettier     # Prettier check only
syntek-dev lint --markdown --fix  # markdownlint auto-fix only
```

---

## v0.5.2 — 08/03/2026

**Branch**: `us004/shared-graphql-operations-package`\
**Type**: PATCH\
**Story**: Fix pnpm version conflict in GitHub Actions CI workflows

### Highlights

- `.github/workflows/web.yml` and `.github/workflows/graphql-drift.yml` — removed the hardcoded
  `version: "10.28.2"` key from the `pnpm/action-setup@v4` step in both workflows
- `pnpm/action-setup@v4` now reads the pnpm version directly from `packageManager: pnpm@10.31.0` in
  `package.json`, eliminating the version mismatch that caused CI to fail
- No functional, API, or schema changes — all tests remain green

### Verify

```bash
# CI passes without pnpm version conflict errors
# Check GitHub Actions run for web.yml and graphql-drift.yml
```

---

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
