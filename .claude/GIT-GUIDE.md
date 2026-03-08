# Git Guide — syntek-modules

---

## Table of Contents

- [Branch Strategy](#branch-strategy)
- [Before Every Commit](#before-every-commit)
- [Before Every Push](#before-every-push)
- [Commit Message Format](#commit-message-format)
- [PR Flow](#pr-flow)

---

## Branch Strategy

```
us###/feature  →  testing  →  dev  →  staging  →  main
```

| Branch          | Purpose                                                                      |
| --------------- | ---------------------------------------------------------------------------- |
| `us###/feature` | Feature work scoped to a user story (e.g. `us004/shared-graphql-operations`) |
| `testing`       | Dev team QA — feature tests pass here before merging to dev                  |
| `dev`           | Integration branch — all in-progress features merged here                    |
| `staging`       | Pre-production — integration and acceptance tests run here                   |
| `main`          | Production-ready code — client-accepted releases only                        |

Branch names use the user story number prefix: `us###/<short-description>`.

---

## Before Every Commit

Run these two commands in order before every commit — no exceptions.

### Step 1 — Auto-fix

```bash
syntek-dev lint --fix
```

This auto-fixes everything that can be fixed automatically:

- `ruff check --fix` — Python lint issues and import ordering
- `eslint --fix` — TypeScript/JS lint issues
- `pnpm format` (Prettier `--write`) — TypeScript/JS/JSON/YAML/Markdown formatting
- `pnpm lint:md:fix` — Markdownlint issues
- `cargo clippy --fix --allow-dirty` — Rust lint suggestions

### Step 2 — Verify clean state

```bash
syntek-dev lint
```

Run without `--fix` to confirm everything passes after the auto-fix step. If any linter still fails,
fix the remaining issues manually before committing.

### Step 3 — Commit

Only commit once `syntek-dev lint` exits cleanly (exit code 0).

---

## Before Every Push

Run the full local CI pipeline before pushing any branch:

```bash
syntek-dev ci
```

This mirrors all four remote CI workflows (14 steps total). The output ends with `Safe to push.`
when all steps pass. See `.claude/CLI-TOOLING.md` for the full step-by-step breakdown.

Only push when `syntek-dev ci` passes.

---

## Commit Message Format

Use the following template for every commit:

```
<type>(<scope>): <Description> - <Summarise>

<Body>

Files Changed:
- path/to/file

Still to do:
- task

Version: <old> → <new>
```

### Type values

| Type       | When to use                                         |
| ---------- | --------------------------------------------------- |
| `feat`     | New feature or new module                           |
| `fix`      | Bug fix                                             |
| `refactor` | Code change that is neither a fix nor a new feature |
| `test`     | Adding or updating tests                            |
| `docs`     | Documentation only                                  |
| `chore`    | Tooling, config, dependencies, version bumps        |
| `ci`       | CI/CD workflow changes                              |
| `perf`     | Performance improvement                             |
| `style`    | Formatting only (no logic change)                   |

### Scope values

Use the affected area as scope. Examples:

| Scope           | Meaning                                          |
| --------------- | ------------------------------------------------ |
| `syntek-auth`   | The `syntek-auth` backend package                |
| `@syntek/ui`    | The `@syntek/ui` web package                     |
| `syntek-crypto` | The `syntek-crypto` Rust crate                   |
| `shared`        | The `shared/` types or GraphQL operations layer  |
| `tooling`       | Root-level tooling (package.json, turbo, eslint) |
| `ci`            | CI workflow files                                |
| `docs`          | Documentation files                              |

### Example commit messages

```
feat(syntek-auth): add passkey registration flow - implements WebAuthn Level 3

Adds a new GraphQL mutation `registerPasskey` backed by the py_webauthn library.
Encryption delegated to syntek-pyo3 encrypt_field for credential storage.

Files Changed:
- packages/backend/syntek-auth/syntek_auth/mutations/passkey.py
- packages/backend/syntek-auth/syntek_auth/schema.py
- packages/backend/syntek-auth/tests/test_passkey.py

Still to do:
- Add passkey login mutation
- Wire up frontend in @syntek/ui-auth

Version: 1.3.0 → 1.4.0
```

```
chore(tooling): add lefthook pre-commit hooks for lint enforcement

Installs lefthook and configures pre-commit to run syntek-dev lint --fix
followed by syntek-dev lint to block dirty commits.

Files Changed:
- .lefthook.yml
- package.json

Still to do:
- None

Version: 0.5.0 → 0.5.1
```

---

## PR Flow

All feature branches must travel the full promotion order. **Never skip a stage.**

```
us###/feature  →  testing  →  dev  →  staging  →  main
```

### Branch purposes

| Branch          | Purpose                                                                                  | Who acts here        |
| --------------- | ---------------------------------------------------------------------------------------- | -------------------- |
| `us###/feature` | All feature work — scoped to a single user story                                         | Developer            |
| `testing`       | Full QA — automated CI + manual testing by the QA team. This is where bugs are caught    | Developer + QA       |
| `dev`           | Secondary check — integration layer; catches anything missed in testing                  | Lead dev / tech lead |
| `staging`       | Pre-release — staged environment tested by select developers for feedback before release | Select devs / leads  |
| `main`          | Released — code is now available for all developers to use; triggers a release           | Maintainers          |

### PR gates

| Merge step                  | Gate                                                                    |
| --------------------------- | ----------------------------------------------------------------------- |
| `us###/feature` → `testing` | `syntek-dev ci` passes locally; PR opened to `testing` only             |
| `testing` → `dev`           | CI passes on `testing`; QA sign-off (manual + automated tests complete) |
| `dev` → `staging`           | CI passes on `dev`; lead dev sign-off; no regressions                   |
| `staging` → `main`          | Staging sign-off by select devs; `syntek-docs` PR approved              |

### Rules

- Feature branches always target `testing` — never `dev`, `staging`, or `main` directly
- `testing` → `dev` → `staging` → `main` is the only permitted promotion path
- A branch rejection at any stage goes back to the original `us###/feature` branch for fixes, then
  re-enters at `testing`

---

## Documentation Requirement

All contributions that add or change public API surface (new modules, new GraphQL types or
mutations, changed configuration keys) **must include a linked PR to `syntek-docs`**.

The canonical documentation for the full Syntek ecosystem is published at:

**[syntekstudio.com/dev/docs](https://syntekstudio.com/dev/docs)**

The `syntek-docs` repository uses Docusaurus. A PR to `syntek-modules` that introduces a new feature
will not be merged to `staging` or `main` until the corresponding `syntek-docs` PR is approved.

Include the `syntek-docs` PR link in the **Related Issues** section of your PR description.
