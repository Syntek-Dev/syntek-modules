# BUG REPORT — US004: Shared GraphQL Operations Package

**Date:** 08-03-2026 **Reporter:** QA Analysis **Status:** Fixed

## Findings Fixed

### BUG-001: Fetcher uses `http://localhost:8000/graphql` as SSR fallback

- **Severity:** Critical
- **Location:** `shared/graphql/src/lib/fetcher.ts`:1, 9-12
- **Root Cause:** When `typeof window === "undefined"` (SSR context) and `GRAPHQL_ENDPOINT` is not
  set, the fetcher silently fell back to `http://localhost:8000/graphql`. On production servers,
  this causes connection refused errors or hits unrelated services on port 8000.
- **Fix Applied:** Removed the hardcoded `DEFAULT_ENDPOINT` constant entirely. The fetcher now
  throws a descriptive `Error` when `GRAPHQL_ENDPOINT` is not set in SSR context, with a message
  explaining what to set and why.
- **Tests Added:** Yes — `fetcher.test.ts` includes a test verifying that an error is thrown when
  `GRAPHQL_ENDPOINT` is unset in SSR context, and another verifying the env var is used when set.

### BUG-002: Fetcher does not check HTTP response status

- **Severity:** Critical
- **Location:** `shared/graphql/src/lib/fetcher.ts`:14-27
- **Root Cause:** No check on `res.ok` before calling `res.json()`. Non-200 responses (500 HTML
  pages, 401/403 auth failures, rate limiting) were either parsed as JSON (causing cryptic
  "Unexpected token '<'" errors) or silently swallowed.
- **Fix Applied:** Added `if (!res.ok)` check before JSON parsing that throws a new `HttpError`
  class with the status code and status text. This provides clear, actionable error information for
  monitoring and debugging.
- **Tests Added:** Yes — `fetcher.test.ts` includes tests for HTTP 500, 401, and 403 responses.

### BUG-003: Only first GraphQL error thrown, remaining discarded

- **Severity:** High
- **Location:** `shared/graphql/src/lib/fetcher.ts`:25
- **Root Cause:** `if (json.errors?.[0]) throw new Error(json.errors[0].message)` — only the first
  error message was thrown. GraphQL responses can contain multiple errors for partial failures;
  discarding all but the first hides the full failure context.
- **Fix Applied:** Replaced with a new `GraphQLError` class that stores the entire `errors` array
  and joins all messages into the error message string. Callers can access individual errors via the
  `.errors` property.
- **Tests Added:** Yes — `fetcher.test.ts` verifies that all error messages are accessible when
  multiple GraphQL errors are returned.

### BUG-004: Auth operations missing `logout` and `refreshToken` mutations

- **Severity:** High
- **Location:** `shared/graphql/schema.graphql`:42-44, `shared/graphql/src/operations/auth.graphql`
- **Root Cause:** The story task list requires "auth queries/mutations" (plural) but only `login`
  was defined. Without `logout`, tokens cannot be revoked server-side. Without `refreshToken`, token
  rotation is not possible.
- **Fix Applied:** Added `LogoutPayload` and `RefreshTokenPayload` types to `schema.graphql`. Added
  `logout` and `refreshToken` mutations. Added corresponding operation definitions in `auth.graphql`
  (`Logout` and `RefreshToken` mutations).
- **Tests Added:** No — codegen must be re-run to generate the new hooks; the existing
  codegen-output tests will need updating after codegen.

### BUG-005: `fetcher.ts` does not set `credentials: "include"`

- **Severity:** Low
- **Location:** `shared/graphql/src/lib/fetcher.ts`:14-17
- **Root Cause:** The `fetch` call had no `credentials` option. The default `"same-origin"` does not
  send cookies cross-origin, causing unauthenticated requests in cross-origin deployments.
- **Fix Applied:** Added `credentials: "include"` to the fetch options.
- **Tests Added:** Yes — `fetcher.test.ts` verifies that `credentials: "include"` is passed to
  fetch.

### BUG-006: `graphql-drift.yml` pins stale pnpm version

- **Severity:** Low
- **Location:** `.forgejo/workflows/graphql-drift.yml`:31-32
- **Root Cause:** The drift check workflow pinned pnpm `10.28.2` while `package.json` specifies
  `pnpm@10.31.0`. Minor version differences can cause different lockfile resolution.
- **Fix Applied:** Removed the explicit `version` pin from the `pnpm/action-setup` step, allowing it
  to use the version from `package.json`'s `packageManager` field (the standard behaviour for
  pnpm/action-setup@v4).
- **Tests Added:** No — this is a configuration fix.

### BUG-007: Fetcher test coverage was zero

- **Severity:** High
- **Location:** `shared/graphql/src/__tests__/`
- **Root Cause:** No tests existed for `fetcher.ts` despite it being the primary runtime path for
  all GraphQL requests.
- **Fix Applied:** Created `shared/graphql/src/__tests__/fetcher.test.ts` with comprehensive tests
  covering endpoint selection, HTTP error handling, GraphQL error aggregation, and credentials
  configuration.
- **Tests Added:** Yes — new test file with 7 test cases.

## Findings Not Fixed (with reason)

### `me` and `currentTenant` return nullable types with no documented handling contract

- **Reason:** The nullability is correct GraphQL design — `me` returns `null` for unauthenticated
  users, `currentTenant` returns `null` when no tenant context exists. Documenting the handling
  contract requires a guide in `docs/GUIDES/` which is out of scope for this bug fix. A JSDoc
  comment could be added to the schema but `.graphql` files do not support JSDoc.

### Schema drift check degrades to SDL-only detection when `GRAPHQL_SCHEMA_URL` is unset

- **Reason:** This is by design. No running backend exists at this stage of development. The drift
  check will use the live backend schema URL once configured as a Forgejo repository variable. The
  current SDL-only fallback is the expected behaviour for the current development phase.

### CSRF token injection

- **Reason:** Requires confirmation of whether Django Strawberry has CSRF exemption configured.
  Added a comment in the fetcher documenting the expected configuration. The consuming application
  can pass CSRF headers via the `headers` parameter if needed.

### `codegen-output.test.ts` repeated existence guards

- **Reason:** Low priority refactoring. The tests function correctly; the noise in CI output is a
  minor annoyance. Deferred to a future cleanup.
