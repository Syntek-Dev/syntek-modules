# QA Report: US004 — Shared GraphQL Operations Package

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US004 — Shared GraphQL
Operations Package **Branch:** main (completed story) **Scope:** `shared/graphql/src/`,
`shared/graphql/schema.graphql`, `shared/graphql/codegen.ts`, `shared/graphql/src/lib/fetcher.ts`,
`shared/graphql/src/operations/`, `shared/graphql/src/__tests__/`,
`.forgejo/workflows/graphql-drift.yml` **Status:** CRITICAL ISSUES FOUND

---

## Summary

The `@syntek/graphql` package delivers typed React Query hooks and generates correct TypeScript from
the GraphQL SDL. All 29 tests pass. However, the `fetcher.ts` implementation — which is an explicit
US004 deliverable — contains two critical defects: a hardcoded `localhost:8000` SSR fallback
endpoint that will silently fail in production, and no HTTP response status check before JSON
parsing. The auth operation set is also incomplete against the story's stated scope: the task list
requires "auth queries/mutations" but only a login mutation is defined — no logout and no token
refresh. The schema drift check is correctly implemented but the `graphql-drift.yml` workflow pins a
stale pnpm version. `fetcher.ts` has zero test coverage despite being the primary runtime path.

---

## CRITICAL (Blocks deployment)

### 1. Fetcher uses `http://localhost:8000/graphql` as the SSR default endpoint

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts` lines 1,
9–12

```ts
const DEFAULT_ENDPOINT = "http://localhost:8000/graphql";

const endpoint =
  typeof window !== "undefined"
    ? "/graphql"
    : (process.env["GRAPHQL_ENDPOINT"] ?? DEFAULT_ENDPOINT);
```

In server-side rendering (Next.js App Router or Pages Router with `getServerSideProps`), there is no
`window` object. The fetcher falls back to `process.env["GRAPHQL_ENDPOINT"]`. But if
`GRAPHQL_ENDPOINT` is not set in the server environment — which is the case on any server that has
not been explicitly configured — the fetcher silently sends all SSR requests to
`http://localhost:8000/graphql`.

On a production server, port 8000 is not the Django backend. The request will either fail with
connection refused, causing the entire SSR render to throw, or hit an unrelated service on that port
and return unexpected data. There is no startup-time validation that `GRAPHQL_ENDPOINT` is set, and
no warning log when the localhost default is used.

**Impact:** Any consuming Next.js page that fetches data server-side will silently fail or return
incorrect data in any deployment where `GRAPHQL_ENDPOINT` is not explicitly set.

**Reproduce:** Deploy a Next.js app using `@syntek/graphql` without setting `GRAPHQL_ENDPOINT`. Any
SSR data fetch will fail with ECONNREFUSED or return unexpected data from port 8000.

---

### 2. Fetcher does not check HTTP response status — non-200 responses are silently parsed

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts` lines
14–27

```ts
const res = await fetch(endpoint, {
  method: "POST",
  headers: { "Content-Type": "application/json", ...headers },
  body: JSON.stringify({ query, variables }),
});

const json = (await res.json()) as {
  data?: TData;
  errors?: Array<{ message: string }>;
};

if (json.errors?.[0]) throw new Error(json.errors[0].message);
return json.data as TData;
```

There is no check on `res.ok` or `res.status`. If the backend returns an HTTP 500 with an HTML error
page, `res.json()` will throw a parse error with the unhelpful message `Unexpected token '<'`. If
the backend returns an HTTP 401 or 403 with a JSON body that does not follow the GraphQL error
envelope, `json.errors` will be `undefined` and `json.data` will be cast to `TData` — returning
`undefined` where a typed value is expected, with no error thrown.

**Impact:** Authentication failures, CSRF rejections, rate limiting responses, and gateway errors
are all silently swallowed or produce cryptic parse errors with no actionable information for the
caller or for error monitoring.

---

## HIGH (Must fix before production)

### 3. Only the first GraphQL error is thrown — remaining errors are discarded

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts` line 25

```ts
if (json.errors?.[0]) throw new Error(json.errors[0].message);
```

