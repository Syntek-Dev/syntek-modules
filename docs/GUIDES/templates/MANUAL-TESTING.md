# Manual Testing Guide — {PACKAGE_NAME}

> **Template**: Copy to `packages/backend/syntek-{name}/docs/MANUAL-TESTING.md` (backend),
> `packages/web/{name}/docs/MANUAL-TESTING.md` (web), or
> `mobile/{name}/docs/MANUAL-TESTING.md` (mobile).
> Replace all `{PLACEHOLDER}` values.

---

**Package**: `{PACKAGE_NAME}`\
**Last Updated**: `{YYYY-MM-DD}`\
**Tested against**: Django `{version}` / Node.js `{version}` / Rust `{version}`

---

## Overview

_A one-paragraph description of what this package does and what a tester should
be looking to verify._

---

## Prerequisites

Before testing, ensure the following are in place:

- [ ] Sandbox environment is running (`syntek-dev up`)
- [ ] Database is seeded (`syntek-dev db seed`)
- [ ] Python venv is active (`source .venv/bin/activate`)
- [ ] Any required environment variables are set (see `.env.dev.example`)
- [ ] _{Any package-specific prerequisites}_

---

## Test Scenarios

Each scenario has a **Setup**, **Steps**, and **Expected Result** section.

---

### Scenario 1 — {Happy path scenario name}

**What this tests**: _{Brief description}_

#### Setup

```bash
syntek-dev db reset
syntek-dev db seed
```

#### Steps

1. _{Action}_
2. _{Action}_
3. _{Action}_

#### Expected Result

- [ ] _{Observable outcome 1}_
- [ ] _{Observable outcome 2}_

---

### Scenario 2 — {Validation / error path}

**What this tests**: _{Brief description}_

#### Setup

_{Any specific setup required}_

#### Steps

1. _{Action}_
2. _{Action}_

#### Expected Result

- [ ] _{Observable outcome — e.g. error message, HTTP 422, etc.}_

---

### Scenario 3 — {Security / edge case}

**What this tests**: _{e.g. Unauthenticated access is rejected}_

#### Steps

1. _{Action without valid credentials or with invalid input}_

#### Expected Result

- [ ] _{Rejection behaviour, e.g. HTTP 401, redirect to login, error message}_

---

## API / GraphQL Testing

If this package exposes a GraphQL API, test the following mutations and queries
using the GraphQL playground at `http://localhost:8000/graphql` (open with
`syntek-dev open api`).

### Mutations

#### `{MutationName}`

```graphql
mutation {
  {mutationName}(input: {
    {field}: "{value}"
  }) {
    {returnField}
  }
}
```

**Expected**: _{description of correct response}_

---

### Queries

#### `{QueryName}`

```graphql
query {
  {queryName} {
    {field}
  }
}
```

**Expected**: _{description of correct response}_

---

## UI Testing

> Only applicable to `packages/web/*` and `mobile/*` packages.

### Component — {ComponentName}

Open Storybook at `http://localhost:6006` (or `syntek-dev open storybook`).

1. Navigate to the `{ComponentName}` story
2. Verify each story state renders correctly:
   - [ ] Default
   - [ ] Loading
   - [ ] Error
   - [ ] _{Any custom states}_

### Interactive flow

1. _{Step through the user journey in the browser}_
2. _{Verify the expected outcome}_

---

## Regression Checklist

Run before marking a PR ready for review:

- [ ] All automated tests pass: `syntek-dev test --python-package {name}`
- [ ] Happy path works end-to-end
- [ ] Validation errors display correctly
- [ ] Unauthenticated requests are rejected (HTTP 401)
- [ ] Unauthorised requests are rejected (HTTP 403)
- [ ] Edge cases documented above have been verified
- [ ] No console errors in the browser
- [ ] No unhandled Python exceptions in logs

---

## Known Issues

_List any known issues or limitations that testers should be aware of._

| Issue | Workaround | Story / Issue |
| ----- | ---------- | ------------- |
| _{description}_ | _{workaround}_ | US-000 |

---

## Reporting a Bug

If a test scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/{PACKAGE_NAME}-{YYYY-MM-DD}.md`
5. Reference the user story: `Blocks US-{NNN}`
