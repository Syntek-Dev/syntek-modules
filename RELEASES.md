# Releases

## v0.14.0 — 11/03/2026

**Branch**: `us008/syntek-graphql-crypto`\
**Type**: MINOR\
**Story**: US008 — `syntek-graphql-crypto` GraphQL Encryption Middleware

### Highlights

- **`syntek-graphql-crypto` complete** — The GraphQL encryption middleware that prevents plaintext
  resolver output is fully implemented across both the Rust and Python layers. All sensitive fields
  annotated with `@encrypted` or `@encrypted(batch: "group_name")` in the Strawberry schema are
  automatically encrypted before the ORM write and decrypted after the resolver returns — with no
  crypto logic required in individual resolvers.

- **Strawberry `SchemaExtension` middleware** — `EncryptionMiddleware` intercepts
  `on_executing_start` (write path) and `on_executing_end` (read path). Individual fields use
  `encrypt_field` / `decrypt_field`; batch groups use `encrypt_fields_batch` /
  `decrypt_fields_batch` for a single call per group. On encrypt failure the mutation is rejected
  entirely — no partial ciphertext is written. On decrypt failure, individual fields are nulled with
  a structured error; batch group failures null all fields in the group with a single error.
  Unauthenticated requests receive null encrypted fields and a structured auth error; non-encrypted
  fields are never affected.

- **Key naming convention** — Per-field encryption keys are resolved from environment variables
  named `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>` (e.g. `SYNTEK_FIELD_KEY_USER_EMAIL`). The Rust layer is
  not configurable; all cryptographic algorithms and parameters are fixed by Syntek security policy.

- **59 tests, all green** — 13 Rust unit tests (`cargo test -p syntek-graphql-crypto`), 42 Python
  unit tests (`pytest packages/backend/syntek-graphql-crypto/tests/ -v`), and 4 integration tests
  (`pytest tests/graphql_crypto/ -v`) covering all 11 acceptance criteria.

### Breaking Changes

None.

### Verify

```bash
# Rust unit tests
cargo test -p syntek-graphql-crypto

# Python unit tests (no native extension required — syntek_pyo3 is mocked)
pytest packages/backend/syntek-graphql-crypto/tests/ -v

# Integration tests (requires maturin develop in rust/syntek-pyo3/ first)
pytest tests/graphql_crypto/ -v
```

---

## v0.13.0 — 09/03/2026

**Branch**: `us007/syntek-pyo3`\
**Type**: MINOR\
**Story**: US007 — `syntek-pyo3` PyO3 Django Bindings

### Highlights

- **`syntek-pyo3` native extension complete** — The PyO3 bridge between Django and `syntek-crypto`
  is fully implemented. `syntek_pyo3.so` is built with `maturin develop` (dev) or `maturin build`
  (production wheel). It exposes `encrypt_field`, `decrypt_field`, `hash_password`,
  `verify_password`, `encrypt_fields_batch`, and `decrypt_fields_batch` to Python with no
  cryptographic logic duplicated outside the `syntek-crypto` crate.

- **`EncryptedField` and `EncryptedFieldDescriptor`** — Django model fields are now protected by the
  `EncryptedField` type which prevents plaintext from ever reaching the database. The encryption
  boundary is the GraphQL middleware layer, not the ORM. `EncryptedField` stores and validates
  ciphertext only; `EncryptedFieldDescriptor` records model and field names for automatic AAD
  resolution by the middleware.

- **65 tests, all green** — 12 Rust integration tests (`cargo test -p syntek-pyo3`) and 53 Python
  unit tests (`pytest tests/pyo3/ packages/backend/syntek-pyo3/tests/ -v`) covering all acceptance
  criteria: import, round-trip, tamper rejection, AAD mismatch, batch ops, passthrough, and
  descriptor metadata.

- **Type stubs for basedpyright** — `stubs/syntek_pyo3.pyi` provides full type information for all
  eight exported symbols so the type checker resolves types without a compiled `.so`.

### Breaking Changes

None.

### Verify

```bash
# Rust tests
cargo test -p syntek-pyo3

# Python tests (requires maturin develop first)
source .venv/bin/activate
cd rust/syntek-pyo3 && maturin develop && cd ../..
pytest tests/pyo3/ packages/backend/syntek-pyo3/tests/ -v
```

---

## v0.12.1 — 09/03/2026

**Branch**: `us006/syntek-crypto`\
**Type**: PATCH\
**Story**: US006 — `syntek-crypto` Core Cryptographic Primitives (supply-chain tooling fix)

### Highlights