GraphQL responses can contain an `errors` array with multiple entries. This implementation throws
only `errors[0].message` and silently discards `errors[1]` through `errors[N]`. A request that
partially succeeds (partial data alongside multiple field-level errors) will throw only the first
error, hiding the full failure context from the caller and from error monitoring.

---

### 4. Auth operation set is incomplete — no `logout` mutation and no `refreshToken` mutation

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/operations/auth.graphql`
**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/schema.graphql` lines 42–44

```graphql
type Mutation {
  login(email: String!, password: String!): LoginPayload
}
```

The US004 story task list states: "Define initial `.graphql` operation files: **auth
queries/mutations**, tenant query." Only a login mutation is defined. There is no `logout` mutation
to invalidate sessions server-side and no `refreshToken` mutation for token rotation.

A session system without server-side logout means tokens cannot be revoked before their natural
expiry. If a token is compromised or a device is lost, there is no mechanism to revoke access
through the GraphQL API. This is a gap against the story's stated scope of "auth queries/mutations"
(plural).

---

### 5. `me` and `currentTenant` queries return nullable types with no documented handling contract

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/schema.graphql` lines 37–40

```graphql
type Query {
  me: User
  currentTenant: Tenant
}
```

Both return nullable types (no `!`). The generated TypeScript types `me` as
`User | null | undefined` and `currentTenant` as `Tenant | null | undefined`. The type-inference
tests use `NonNullable<CurrentUserQuery["me"]>` throughout, confirming the test authors are aware of
the nullable return. There is no documented contract about what null signifies (unauthenticated
user? user not found?) and no generated hook behaviour to redirect on null `me`. The fetcher does
not distinguish between an unauthenticated null response and a legitimate null. Every call site must
null-check and decide what null means without guidance from the schema or the operation file.

---

### 6. Test coverage for `fetcher.ts` is zero

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/__tests__/`

The `__tests__` directory contains `type-inference.test.ts` and `codegen-output.test.ts`. Neither
tests `fetcher.ts`. The fetcher is the US004-delivered runtime execution path for every GraphQL
request in the platform. Issues 1, 2, and 3 above are all in `fetcher.ts` and are all untested.
There are no tests for: correct endpoint selection in browser vs SSR context, error handling on
non-200 HTTP responses, behaviour when the `errors` array has multiple entries, or behaviour when
`json.data` is `undefined`.

---

## MEDIUM (Should fix)

### 7. Fetcher has no CSRF token injection

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts` lines
14–17

```ts
headers: { "Content-Type": "application/json", ...headers },
```

The fetcher accepts an optional `headers` parameter but has no built-in mechanism to read and inject
a CSRF token (e.g., from `document.cookie` or a meta tag). Django enforces CSRF protection on
state-changing requests by default. Any consuming package that uses the login mutation without
explicitly passing a CSRF header will receive a 403 response from Django — which, per Issue 2, is
silently swallowed or produces a cryptic error. Whether Strawberry GraphQL has CSRF exemption
configured is not documented in the fetcher, the schema, or the operations. This must be clarified
and the fetcher updated accordingly.

---

### 8. Schema drift check degrades to SDL-only detection when `GRAPHQL_SCHEMA_URL` is unset

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/codegen.ts` line 17 **File:**
`/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/graphql-drift.yml` lines 44–48

```ts
const schema = process.env["GRAPHQL_SCHEMA_URL"] || "./schema.graphql";
```

The US004 story AC states: "Given the backend GraphQL schema changes, When I run `pnpm codegen`,
Then the generated types update and TypeScript surfaces any breaking changes." This is only true if
`schema.graphql` has also been updated. The drift check CI job uses `GRAPHQL_SCHEMA_URL` from a
repository variable that "falls back to `schema.graphql` SDL when unset." If `GRAPHQL_SCHEMA_URL` is
never set (the current state — no running backend exists), drift detection only catches divergence
between the committed SDL and the generated files, not divergence between the live backend schema
and the SDL. A backend developer who changes the Django/Strawberry schema without updating
`schema.graphql` will pass the drift check.

---

### 9. `codegen-output.test.ts` existence guards are repeated 11 times — does not fail atomically

**File:**
`/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/__tests__/codegen-output.test.ts`
lines 36–50

