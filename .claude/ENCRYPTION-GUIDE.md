# Encryption Guide

**Applies to:** All Django backend modules in `packages/backend/` **Reference implementation:**
`packages/backend/syntek-auth/`

---

## Table of Contents

- [Zero-Plaintext Guarantee](#zero-plaintext-guarantee)
- [EncryptedField](#encryptedfield)
- [Encryption and Decryption Paths](#encryption-and-decryption-paths)
- [Individual Field Encryption](#individual-field-encryption)
- [Batch Field Encryption](#batch-field-encryption)
- [Unique Fields — Lookup Tokens](#unique-fields--lookup-tokens)
- [Settings Required](#settings-required)
- [Migrations](#migrations)
- [What Does NOT Need Encryption](#what-does-not-need-encryption)
- [Quick Checklist](#quick-checklist)

---

## Zero-Plaintext Guarantee

**No plaintext PII ever reaches the database.** Sensitive fields are encrypted by the Rust layer
(`syntek-pyo3`) before any DB write. The GraphQL middleware decrypts on the way out. The model field
itself is a storage type only.

The three actors and their responsibilities:

| Actor                                            | Responsibility                                                                                                  |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Django model field** (`EncryptedField`)        | Storage type — `TEXT` column, ciphertext validation via `syntek_pyo3`                                           |
| **Service layer**                                | Calls `encrypt_field` / `encrypt_fields_batch` before save; `decrypt_field` / `decrypt_fields_batch` after load |
| **GraphQL middleware** (`syntek-graphql-crypto`) | Intercepts resolvers marked `@encrypted` and decrypts before returning to the client                            |

---

## EncryptedField

Every PII column on a Django model must use `EncryptedField` instead of `CharField`, `TextField`, or
`EmailField`.

```python
from syntek_auth.models.user import EncryptedField  # or import from your module's models

class MyModel(models.Model):
    full_name = EncryptedField(blank=False, null=False)
    phone     = EncryptedField(blank=True, null=True)
```

`EncryptedField` extends `models.TextField` so the DB column is `TEXT`. When `syntek_pyo3` is
installed it delegates ciphertext validation to the Rust implementation. Without it (early
development, CI without the compiled extension) it falls back to a no-op, so tests and migrations
continue to work.

**Rules:**

- Never use `unique=True` on an `EncryptedField` — see
  [Unique Fields](#unique-fields--lookup-tokens).
- Never use `db_index=True` on an `EncryptedField` — the ciphertext is random and unindexable.
- Never set `max_length` — the ciphertext is always longer than the plaintext.
- `null=True` is allowed for optional fields.

---

## Encryption and Decryption Paths

### Write path

```
GraphQL mutation / service call
    │
    ├── encrypt_field(plaintext, key, model, field)        ← individual
    │   OR
    └── encrypt_fields_batch([(field, value), ...], key, model)  ← batch
            │
            ▼
    model.field = ciphertext
    model.field_token = make_field_token(plaintext)   ← if unique
    model.save()
            │
            ▼
         PostgreSQL (TEXT column — ciphertext only, never plaintext)
```

### Read path

```
PostgreSQL (ciphertext)
    │
    ▼
model.field  →  raw ciphertext (EncryptedField.from_db_value passthrough)
    │
    ├── Service layer: decrypt_field(ciphertext, key, model, field)
    │   OR
    └── GraphQL middleware: intercepts @encrypted resolvers, calls decrypt_field
            │
            ▼
         plaintext returned to caller / client
```

---

## Individual Field Encryption

Use `encrypt_field` / `decrypt_field` when a model has **one or two** sensitive fields, or when
fields have different keys.

```python
from syntek_pyo3 import encrypt_field, decrypt_field

FIELD_KEY = settings.SYNTEK_FIELD_KEY_MY_MODEL  # 32-byte key from env var

# Encrypt before save
model.full_name = encrypt_field(plaintext_name, FIELD_KEY, "MyModel", "full_name")
model.save()

# Decrypt after load
plaintext_name = decrypt_field(model.full_name, FIELD_KEY, "MyModel", "full_name")
```

The `model` and `field` arguments are used as AAD (Additional Authenticated Data) so a ciphertext
from one field cannot be replayed into another.

---

## Batch Field Encryption

Use `encrypt_fields_batch` / `decrypt_fields_batch` when a model has **three or more** sensitive
fields that share the same key. Batch operations are more efficient and reduce the number of
Rust→Python boundary crossings.

```python
from syntek_pyo3 import encrypt_fields_batch, decrypt_fields_batch

FIELD_KEY = settings.SYNTEK_FIELD_KEY_MY_MODEL

# Encrypt before save
encrypted = encrypt_fields_batch(
    [
        ("full_name", plaintext_name),
        ("address_line_1", plaintext_addr1),
        ("address_line_2", plaintext_addr2),
        ("postcode", plaintext_postcode),
    ],
    FIELD_KEY,
    "MyModel",
)
# encrypted is a list[str] in the same order as the input
model.full_name, model.address_line_1, model.address_line_2, model.postcode = encrypted
model.save()

# Decrypt after load
decrypted = decrypt_fields_batch(
    [
        ("full_name", model.full_name),
        ("address_line_1", model.address_line_1),
        ("address_line_2", model.address_line_2),
        ("postcode", model.postcode),
    ],
    FIELD_KEY,
    "MyModel",
)
plaintext_name, plaintext_addr1, plaintext_addr2, plaintext_postcode = decrypted
```

**Rule of thumb:**

| Number of encrypted fields | Use                                             |
| -------------------------- | ----------------------------------------------- |
| 1–2                        | `encrypt_field` / `decrypt_field`               |
| 3 or more                  | `encrypt_fields_batch` / `decrypt_fields_batch` |

---

## Unique Fields — Lookup Tokens

AES-256-GCM uses a random nonce per encryption. The same plaintext encrypted twice produces
**different ciphertext**. A DB `UNIQUE` constraint on ciphertext is therefore meaningless — the same
email stored twice would pass the constraint because its ciphertexts differ.

**Rule: every `EncryptedField` that must be unique gets a companion `*_token` column.** The token is
a deterministic HMAC-SHA256 of the normalised plaintext. The `UNIQUE` constraint goes on the token
column, never on the ciphertext column.

### Token column naming

| Encrypted field             | Token column                      |
| --------------------------- | --------------------------------- |
| `email`                     | `email_token`                     |
| `phone`                     | `phone_token`                     |
| `username`                  | `username_token`                  |
| `national_insurance_number` | `national_insurance_number_token` |
| `bank_account_number`       | `bank_account_number_token`       |

For **batch** groups, use a shared token column only when the combined values form a single unique
key. Otherwise add one token column per unique field:

```python
# Individual unique fields within a batch
class PatientRecord(models.Model):
    nhs_number     = EncryptedField()          # unique
    nhs_number_token = models.CharField(max_length=64, unique=True, db_index=True)

    full_name      = EncryptedField()          # not unique — no token needed
    date_of_birth  = EncryptedField()          # not unique — no token needed
    postcode       = EncryptedField()          # not unique — no token needed
```

### Model definition

```python
class MyModel(models.Model):
    # Encrypted — no unique, no db_index
    email = EncryptedField(blank=False, null=False)

    # Token — carries the UNIQUE constraint
    email_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="email lookup token",
        help_text="HMAC-SHA256 of the normalised email address.",
    )

    # Nullable encrypted field with nullable token
    phone = EncryptedField(blank=True, null=True)
    phone_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="phone lookup token",
    )
```

### Token generation

Tokens are generated from the module's `services/lookup_tokens.py` (each module that needs them must
define its own, following the `syntek-auth` pattern). The key comes from the module's
`SYNTEK_<MODULE>['FIELD_HMAC_KEY']` setting.

```python
# services/lookup_tokens.py
import hashlib
import hmac as _hmac

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _hmac_key() -> bytes:
    cfg = getattr(settings, "SYNTEK_<MODULE>", {})
    key = cfg.get("FIELD_HMAC_KEY")
    if not key:
        raise ImproperlyConfigured("SYNTEK_<MODULE>['FIELD_HMAC_KEY'] must be set.")
    return key.encode("utf-8") if isinstance(key, str) else bytes(key)


def make_email_token(email: str) -> str:
    """Lowercase + strip before hashing for case-insensitive lookups."""
    return _hmac.new(_hmac_key(), email.strip().lower().encode(), hashlib.sha256).hexdigest()


def make_phone_token(phone: str) -> str:
    return _hmac.new(_hmac_key(), phone.strip().encode(), hashlib.sha256).hexdigest()
```

### DB lookups — always use the token column

Never query against an encrypted column directly. Always use the token:

```python
# WRONG — ciphertext lookup, will never match
User.objects.filter(email__iexact=identifier)
User.objects.filter(email=identifier)

# CORRECT — token lookup
from syntek_auth.services.lookup_tokens import make_email_token
User.objects.filter(email_token=make_email_token(identifier))
```

### Write path with token

The model manager (or service layer) must compute the token and set both fields before `save()`:

```python
def create_record(email: str, ...) -> MyModel:
    from mymodule.services.lookup_tokens import make_email_token

    obj = MyModel(
        email=encrypt_field(email, FIELD_KEY, "MyModel", "email"),
        email_token=make_email_token(email),
        ...
    )
    obj.save()
    return obj
```

### Token normalisation rules

| Field type               | Normalisation before hashing                                       |
| ------------------------ | ------------------------------------------------------------------ |
| Email                    | `strip().lower()`                                                  |
| Phone                    | `strip()` only (no reformatting)                                   |
| Username                 | `strip().lower()` unless `CASE_SENSITIVE = True`                   |
| National Insurance / SSN | `strip().upper().replace(" ", "")`                                 |
| Other identifiers        | `strip()` — add lowercasing if case-insensitive lookups are needed |

---

## Settings Required

Every module that uses encrypted fields must define two keys in its `SYNTEK_<MODULE>` settings dict,
both read from environment variables:

```python
SYNTEK_PAYMENTS = {
    # 32-byte key for field encryption (AES-256-GCM)
    "FIELD_KEY": env("SYNTEK_PAYMENTS_FIELD_KEY"),

    # 32-byte key for HMAC lookup tokens (only needed when unique fields exist)
    "FIELD_HMAC_KEY": env("SYNTEK_PAYMENTS_FIELD_HMAC_KEY"),
}
```

`FIELD_KEY` and `FIELD_HMAC_KEY` **must be different keys**. Using the same key for both encryption
and HMAC is a cryptographic mistake.

Minimum lengths validated at startup (`AppConfig.ready()`):

| Setting          | Minimum  | Why                            |
| ---------------- | -------- | ------------------------------ |
| `FIELD_KEY`      | 32 bytes | AES-256 requires a 256-bit key |
| `FIELD_HMAC_KEY` | 32 bytes | HMAC-SHA256 security margin    |

---

## Migrations

When adding encrypted fields to a new or existing model:

1. **Add** `EncryptedField` columns — no `unique=True`, no `db_index=True`.
2. **Add** `*_token` columns as `null=True` initially (no `unique` yet).
3. **RunPython** to backfill tokens for existing rows using `FIELD_HMAC_KEY`.
4. **AlterField** token columns to `null=False, unique=True` (or keep `null=True` for optional
   fields — PostgreSQL allows multiple `NULL` values under a `UNIQUE` constraint).
5. **AlterField** the encrypted columns to remove any `unique` / `db_index` that may have been set
   before the token pattern was applied.

See `syntek_auth/migrations/0003_user_encrypted_unique_tokens.py` for the canonical example.

---

## What Does NOT Need Encryption

Not every field is PII. Do not encrypt fields that are:

- **Not sensitive** — `is_active`, `is_staff`, `created_at`, `updated_at`
- **Already hashed** — password hashes, backup code hashes (`code_hash`) — hashing is not
  encryption; these are already non-reversible
- **Random tokens** — JWT JTIs, verification tokens, TOTP secrets stored as base32 — these are
  random, not derived from user input
- **Foreign keys** — encrypt the referenced row's PII, not the FK integer
- **Enum / choice fields** — `code_type`, `status` — low cardinality, not PII

When in doubt: if the value could identify a real person or be used to contact them (name, email,
phone, address, government ID), encrypt it.

---

## Quick Checklist

When adding a new encrypted field to any Django model:

- [ ] Field uses `EncryptedField` (not `CharField`, `TextField`, etc.)
- [ ] No `unique=True` on the `EncryptedField` column
- [ ] No `db_index=True` on the `EncryptedField` column
- [ ] If unique: companion `*_token` column added (`CharField(max_length=64, unique=True)`)
- [ ] If unique: token computed in the manager / service layer before `save()`
- [ ] If unique: DB lookups use `filter(field_token=make_field_token(value))`, not
      `filter(field=value)`
- [ ] `FIELD_KEY` and `FIELD_HMAC_KEY` settings defined, read from env vars, validated in
      `AppConfig.ready()`
- [ ] `FIELD_KEY` ≠ `FIELD_HMAC_KEY` — different keys for encryption and HMAC
- [ ] 3+ encrypted fields → use `encrypt_fields_batch` / `decrypt_fields_batch`
- [ ] Migration follows the 5-step pattern (add nullable → backfill → tighten)
- [ ] Tests set `FIELD_HMAC_KEY` in the conftest `SYNTEK_<MODULE>` dict
