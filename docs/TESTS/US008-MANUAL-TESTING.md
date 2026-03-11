# Manual Testing Guide — syntek-graphql-crypto

**Package**: `syntek-graphql-crypto` (`rust/syntek-graphql-crypto` +
`packages/backend/syntek-graphql-crypto`)\
**Last Updated**: `2026-03-10`\
**Tested against**: Django `6.0.4` / Rust `stable` / Strawberry GraphQL `0.307.1`

---

## Overview

`syntek-graphql-crypto` is the single encryption boundary for the entire Syntek system. It
intercepts every GraphQL execution via a Strawberry `SchemaExtension`, encrypting plaintext mutation
inputs before they reach the ORM and decrypting ciphertext resolver outputs before they reach the
frontend.

Individual resolvers have no awareness of encryption — they receive ciphertext on reads and pass
ciphertext to the ORM on writes. Fields annotated with `@encrypted` are encrypted/decrypted
individually; fields annotated with `@encrypted(batch: "group_name")` are processed in a single
batch Rust call.

A tester should verify that:

- No plaintext is ever stored in the database for annotated fields.
- No ciphertext is ever returned to the GraphQL client.
- Decryption failures are handled gracefully (null field + structured error, no abort).
- Encryption failures cause complete mutation rejection with no partial DB write.
- Unauthenticated requests receive null for all encrypted fields plus an auth error.
- Resolvers contain no encryption or decryption logic.

---

## Prerequisites

Before testing, ensure the following are in place:

- [x] Python venv is active (`source .venv/bin/activate`)
- [x] `maturin develop` has been run in `rust/syntek-pyo3/` (builds the native extension)
- [x] `maturin develop` has been run in `rust/syntek-graphql-crypto/` (builds the middleware)
- [x] `SYNTEK_FIELD_KEY_USER_EMAIL` env var is set (32-byte base64-encoded key)
- [x] `SYNTEK_FIELD_KEY_USER_FIRST_NAME` env var is set
- [x] `SYNTEK_FIELD_KEY_USER_LAST_NAME` env var is set
- [x] Sandbox Django project is configured with `syntek_graphql_crypto` in `INSTALLED_APPS`
- [x] GraphQL playground is accessible at `http://localhost:8000/graphql` (`syntek-dev open api`)
- [x] A valid authenticated user session is available (log in via the sandbox UI)

---

## Test Scenarios

---

### Scenario 1 — Individual field write stores ciphertext; read returns plaintext

**What this tests**: AC1 + AC4 — the write path encrypts individual `@encrypted` fields before the
ORM, and the read path decrypts ciphertext resolver output before serialisation.

#### Setup

```bash
syntek-dev db reset
syntek-dev db seed
```

Set the required environment variable:

```bash
export SYNTEK_FIELD_KEY_USER_EMAIL=$(python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())")
```

#### Steps

1. Log in to the sandbox as an authenticated user.
2. Execute the following mutation in the GraphQL playground:

```graphql
mutation {
  updateUser(input: { email: "alice@example.com" }) {
    email
  }
}
```

1. Inspect the database directly:

```bash
syntek-dev db shell
# In the Django shell:
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.get(email__isnull=False).email)
```

1. Execute the following query:

```graphql
query {
  user {
    email
  }
}
```

#### Expected Result

- [x] The mutation response contains `"email": "alice@example.com"` (decrypted immediately by the
      middleware).
- [x] The DB `email` column contains a base64-encoded AES-256-GCM ciphertext (not
      `"alice@example.com"`).
- [x] The query response contains `"email": "alice@example.com"` (decrypted by the middleware).
- [x] No plaintext string `"alice@example.com"` appears in any DB column.

---

### Scenario 2 — Batch group write stores ciphertext per field; read returns all plaintext

**What this tests**: AC2 + AC5 — multiple `@encrypted(batch: "profile")` fields are encrypted in a
single batch Rust call; each field is stored as its own ciphertext; the read query decrypts all
fields via a single `decrypt_fields_batch` call.

#### Setup

```bash
syntek-dev db reset
syntek-dev db seed
export SYNTEK_FIELD_KEY_USER_FIRST_NAME=$(python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())")
export SYNTEK_FIELD_KEY_USER_LAST_NAME=$(python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())")
```

#### Steps

1. Execute the following mutation as an authenticated user:

```graphql
mutation {
  updateUser(input: { firstName: "Alice", lastName: "Smith" }) {
    firstName
    lastName
  }
}
```