Every test in `codegen-output.test.ts` independently checks whether the generated file exists before
reading it, then calls `expect.fail(...)` with the same message if it does not. This pattern is
repeated 11 times. If the generated file is absent, 11 tests fail with identical error messages
rather than 1 test failing (the existence check) and the remaining 10 being skipped. This produces
redundant and noisy failure output in CI. A `beforeAll` guard would resolve this.

---

## LOW (Consider fixing)

### 10. `graphql-drift.yml` pins pnpm `10.28.2` while `package.json` pins `pnpm@10.31.0`

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/graphql-drift.yml` line 32

```yaml
- uses: pnpm/action-setup@v4
  with:
    version: "10.28.2"
```

`package.json` pins `"pnpm@10.31.0"`. The `graphql-drift.yml` workflow — a US004 deliverable — pins
`10.28.2`. This means pnpm in the drift check job runs against a different version than all other CI
jobs and local development. Minor pnpm version differences can produce different lockfile resolution
output, which could cause the drift check to fail spuriously or pass incorrectly.

---

### 11. `fetcher.ts` does not set `credentials: "include"` — session cookies not sent cross-origin

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts`

The `fetch` call has no `credentials` option. The default is `"same-origin"`, which sends cookies
only to the same origin. If the Next.js frontend is on a different origin from the Django backend —
a standard production topology — HttpOnly session cookies will not be sent without
`credentials: "include"`. This will manifest as unauthenticated requests in any cross-origin
deployment.

---

## Test Scenarios Needed

- Fetcher in SSR context (no `window`) with `GRAPHQL_ENDPOINT` unset — should throw a descriptive
  error or warn, not silently use `localhost:8000`
- Fetcher receives HTTP 500 HTML response — should throw a meaningful HTTP error, not a JSON parse
  error
- Fetcher receives HTTP 401 — should throw an authentication error with status code
- Fetcher receives HTTP 403 — should throw a CSRF or authorisation error
- Fetcher `errors` array has two entries — both messages should be accessible to the caller
- Fetcher `res.ok` is false — should throw before attempting `res.json()`
- `logout` mutation defined in `auth.graphql` and a typed `useLogoutMutation` hook is generated
- `refreshToken` mutation defined in `auth.graphql` and a typed `useRefreshTokenMutation` hook is
  generated

---

## Implementation Files Reviewed

| File                                                                                              | Purpose                                |
| ------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/lib/fetcher.ts`                   | Runtime GraphQL fetcher                |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/schema.graphql`                       | GraphQL SDL                            |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/codegen.ts`                           | Codegen configuration                  |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/index.ts`                         | Package entry point                    |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/operations/auth.graphql`          | Auth operations                        |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/operations/tenant.graphql`        | Tenant operations                      |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/package.json`                         | Package manifest                       |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/__tests__/type-inference.test.ts` | Type tests                             |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/graphql/src/__tests__/codegen-output.test.ts` | Codegen output tests                   |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/graphql-drift.yml`                | Drift detection CI (US004 deliverable) |
| `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US004-TEST-STATUS.md`                     | Test status                            |

---

## Overall Risk Rating

**Critical**

The fetcher implementation has two Critical issues that will cause production failures in any SSR
deployment: the hardcoded `localhost:8000` fallback and the absence of HTTP status checking. These
are not theoretical — they are defects in the US004-delivered `fetcher.ts` that will fire on any
server where `GRAPHQL_ENDPOINT` is not configured or where the backend returns a non-200 response.
The auth operation set is also incomplete against the story's stated scope, and `fetcher.ts` has
zero test coverage.

---

## Handoff Signals

- Run `/syntek-dev-suite:debug` to confirm whether Strawberry GraphQL is configured with CSRF
  exemption or requires CSRF token injection in the fetcher, and document the outcome in
  `fetcher.ts`.
- Run `/syntek-dev-suite:backend` to add an HTTP status check to the fetcher, add startup-time
  validation of `GRAPHQL_ENDPOINT`, add `logout` and `refreshToken` mutations to the schema and
  operations files, and fix the pnpm version pin in `graphql-drift.yml`.
- Run `/syntek-dev-suite:test-writer` to add unit tests for `fetcher.ts` covering SSR endpoint
  selection, non-200 HTTP responses, and multiple GraphQL errors.
- Run `/syntek-dev-suite:completion` to update QA status for US004 once the Critical issues are
  resolved.