- **`cargo deny check` now passes** — `deny.toml` was rewritten for cargo-deny 0.16+ which
  introduced breaking configuration changes. The deprecated lint-level fields (`vulnerability`,
  `notice`, `unlicensed`, `copyleft`) were removed; `unmaintained = "warn"` was corrected to
  `unmaintained = "all"` (the field now accepts a scope string); `MPL-2.0` was added to the licence
  allow list (required by the `colored` crate in `syntek-dev`); and `AGPL-3.0` was corrected to the
  canonical SPDX identifier `AGPL-3.0-only`.

- **SPDX licence identifier corrected** — The root `Cargo.toml` workspace `license` field was
  corrected from the deprecated `"AGPL-3.0"` to `"AGPL-3.0-only"`, eliminating parse-error warnings
  produced by cargo-deny and `cargo metadata`.

- **`syntek-dev` marked as licensed** — `rust/syntek-dev/Cargo.toml` was missing
  `license.workspace = true`, causing cargo-deny to treat the crate as unlicensed. Now inherits the
  workspace licence.

- **Wildcard path dependency version pinning** — `rust/syntek-graphql-crypto/Cargo.toml` and
  `rust/syntek-pyo3/Cargo.toml` had `syntek-crypto` path dependencies without a `version` field.
  cargo-deny 0.16+ treats these as wildcard version constraints and rejects them when
  `wildcards = "deny"` is set. Both now specify `version = "0.12.0"`.

### Breaking Changes

None.

### Verify

```bash
# Confirm cargo deny passes
cargo deny check

# Full workspace still compiles
cargo build
```

---

## v0.12.0 — 09/03/2026

**Branch**: `us006/syntek-crypto`\
**Type**: MINOR\
**Story**: US006 — `syntek-crypto` Core Cryptographic Primitives\
**Sprint**: Sprint 03 — Completed 09/03/2026

### Highlights

- **`syntek-crypto` crate — complete** — The cryptographic foundation for all Syntek backend modules
  is now fully implemented. All sensitive fields are encrypted before any database write. No
  plaintext is ever stored or transmitted by the backend layer.

- **AES-256-GCM field encryption** — `encrypt_field` and `decrypt_field` use per-field Additional
  Authenticated Data (`model:field`) to bind ciphertexts to their origin. A ciphertext produced for
  `User:email` cannot be accepted by `User:phone` or any other field — the GCM authentication tag
  fails, preventing ciphertext transplantation attacks.

- **Argon2id password hashing** — `hash_password` and `verify_password` use the Syntek standard
  parameters: m=65536 KiB, t=3 iterations, p=4 lanes. These parameters are fixed by security policy
  and not configurable by consumers.

- **HMAC-SHA256 integrity** — `hmac_sign` and `hmac_verify` provide webhook signature and integrity
  verification. `hmac_verify` uses HMAC's constant-time comparison (via `subtle`) to prevent timing
  attacks.

- **Batch APIs** — `encrypt_fields_batch` and `decrypt_fields_batch` encrypt or decrypt multiple
  fields in a single call. If any field fails, the entire batch fails atomically — no partial
  results are returned.

- **Memory zeroisation** — All sensitive buffers are zeroised after use via the `zeroize` crate,
  meeting the OWASP Cryptographic Storage requirements.

- **Supply-chain policy** — `deny.toml` enforces cargo-deny rules: vulnerabilities denied, yanked
  crates denied, wildcard dependencies denied, only approved licences permitted.

- **CI fixes** — `cargo-audit` CVSS 4.0 crash resolved; `pip-audit` invocation corrected; coverage
  comment step guarded against missing XML output.

### Verify

```bash
# Run all syntek-crypto tests (unit + property-based + doctests)
cargo test -p syntek-crypto

# Clippy (zero warnings)
cargo clippy -p syntek-crypto -- -D warnings

# Format check
cargo fmt -p syntek-crypto -- --check
```

### Breaking Changes

None.

---

## v0.11.0 — 08/03/2026

**Branch**: `us075/design-token-manifest`\
**Type**: MINOR\
**Story**: US075 — Design Token Manifest

### Highlights

- **Design Token Manifest** — `TOKEN_MANIFEST` is now exported from `@syntek/tokens`. It is a
  frozen, readonly array of `TokenDescriptor` objects covering every designable token in the system:
  colour (semantic aliases), spacing, typography (font-size, weight, family), border radius, shadow,
  z-index, and transition (duration, easing). Each descriptor carries the CSS custom property name,
  the widget type for the `syntek-platform` branding form, a human-readable label, and a resolved
  default value. Colour defaults are hex strings — not `var()` references — so colour pickers can
  initialise without resolving variables.