1. Inspect the DB:

```bash
syntek-dev db shell
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()
print(repr(u.first_name), repr(u.last_name))
```

1. Execute a read query:

```graphql
query {
  user {
    firstName
    lastName
  }
}
```

#### Expected Result

- [x] Mutation response contains `"firstName": "Alice"` and `"lastName": "Smith"`.
- [x] DB `first_name` and `last_name` columns each contain a distinct base64 ciphertext.
- [x] `first_name` ciphertext differs from `last_name` ciphertext (each field has its own nonce).
- [x] Read query returns `"firstName": "Alice"` and `"lastName": "Smith"`.
- [x] Rust profiling (via `RUST_LOG=debug`) shows a single `encrypt_fields_batch` call for the write
      and a single `decrypt_fields_batch` call for the read.

---

### Scenario 3 — Tampered DB value returns null field with error; rest of response intact

**What this tests**: AC7 — a tampered or corrupted ciphertext causes graceful degradation: the
affected field is nulled, a structured error is appended to the GraphQL `errors` array, and all
other fields in the response remain intact.

#### Setup

```bash
syntek-dev db shell
# Manually corrupt the email ciphertext:
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()
u.email = "TAMPERED_NOT_A_REAL_CIPHERTEXT"
u.save(update_fields=["email"])
exit()
```

#### Steps

1. As an authenticated user, execute:

```graphql
query {
  user {
    email
    firstName
    lastName
    displayName
  }
}
```

#### Expected Result

- [x] `"email"` is `null` in the response data.
- [x] The `errors` array contains exactly one entry referencing `email` (or the field path).
- [x] The error entry includes a `field_path` or `path` key identifying the affected field.
- [x] `"firstName"`, `"lastName"`, and `"displayName"` are present and correctly decrypted.
- [x] The response HTTP status is `200` (partial success, not a hard error).
- [x] No Python exception or stack trace appears in the application logs.

---

### Scenario 4 — Unauthenticated read returns null encrypted fields with auth error

**What this tests**: AC10 — an unauthenticated request receives null for all `@encrypted` and
`@encrypted(batch: ...)` fields, an auth error in the `errors` array, and non-encrypted fields are
still returned. The attempt is logged.

#### Setup

No special setup required. Use a GraphQL client without an authentication token (e.g. clear the
`Authorization` header in the playground or use `curl` without credentials).

#### Steps

1. Send the following query without an authenticated session:

```graphql
query {
  user {
    email
    firstName
    lastName
    displayName
  }
}
```

#### Expected Result

- [x] `"email"`, `"firstName"`, and `"lastName"` are all `null`.
- [x] `"displayName"` (non-encrypted) is present and correct.
- [x] The `errors` array contains at least one entry with a message referencing authentication.
- [x] The application logs (Django logging) contain a `WARNING` or `INFO` entry referencing the
      unauthenticated access attempt and the affected model/field.
- [x] No decryption is attempted (no calls to `syntek_pyo3.decrypt_field` or
      `syntek_pyo3.decrypt_fields_batch` appear in debug logs).

---

### Scenario 5 — Mixed individual and batch mutation processes fields via correct paths

**What this tests**: AC3 — a mutation with both individual `@encrypted` and batch
`@encrypted(batch: "profile")` fields routes each type through the correct Rust function without
mixing groups.

#### Setup

```bash
syntek-dev db reset
syntek-dev db seed
```

Enable Rust debug logging:

```bash
export RUST_LOG=syntek_graphql_crypto=debug
```

#### Steps

1. As an authenticated user, execute:

```graphql
mutation {
  updateUser(input: { email: "alice@example.com", firstName: "Alice", lastName: "Smith" }) {
    email
    firstName
    lastName
  }
}
```

#### Expected Result

- [x] Mutation response contains correct plaintext for all three fields.
- [x] Debug logs show exactly one `encrypt_field` call for `email`.
- [x] Debug logs show exactly one `encrypt_fields_batch` call for the `profile` group containing
      both `first_name` and `last_name`.
- [x] No call mixes `email` with the profile batch group.
- [x] DB contains three distinct ciphertexts.

---

### Scenario 6 — Encrypt failure rejects entire mutation with no partial DB write

**What this tests**: AC9 — if encryption fails for any field in a mutation (e.g. missing or invalid
key), the entire mutation is rejected and no partial ciphertext is written to the ORM.

#### Setup

