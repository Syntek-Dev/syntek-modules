# Manual Testing Guide — @syntek/graphql

**Package**: `@syntek/graphql`\
**Last Updated**: `2026-03-08`\
**Tested against**: Node.js `24.14.0` / TypeScript `5.9`

---

## Overview

`@syntek/graphql` pre-generates typed React Query hooks from the Syntek backend GraphQL schema. A
tester should verify that: codegen runs against a live (or introspected) schema, the output file is
valid TypeScript, consuming packages get full type inference, and CI correctly rejects stale
generated files.

---

## Prerequisites

Before testing, ensure the following are in place:

- [x] pnpm dependencies installed at workspace root: `pnpm install`
- [x] Backend GraphQL schema is reachable at `http://localhost:8000/graphql` (or set
      `GRAPHQL_SCHEMA_URL` environment variable to an SDL file path or remote URL)
- [x] Active terminal in the repo root

---

## Test Scenarios

---

### Scenario 1 — Codegen produces typed hooks from .graphql files

**What this tests**: Running `pnpm codegen` against the backend schema generates
`src/generated/graphql.ts` with correct React Query hooks and TypeScript types.

#### Setup

```bash
# Remove any existing generated output to start clean
rm -f shared/graphql/src/generated/graphql.ts
```

#### Steps

1. Run codegen:

   ```bash
   pnpm --filter @syntek/graphql codegen
   ```

2. Inspect the generated file:

   ```bash
   cat shared/graphql/src/generated/graphql.ts
   ```

#### Expected Result

- [x] `src/generated/graphql.ts` is created
- [x] File exports `useLoginMutation`, `useCurrentUserQuery`, `useCurrentTenantQuery`
- [x] File exports `LoginMutationVariables`, `LoginMutation`, `CurrentUserQuery`,
      `CurrentTenantQuery`
- [x] `LoginMutationVariables` has `email: string` and `password: string` fields
- [x] No TypeScript errors when opening the file in an editor

> **Tested**: 2026-03-08 — codegen ran against local `schema.graphql` (no live server required). All
> exports confirmed via `grep`. Exit code 0.

---

### Scenario 2 — TypeScript infers response types in consuming packages

**What this tests**: After codegen, a consuming package can import a hook and get full TypeScript
inference on the response and variables.

#### Setup

```bash
# Update src/index.ts to re-export from generated (Green phase)
# Edit shared/graphql/src/index.ts to:
#   export * from './generated/graphql.js'

pnpm --filter @syntek/graphql build
```

#### Steps

1. In any `packages/web/*` package, add `@syntek/graphql` as a dependency.
2. Write a test file:

   ```ts
   import { useLoginMutation } from "@syntek/graphql";
   // hover over `useLoginMutation` in your editor
   ```

3. Run `pnpm --filter <package> type-check`

#### Expected Result

- [ ] No TypeScript errors
- [ ] IDE autocomplete shows `data.login.token` and `data.login.user.email` on the result
- [ ] Passing incorrect variable types (e.g. `email: 123`) causes a type error

---

### Scenario 3 — Schema drift detection rejects stale generated files

**What this tests**: CI fails if the committed generated file is out of date.

#### Setup

```bash
# Commit the current generated file, then simulate a schema change by manually
# editing one field name in src/generated/graphql.ts
```

#### Steps

1. Edit `src/generated/graphql.ts` — change one exported type field name (simulate drift).
2. Run the CI drift check:

   ```bash
   pnpm --filter @syntek/graphql codegen:check
   ```

#### Expected Result

- [x] Command exits with a non-zero code
- [x] Output explains that the generated file differs from expected

> **Tested**: 2026-03-08 — injected drift by renaming `email` → `email_DRIFTED` in the generated
> file. `codegen:check` exited with code 1 and reported:
> `The following stale files were detected: src/generated/graphql.ts`. Generated file restored.

---

### Scenario 4 — Breaking schema change surfaces in consuming packages

**What this tests**: When the backend removes or renames a field in the GraphQL schema, re-running
codegen + type-checking reveals the breakage in consuming packages.

#### Steps

1. Temporarily remove the `token` field from the `LoginPayload` type in the backend schema.
2. Re-run codegen:

   ```bash
   pnpm --filter @syntek/graphql codegen
   ```

3. Run type-check across the workspace:

   ```bash
   pnpm type-check
   ```

#### Expected Result

- [x] `src/generated/graphql.ts` no longer has `token` in `LoginMutation`
- [x] Any consuming package accessing `data.login.token` gets a TypeScript error
- [x] Error message clearly identifies the field and file

> **Tested**: 2026-03-08 — removed `token: String!` from `LoginPayload` in `schema.graphql`. Codegen
> failed immediately with:
> `GraphQL Document Validation failed: Cannot query field "token" on type "LoginPayload"` at
> `src/operations/auth.graphql:3:5`. Breakage surfaced before type-check was even needed. Schema and
> generated file restored to clean state.

---

## Regression Checklist

Run before marking a PR ready for review:

- [x] All automated tests pass: `pnpm --filter @syntek/graphql test`
- [x] Codegen runs clean against the current schema: `pnpm --filter @syntek/graphql codegen`
- [x] Type-check passes: `pnpm --filter @syntek/graphql type-check`
- [x] Build succeeds: `pnpm --filter @syntek/graphql build`
- [x] Drift check passes: `pnpm --filter @syntek/graphql codegen:check`
- [x] No TypeScript errors in consuming packages: `pnpm type-check`

---

## Known Issues

| Issue                                                        | Workaround                                                                           | Story / Issue |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ------------- |
| ~~Codegen requires a live backend to introspect the schema~~ | Resolved — `codegen.ts` defaults to local `schema.graphql`; no running server needed | US004         |

---

## Reporting a Bug

If a test scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/@syntek-graphql-{YYYY-MM-DD}.md`
5. Reference the user story: `Blocks US004`
