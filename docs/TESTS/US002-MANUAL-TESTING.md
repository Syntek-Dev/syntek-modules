# Manual Testing Guide — US002 Shared TypeScript Types Package

**Story**: US002 — Shared TypeScript Types Package\
**Last Updated**: 2026-03-06\
**Tested against**: TypeScript 5.9 / Node.js 24.13.0

---

## Overview

Verifies that `@syntek/types` exports consistent TypeScript type definitions that
all web and mobile packages can import, that breaking changes fail compilation in
consuming packages, and that the build produces `.d.ts` declaration files.

---

## Prerequisites

- [x] `pnpm install` completed at repo root
- [x] Node.js 24.x and pnpm 10.x on PATH

---

## Test Scenarios

---

### Scenario 1 — Types import and resolve without errors

**What this tests**: AC1 — TypeScript resolves `@syntek/types` imports without errors

#### Steps

1. `pnpm --filter @syntek/types type-check`
2. Verify exit code 0 and no output

#### Expected Result

- [x] `tsc --noEmit` exits 0
- [x] No type errors in terminal output
- [x] All 14 named exports are resolvable: `ID`, `Timestamp`, `PaginatedResponse`, `ApiError`, `User`, `Session`, `Permission`, `Role`, `Tenant`, `TenantSettings`, `Notification`, `NotificationChannel`

---

### Scenario 2 — Breaking change causes compilation failure

**What this tests**: AC2 — Modifying a type in a breaking way fails compilation in consuming packages

#### Steps

1. In a consuming package's test file, write:
   ```typescript
   import type { User } from '@syntek/types'
   const u: User = {} // should error if User has required fields
   ```
2. Run `tsc --noEmit` in the consuming package
3. Observe the error output

#### Expected Result

- [x] TypeScript reports an error — required properties (`id`, `email`, `roles`) missing
- [x] The error clearly identifies which properties are missing
- [x] Removing any required field from `User` in `@syntek/types` and rebuilding causes downstream package type-check to fail

---

### Scenario 3 — Build produces declaration files

**What this tests**: AC3 — `.d.ts` files are present for all exports after build

#### Steps

1. `pnpm --filter @syntek/types build`
2. `ls shared/types/dist/`

#### Expected Result

- [x] `dist/` directory created
- [x] `dist/index.d.ts` present
- [x] `dist/index.d.ts.map` present
- [x] `dist/base.d.ts` present
- [x] `dist/auth.d.ts` present
- [x] `dist/tenant.d.ts` present
- [x] `dist/notifications.d.ts` present
- [x] `dist/index.js` present and starts with `export`

---

## Regression Checklist

Run before marking US002 as complete:

- [x] `pnpm --filter @syntek/types test` exits 0 (tsc + vitest both pass)
- [x] `pnpm --filter @syntek/types build` exits 0
- [x] All 9 build output files present in `dist/`
- [x] All 14 types exported from `index.ts`
- [x] `NotificationChannel` is a discriminated union, not `string`
- [x] `PaginatedResponse<T>` has `data`, `total`, `page`, `pageSize`
- [x] No `unknown` or empty-interface stubs remain in source files

---

## Known Issues

| Issue | Workaround | Story |
| ----- | ---------- | ----- |
| None | — | — |