- **Tailwind CSS v4 colour palette** — `TAILWIND_COLOURS` exports the full Tailwind v4 palette as a
  flat `{ "blue-600": "#2563eb", ... }` record covering all 22 families at scales 50–950. The
  companion `resolveTailwindColour(name)` utility looks up a palette name and returns the hex value
  (or `undefined`), enabling the platform colour picker's swatch tab to resolve user selections to
  concrete hex before persisting to `syntek-settings`.
- **CSS colour validation** — `isValidCssColour(value)` validates any CSS colour string: hex (3-,
  6-, and 8-digit), rgb(), rgba(), hsl(), hsla(), hwb(), lab(), lch(), oklab(), oklch(), and all CSS
  named colours. The function is the gating check the platform uses before writing an override to
  the DB.
- **Theme CSS generation** — `buildThemeStyle(overrides)` is the single integration surface between
  `@syntek/tokens` and `syntek-platform`. It converts a `{ [cssVar]: value }` override map into a
  `:root { ... }` CSS block. The platform calls this on save, minifies the output, hashes it, writes
  to `tenant_themes`, and serves it with `Cache-Control: immutable` from
  `/api/theme/{tenantId}.css?v={hash}`.
- **GraphQL codegen drift guard** — a new Forgejo workflow (`graphql-drift.yml`) now runs on every
  PR touching schema or operation files, blocking merge if the generated `graphql.ts` is stale.
- **Retrospective QA** — QA reports and bug fix reports produced for US001–US005, with test coverage
  gaps and assertion mismatches resolved in the test suite.

### Verify

```bash
# Run all @syntek/tokens tests
pnpm --filter @syntek/tokens test

# Type-check the full workspace
pnpm type-check

# Confirm GraphQL types are in sync
pnpm codegen && git diff --exit-code shared/graphql/src/generated/

# Full lint
syntek-dev lint
```

---

## v0.10.0 — 08/03/2026

**Branch**: `us074/module-manifest-spec-cli-shared-framework`\
**Type**: MINOR\
**Story**: US074 — Module Manifest Spec & CLI Shared Framework

### Highlights

- `rust/syntek-manifest` — the new shared Rust library crate that every Syntek module CLI binary
  links against. Implements the complete `syntek.manifest.toml` specification and all install-time
  behaviour: manifest parsing, interactive option prompts, Django `settings.py` writing, duplicate
  detection, provider wrapping, and post-install output formatting.
- **Manifest parser** — reads a `syntek.manifest.toml` file and deserialises it into a fully
  validated `SyntekManifest` struct. Descriptive errors report exactly which field is missing or has
  the wrong type so module authors get actionable feedback during development.
- **Interactive prompter** — renders each `options[]` entry from the manifest as a checkbox or
  select prompt in the developer's terminal, allowing per-install customisation without requiring
  manual flag passing.
- **`settings.py` writer** — generates a typed `SYNTEK_*` configuration block from the manifest's
  `settings[]` table and writes it into the consuming project's Django `settings.py`. If a block
  already exists the developer is prompted before any overwrite; declining leaves the file
  unchanged.
- **Duplicate detector** — scans `settings.py` for existing `INSTALLED_APPS` entries and `SYNTEK_*`
  blocks before writing, preventing accidental double-registration when a module is re-installed.
- **Provider wrapper** — reads `providers[]` from the manifest and wraps the declared `entry_point`
  file with the required provider boilerplate, ensuring consistent module entry-point structure
  across all packages.
- **Post-install printer** — formats `post_install_steps[]` as copy-paste-ready terminal output so
  developers always see the manual follow-up steps after `syntek add` completes.
- **127/127 tests pass** on branch `us074/module-manifest-spec-cli-shared-framework` (08/03/2026).
  Test suite in `rust/syntek-manifest/tests/` validates all six modules against their acceptance
  criteria. QA report: 26 findings identified and all resolved.

### Verify

```bash
# Run syntek-manifest unit and integration tests
cargo test -p syntek-manifest

# Build all Rust crates (confirms workspace compiles cleanly)
cargo build

# Full lint and type-check
syntek-dev check
```

---

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
  as a bot comment (MishaKav/pytest-coverage-comment for Python,
  davelosert/vitest-coverage-report-action for TypeScript, lcov-reporter-action for Rust). Comments
  are guarded to only appear on PRs, not plain pushes.
- **43/43 CI validation tests** pass on branch `us005/ci-cd-pipeline` (08/03/2026). Test suite in
  `tests/ci/` validates YAML structure of all three workflow files against the US005 acceptance
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
