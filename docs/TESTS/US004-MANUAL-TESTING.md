# Manual Testing Guide — @syntek/graphql

**Package**: `@syntek/graphql`\
**Last Updated**: `2026-03-06`\
**Tested against**: Node.js `24.14.0` / TypeScript `5.9`

---

## Overview

`@syntek/graphql` pre-generates typed React Query hooks from the Syntek backend GraphQL schema.
A tester should verify that: codegen runs against a live (or introspected) schema, the output
file is valid TypeScript, consuming packages get full type inference, and CI correctly rejects
stale generated files.

---

## Prerequisites

Before testing, ensure the following are in place:

- [ ] pnpm dependencies installed at workspace root: `pnpm install`
- [ ] Backend GraphQL schema is reachable at `http://localhost:8000/graphql`
  (or set `GRAPHQL_SCHEMA_URL` environment variable to an SDL file path or remote URL)
- [ ] Active terminal in the repo root

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

- [ ] `src/generated/graphql.ts` is created
- [ ] File exports `useLoginMutation`, `useCurrentUserQuery`, `useCurrentTenantQuery`
- [ ] File exports `LoginMutationVariables`, `LoginMutation`, `CurrentUserQuery`, `CurrentTenantQuery`
- [ ] `LoginMutationVariables` has `email: string` and `password: string` fields
- [ ] No TypeScript errors when opening the file in an editor

---

### Scenario 2 — TypeScript infers response types in consuming packages

**What this tests**: After codegen, a consuming package can import a hook and get
full TypeScript inference on the response and variables.

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
   import { useLoginMutation } from '@syntek/graphql'
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

- [ ] Command exits with a non-zero code
- [ ] Output explains that the generated file differs from expected

---

### Scenario 4 — Breaking schema change surfaces in consuming packages

**What this tests**: When the backend removes or renames a field in the GraphQL schema,
re-running codegen + type-checking reveals the breakage in consuming packages.

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

- [ ] `src/generated/graphql.ts` no longer has `token` in `LoginMutation`
- [ ] Any consuming package accessing `data.login.token` gets a TypeScript error
- [ ] Error message clearly identifies the field and file

---

## Regression Checklist

Run before marking a PR ready for review:

- [ ] All automated tests pass: `pnpm --filter @syntek/graphql test`
- [ ] Codegen runs clean against the current schema: `pnpm --filter @syntek/graphql codegen`
- [ ] Type-check passes: `pnpm --filter @syntek/graphql type-check`
- [ ] Build succeeds: `pnpm --filter @syntek/graphql build`
- [ ] Drift check passes: `pnpm --filter @syntek/graphql codegen:check`
- [ ] No TypeScript errors in consuming packages: `pnpm type-check`

---

## Known Issues

| Issue | Workaround | Story / Issue |
| ----- | ---------- | ------------- |
| Codegen requires a live backend to introspect the schema | Use a local SDL file as `schema` in `codegen.ts`, or start the Django dev server | US004 |

---

## Reporting a Bug

If a test scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/@syntek-graphql-{YYYY-MM-DD}.md`
5. Reference the user story: `Blocks US004`
