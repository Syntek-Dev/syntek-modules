# Test Status — @syntek/graphql

**Package**: `@syntek/graphql`\
**Last Run**: `2026-03-06T00:00:00Z`\
**Run by**: Green phase — implementation complete\
**Overall Result**: `PASS`\
**Coverage**: N/A (type-level + codegen output tests)

---

## Summary

| Suite | Tests | Passed | Failed | Skipped |
| ----- | ----- | ------ | ------ | ------- |
| Unit (type) | 17 | 17 | 0 | 0 |
| Integration (codegen output) | 12 | 12 | 0 | 0 |
| E2E | 0 | 0 | 0 | 0 |
| **Total** | **29** | **29** | **0** | **0** |

---

## Unit Tests

### Type inference — LoginMutationVariables

- [ ] `LoginMutationVariables.email is string` — email is a required string field
- [ ] `LoginMutationVariables.password is string` — password is a required string field
- [ ] `LoginMutationVariables is not Record<string, unknown>` — closed object, not an index signature

### Type inference — LoginMutation

- [ ] `LoginMutation has login field` — result shape has login property
- [ ] `login.token is string` — token returned from login is a string
- [ ] `login.user.id is string` — returned user id is a string
- [ ] `login.user.email is string` — returned user email is a string

### Type inference — CurrentUserQueryVariables

- [ ] `CurrentUserQueryVariables is Record<string, never>` — no variables required

### Type inference — CurrentUserQuery

- [ ] `CurrentUserQuery has me field` — result shape has me property
- [ ] `me.id is string` — user id is a string
- [ ] `me.email is string` — user email is a string
- [ ] `me.createdAt is string` — createdAt is an ISO timestamp string

### Type inference — CurrentTenantQueryVariables

- [ ] `CurrentTenantQueryVariables is Record<string, never>` — no variables required

### Type inference — CurrentTenantQuery

- [ ] `CurrentTenantQuery has currentTenant field` — result shape has currentTenant property
- [ ] `currentTenant.id is string` — tenant id is a string
- [ ] `currentTenant.slug is string` — tenant slug is a string
- [ ] `currentTenant.name is string` — tenant name is a string

---

## Integration Tests

### Codegen output — file existence

- [ ] `src/generated/graphql.ts exists` — codegen has been run

### Codegen output — auth hooks

- [ ] `exports useLoginMutation` — hook function present in generated file
- [ ] `exports useCurrentUserQuery` — hook function present in generated file
- [ ] `exports LoginMutationVariables type` — type alias present
- [ ] `exports LoginMutation type` — type alias present
- [ ] `exports CurrentUserQuery type` — type alias present
- [ ] `LoginMutationVariables contains email field` — codegen picked up schema field
- [ ] `LoginMutationVariables contains password field` — codegen picked up schema field

### Codegen output — tenant hooks

- [ ] `exports useCurrentTenantQuery` — hook function present in generated file
- [ ] `exports CurrentTenantQuery type` — type alias present

### Codegen output — module structure

- [ ] `generated file is a valid ES module` — contains export keyword
- [ ] `generated file contains a GraphQL document` — DocumentNode or gql tag present

---

## E2E Tests

> Not applicable to this shared utility package.

---

## Known Failures

| Test | Failure reason | Story / Issue |
| ---- | -------------- | ------------- |
| — | No failures | — |

---

## How to Run

```bash
# Full suite (type-check + vitest)
pnpm --filter @syntek/graphql test

# Watch mode
pnpm --filter @syntek/graphql test:watch

# Type-check only
pnpm --filter @syntek/graphql type-check

# Run codegen (needed for Green phase)
pnpm --filter @syntek/graphql codegen

# CI drift check (fails if generated files differ from committed)
pnpm --filter @syntek/graphql codegen:check
```

---

## Notes

- Tests intentionally fail in Red phase — this is correct TDD behaviour.
- `tsc --noEmit` will report type errors on `type-inference.test.ts` because the stub
  exports `Record<string, unknown>` instead of the real generated shapes.
- `codegen-output.test.ts` will fail at runtime because `src/generated/graphql.ts` is absent.
- To reach Green phase: run `pnpm codegen`, then update `src/index.ts` to re-export from
  `./generated/graphql.js`, then run `pnpm build`.