```bash
# Remove the key for one field to simulate a missing key.
unset SYNTEK_FIELD_KEY_USER_EMAIL
```

#### Steps

1. As an authenticated user, execute:

```graphql
mutation {
  updateUser(input: { email: "alice@example.com", firstName: "Alice", lastName: "Smith" }) {
    email
    firstName
    lastName
  }
}
```

1. Inspect the DB to confirm no partial write occurred.

#### Expected Result

- [x] The mutation response contains an `errors` entry referencing the key resolution failure.
- [x] The response `data` is `null` for the entire mutation (not a partial result).
- [x] The DB `email`, `first_name`, and `last_name` columns are unchanged from before the mutation.
- [x] No resolver function is called (no ORM writes occur).
- [x] Restore the key after the test: `export SYNTEK_FIELD_KEY_USER_EMAIL=<original_key>`.

---

### Scenario 7 — Resolvers contain no encryption or decryption logic

**What this tests**: AC11 (resolver isolation) — individual resolvers must be oblivious to
encryption. They must receive ciphertext on reads and pass ciphertext to the ORM on writes. All
crypto is handled exclusively by the middleware.

#### Setup

No runtime setup required. This is a code review scenario.

#### Steps

1. Open each resolver file under `packages/backend/syntek-graphql-crypto/`.
2. Search for any direct calls to `syntek_pyo3`, `encrypt_field`, `decrypt_field`,
   `encrypt_fields_batch`, or `decrypt_fields_batch`:

```bash
grep -r "syntek_pyo3\|encrypt_field\|decrypt_field" packages/backend/syntek-graphql-crypto/ \
  --include="*.py" \
  --exclude-dir=tests
```

1. Confirm that no import of `syntek_pyo3` appears in any resolver file.

#### Expected Result

- [x] `grep` returns zero matches outside of `middleware.py` and test files.
- [x] Each resolver simply returns or accepts the field value as a string — no cryptographic
      operations.
- [x] The `EncryptionMiddleware` in `middleware.py` is the only file that imports `syntek_pyo3`.

---

## API / GraphQL Testing

The middleware adds no new top-level queries or mutations — it wraps existing schema fields. Test
using the standard GraphQL playground at `http://localhost:8000/graphql` (open with
`syntek-dev open api`).

### Queries

#### `user { email }`

```graphql
query {
  user {
    email
    firstName
    lastName
    displayName
  }
}
```

**Expected**: Encrypted fields return decrypted plaintext strings for authenticated users.
Unauthenticated users receive `null` for all encrypted fields and an auth error in `errors`.

### Mutations

#### `updateUser`

```graphql
mutation {
  updateUser(input: { email: "alice@example.com", firstName: "Alice", lastName: "Smith" }) {
    email
    firstName
    lastName
  }
}
```

**Expected**: Plaintext is encrypted before the resolver runs. The response returns the decrypted
values (middleware decrypt on write-response). The DB stores ciphertext.

---

## Regression Checklist

Run before marking a PR ready for review:

- [x] All automated tests pass: `syntek-dev test --rust` and
      `syntek-dev test --python --python-package syntek-graphql-crypto`
- [x] Individual field write → DB ciphertext → read returns plaintext (Scenario 1)
- [x] Batch group write → DB ciphertext per field → all plaintext returned (Scenario 2)
- [x] Tampered DB value → null field + structured error, rest intact (Scenario 3)
- [x] Unauthenticated request → all encrypted fields null + auth error (Scenario 4)
- [x] Mixed individual + batch mutation → correct routing confirmed in logs (Scenario 5)
- [x] Encrypt failure → mutation rejected, no partial DB write (Scenario 6)
- [x] Resolver isolation confirmed — no crypto logic in resolver files (Scenario 7)
- [x] No Python exceptions or Rust panics in application logs during any scenario
- [x] `RUST_LOG=debug` output confirms correct function routing for each field type

---

## Known Issues

No known issues at the time of red-phase writing.

| Issue | Workaround | Story / Issue |
| ----- | ---------- | ------------- |
| —     | —          | —             |

---

## Reporting a Bug

If a test scenario fails unexpectedly:

1. Note the exact steps to reproduce.
2. Capture the error message and stack trace.
3. Check `docs/BUGS/` for existing reports.
4. Create a new bug report in `docs/BUGS/syntek-graphql-crypto-{YYYY-MM-DD}.md`.
5. Reference the user story: `Blocks US008`.
