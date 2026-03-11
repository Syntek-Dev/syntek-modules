# syntek-graphql-crypto

GraphQL encryption middleware for Strawberry — the **single encryption boundary** for the entire
Syntek system.

Plaintext from the frontend is encrypted before reaching the ORM on writes. Ciphertext from the
database is decrypted before reaching the frontend on reads. Individual resolvers have **zero**
encryption logic.

```text
Write path:  Frontend (plaintext) → [middleware encrypts] → Resolver → ORM → DB (ciphertext)
Read path:   DB (ciphertext) → ORM → Resolver → [middleware decrypts] → Frontend (plaintext)
```

---

## Installation

```bash
syntek add syntek-graphql-crypto
```

---

## Wiring the middleware

Add `EncryptionMiddleware` to your Strawberry schema's `extensions` list:

```python
import strawberry
from syntek_graphql_crypto.middleware import EncryptionMiddleware

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[EncryptionMiddleware],
)
```

No other configuration is required at the schema level. All field-level configuration is done via
directives and environment variables.

---

## Annotating fields

### Individual field — `@encrypted`

Use for fields that are queried or mutated in isolation:

```python
from syntek_graphql_crypto.directives import Encrypted

@strawberry.type
class UserType:
    email: str | None = strawberry.field(directives=[Encrypted()])
    display_name: str  # not encrypted — passes through unchanged
```

On writes, the middleware calls `syntek_pyo3.encrypt_field` once per individual field. On reads, the
middleware calls `syntek_pyo3.decrypt_field` once per individual field.

### Batch group — `@encrypted(batch: "group_name")`

Use for fields that are always read or written together (e.g. name parts, address lines). All fields
sharing the same `group_name` on the same type are encrypted or decrypted in a **single** Rust call:

```python
@strawberry.type
class UserType:
    first_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])
    last_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])
    address_line_1: str | None = strawberry.field(directives=[Encrypted(batch="address")])
    postcode: str | None = strawberry.field(directives=[Encrypted(batch="address")])
```

On writes, each batch group produces one `syntek_pyo3.encrypt_fields_batch` call. On reads, each
batch group produces one `syntek_pyo3.decrypt_fields_batch` call.

### Mutation input arguments

Annotate mutation arguments with `strawberry.annotated`:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_email(
        self,
        email: strawberry.annotated[str, Encrypted()],
    ) -> str:
        # email is already ciphertext here — save directly to ORM
        ...

    @strawberry.mutation
    def update_profile(
        self,
        first_name: strawberry.annotated[str, Encrypted(batch="profile")],
        last_name: strawberry.annotated[str, Encrypted(batch="profile")],
    ) -> str:
        # both args are ciphertext — encrypted in a single batch call
        ...
```

> **Passwords** are **never** handled by this middleware. Use `syntek_pyo3.hash_password` /
> `verify_password` directly in the resolver — they are one-way hashes, not reversible encryption.

---

## Key naming convention

For every encrypted field you must set one environment variable:

```bash
SYNTEK_FIELD_KEY_<MODEL>_<FIELD>=<base64-encoded 32-byte key>
```

| Model  | Field        | Environment variable               |
| ------ | ------------ | ---------------------------------- |
| `User` | `email`      | `SYNTEK_FIELD_KEY_USER_EMAIL`      |
| `User` | `first_name` | `SYNTEK_FIELD_KEY_USER_FIRST_NAME` |
| `User` | `phone`      | `SYNTEK_FIELD_KEY_USER_PHONE`      |

Rules:

- Model and field names are uppercased.
- The key must be exactly 32 bytes, base64-encoded (44 characters including padding).
- Generate a key: `python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"`
- The middleware resolves the correct key per field at request time. Missing keys raise a
  `RuntimeError` at execution time, not at startup.

---

## Error handling

### Decrypt failure (query)

If decryption fails for an individual `@encrypted` field, that field is set to `null`, a structured
error is appended to the GraphQL `errors` array, and the rest of the response is returned normally.

If decryption fails for any field within an `@encrypted(batch: ...)` group, **all** fields in that
group are set to `null` and a single error entry is appended. Partial group results are never
returned.

### Encrypt failure (mutation)

If encryption fails for any field in a mutation, the **entire mutation is rejected** with a
structured error. No partial ciphertext is written to the ORM.

---

## Auth guard

The middleware checks `info.context.user.is_authenticated` before performing any decryption. For
unauthenticated requests:

- All `@encrypted` fields in the response are set to `null`.
- An authorisation error is appended to the `errors` array.
- Non-encrypted fields are returned normally — the request is not aborted.
- The attempt is logged via `syntek_graphql_crypto` logger at `WARNING` level.

---

## Django settings

No `SYNTEK_*` settings dict is required for this module. Configuration is entirely via
`SYNTEK_FIELD_KEY_*` environment variables.
