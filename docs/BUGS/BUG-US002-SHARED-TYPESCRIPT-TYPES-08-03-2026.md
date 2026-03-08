# BUG REPORT — US002: Shared TypeScript Types Package

**Date:** 08-03-2026 **Reporter:** QA Analysis **Status:** Fixed

## Findings Fixed

### BUG-001: `ID` is an unbranded `string` — type confusion undetectable at compile time

- **Severity:** High
- **Location:** `shared/types/src/base.ts`:1
- **Root Cause:** `ID` was defined as `type ID = string`, making it fully interchangeable with plain
  strings. In a multi-tenant system, this means a `tenantId` can be silently passed where a `userId`
  is expected without any compiler warning.
- **Fix Applied:** Changed `ID` to a branded type: `string & { readonly __brand: "ID" }`. Values
  must be explicitly cast via `as ID`. This provides compile-time protection against accidental
  interchange.
- **Tests Added:** Yes — updated `exports.test.ts` to verify `ID` extends `string` but is not equal
  to `string`.

### BUG-002: `Timestamp` is an untyped `string` with no format contract

- **Severity:** High
- **Location:** `shared/types/src/base.ts`:3
- **Root Cause:** `Timestamp` was defined as `type Timestamp = string` with no documentation or
  branding. Any string value was accepted, including `"tomorrow"` or `""`.
- **Fix Applied:** Changed `Timestamp` to a branded type:
  `string & { readonly __brand: "Timestamp" }` with JSDoc documenting the expected ISO 8601 format.
  The brand prevents accidental assignment from plain strings.
- **Tests Added:** Yes — updated `exports.test.ts` to verify `Timestamp` extends `string` but is not
  equal to `string`.

### BUG-003: `User` missing `updatedAt`, `isActive`, and `displayName` fields

- **Severity:** Medium
- **Location:** `shared/types/src/auth.ts`:14-19
- **Root Cause:** The `User` interface was defined with minimal fields (`id`, `email`, `roles`,
  `createdAt`), missing fields that every consuming UI package will need: `updatedAt`, `isActive`,
  and `displayName`.
- **Fix Applied:** Added `displayName: string`, `isActive: boolean`, and `updatedAt: Timestamp`
  fields to the `User` interface.
- **Tests Added:** Yes — added type assertions for all three new fields in `exports.test.ts`.

### BUG-004: `Session` missing `createdAt` and `tenantId` fields

- **Severity:** Medium
- **Location:** `shared/types/src/auth.ts`:21-25
- **Root Cause:** The `Session` interface had no `tenantId` field (critical for multi-tenancy) and
  no `createdAt` field (needed to compute session age).
- **Fix Applied:** Added `tenantId: ID` and `createdAt: Timestamp` fields to `Session`.
- **Tests Added:** Yes — added type assertions for both new fields in `exports.test.ts`.

### BUG-005: `Notification` missing `userId` and `createdAt` fields

- **Severity:** Medium
- **Location:** `shared/types/src/notifications.ts`:5-12
- **Root Cause:** The `Notification` interface had no `userId` field (needed to associate
  notifications with recipients) and no `createdAt` field (needed for sorting by recency).
- **Fix Applied:** Added `userId: ID` and `createdAt: Timestamp` fields to `Notification`.
- **Tests Added:** Yes — added type assertions for both new fields in `exports.test.ts`.

### BUG-006: `skipLibCheck: true` suppresses declaration file errors

- **Severity:** Medium
- **Location:** `shared/types/tsconfig.json`:14
- **Root Cause:** `skipLibCheck: true` skips type checking of `.d.ts` files, including this
  package's own build output. For the canonical type source of the entire codebase, declaration file
  correctness should be verified.
- **Fix Applied:** Changed `skipLibCheck` to `false`.
- **Tests Added:** No — this is a configuration fix.

## Findings Not Fixed (with reason)

### `TenantSettings.settings` is `Record<string, unknown>`

- **Reason:** Requires an architectural decision about what settings keys to define. This is design
  work that depends on downstream package requirements and should be addressed in a dedicated story
  when tenant settings are implemented.

### `build.test.ts` uses `existsSync` checks that pass on stale dist/

- **Reason:** Low severity. In CI the build step always precedes tests. Adding mtime comparison or
  content checks would add complexity for minimal benefit. Noted for future improvement.
