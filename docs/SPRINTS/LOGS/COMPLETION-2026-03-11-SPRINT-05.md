# Sprint 05 Completion Log — Rust: GraphQL Middleware + Security Policy

**Sprint**: Sprint 05
**Completed**: 11/03/2026
**Repository**: Backend (Python) + Rust
**Logged By**: Completion Agent

---

## Sprint Summary

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 2     | 2         | 0         |
| Should Have      | 0     | 0         | 0         |
| Could Have       | 0     | 0         | 0         |
| **Total Points** | 23    | 23        | 0         |

| Story | Title                                                                  | Points | Branch                        | Completed  |
| ----- | ---------------------------------------------------------------------- | ------ | ----------------------------- | ---------- |
| US008 | `syntek-graphql-crypto` — GraphQL Encryption Middleware                | 13     | `us008/syntek-graphql-crypto` | 10/03/2026 |
| US076 | Security Policy: MFA-Enforcing SSO, Key Rotation, Network Architecture | 10     | `us076/security-policy`       | 11/03/2026 |

---

## US008 — `syntek-graphql-crypto`: GraphQL Encryption Middleware

**Completed**: 10/03/2026 | **Points**: 13

### What was built

- `rust/syntek-graphql-crypto/src/lib.rs` — `EncryptedFieldSpec` struct and `MiddlewareError` enum
- `rust/syntek-graphql-crypto/Cargo.toml` — correct dependencies and `crate-type = ["cdylib", "lib"]`
- `rust/syntek-graphql-crypto/tests/middleware_tests.rs` — 13 Rust unit tests
- `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py` — full Strawberry
  `SchemaExtension` — write-path (encrypt before resolver) and read-path (decrypt after resolver)
- `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py` — `@encrypted` and
  `@encrypted(batch: "group_name")` schema directives
- `packages/backend/syntek-graphql-crypto/README.md` — setup guide, annotation guide, key naming
  convention (`SYNTEK_FIELD_KEY_<MODEL>_<FIELD>`)
- `packages/backend/syntek-graphql-crypto/syntek.manifest.toml` — crate ID + Forgejo registry
  coordinates; no user-configurable options (Rust layer is pre-configured and not editable)
- `packages/backend/syntek-graphql-crypto/tests/test_write_path.py` — 10 unit tests (AC1–AC3)
- `packages/backend/syntek-graphql-crypto/tests/test_read_path.py` — 9 unit tests (AC4–AC6)
- `packages/backend/syntek-graphql-crypto/tests/test_error_handling.py` — 11 unit tests (AC7–AC9)
- `packages/backend/syntek-graphql-crypto/tests/test_auth_guard.py` — 6 unit tests (AC10–AC11)
- `packages/backend/syntek-graphql-crypto/tests/test_directives.py` — 6 unit tests
- `tests/graphql_crypto/test_integration.py` — 4 integration tests (full write→DB→read pipeline)

### Acceptance criteria

| AC   | Description                                                | Status    |
| ---- | ---------------------------------------------------------- | --------- |
| AC1  | Individual `@encrypted` write → ciphertext to resolver     | Satisfied |
| AC2  | Batch `@encrypted` write → single `encrypt_fields_batch`   | Satisfied |
| AC3  | Mixed individual + batch → correct routing, no mixing      | Satisfied |
| AC4  | Individual `@encrypted` read → plaintext to frontend       | Satisfied |
| AC5  | Batch `@encrypted` read → single `decrypt_fields_batch`    | Satisfied |
| AC6  | Non-annotated fields → passthrough, zero overhead          | Satisfied |
| AC7  | Decrypt failure (individual) → null + structured error     | Satisfied |
| AC8  | Decrypt failure (batch) → all null, one error              | Satisfied |
| AC9  | Encrypt failure → mutation rejected, no partial ORM write  | Satisfied |
| AC10 | Unauthenticated → null + auth error + logged               | Satisfied |
| AC11 | Resolver isolation — no crypto logic in resolvers          | Satisfied |

### Test summary

| Suite             | Tests  | Passed | Failed | Skipped |
| ----------------- | ------ | ------ | ------ | ------- |
| Rust unit         | 13     | 13     | 0      | 0       |
| Python unit       | 42     | 42     | 0      | 0       |
| Integration       | 4      | 4      | 0      | 0       |
| **Total (green)** | **59** | **59** | **0**  | **0**   |

> The red-phase test plan recorded 56 tests (10 Rust). The green-phase final count is 59 — 3
> additional Rust unit tests were added during implementation to achieve full `MiddlewareError`
> variant coverage.

### Linter status

| Linter       | Result |
| ------------ | ------ |
| ruff         | Clean  |
| basedpyright | Clean  |
| prettier     | Clean  |
| markdownlint | Clean  |
| clippy       | Clean  |

### Key technical notes

- The middleware is implemented as a Strawberry `SchemaExtension` — intercepts both `on_executing_start`
  (write path) and `on_executing_end` (read path) hooks.
- `syntek_pyo3` is mocked via `unittest.mock.patch` in all Python unit tests; the native extension
  does not need to be built to run unit tests.
- Integration tests require `maturin develop` in both `rust/syntek-pyo3/` and
  `rust/syntek-graphql-crypto/`.
- Key naming convention: `SYNTEK_FIELD_KEY_<MODEL>_<FIELD>` (e.g. `SYNTEK_FIELD_KEY_USER_EMAIL`) —
  resolved from environment variables at runtime.
- Password fields are explicitly excluded from this middleware — they use Argon2id one-way hashing
  in the resolver, never reversible AES-256-GCM encryption.
- `syntek.manifest.toml` records only crate ID and registry coordinates — no user-configurable
  options, consistent with the Rust layer security policy.

---

## US076 — Security Policy: MFA-Enforcing SSO, Key Rotation, and Network Architecture

**Completed**: 11/03/2026 | **Points**: 10

### What was built

- `rust/syntek-crypto/src/key_versioning.rs` — `KeyVersion` type (big-endian u16 serialisation),
  `KeyRing` struct (version → 32-byte key mapping, active key resolution), `encrypt_versioned` and
  `decrypt_versioned` functions (2-byte version prefix in ciphertext blob), `reencrypt_to_active`
  for lazy key migration
- `rust/syntek-crypto/tests/key_versioning_tests.rs` — 27 unit tests covering byte serialisation,
  KeyRing construction, round-trip encryption, cross-version decryption, error cases, and nonce
  uniqueness
- `packages/backend/syntek-auth/syntek_auth/sso_allowlist.py` — `validate_oauth_providers` function
  enforcing the MFA-enforcing provider allowlist at `AppConfig.ready()`. Blocked providers: Google,
  Facebook, Instagram, LinkedIn, Twitter/X, Apple (consumer), Discord, Microsoft (consumer MSA).
  Allowed built-ins: GitHub, GitLab, Okta, Entra ID/Azure AD, Authentik, Keycloak, Defguard.
  Custom OIDC providers require `mfa_enforced: True` operator certification.
- `packages/backend/syntek-auth/tests/test_sso_allowlist.py` — 35 unit tests covering all blocked
  providers, all built-in allowed providers, custom OIDC certification, and `AppConfig.ready()`
  integration
- `packages/backend/syntek-security/` — new package created with `apply_proxy_settings` function
  injecting `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, and `SECURE_SSL_REDIRECT` into Django
  settings at startup without overriding any project-level settings
- `packages/backend/syntek-security/tests/test_proxy_settings.py` — 15 unit tests covering settings
  injection, override protection, idempotency, and `AppConfig.ready()` integration

### Acceptance criteria

| AC                        | Description                                                                      | Status    |
| ------------------------- | -------------------------------------------------------------------------------- | --------- |
| SSO — blocked providers   | All 9 blocked providers raise `ImproperlyConfigured` at `AppConfig.ready()`     | Satisfied |
| SSO — allowed providers   | All 8 built-in allowed providers pass startup validation                         | Satisfied |
| SSO — custom OIDC         | Self-hosted providers require `mfa_enforced: True` operator certification        | Satisfied |
| Key versioning — layout   | 2-byte version prefix on all ciphertexts (version + nonce + ciphertext + tag)   | Satisfied |
| Key versioning — rotation | Old ciphertexts decrypt with expanded KeyRing (cross-version backwards compat)  | Satisfied |
| Key versioning — migrate  | `reencrypt_to_active` re-encrypts old ciphertexts under the current active key  | Satisfied |
| Proxy trust settings      | All three Django proxy settings applied at startup via `AppConfig.ready()`       | Satisfied |
| Proxy trust — no override | Existing project-configured settings are preserved; Syntek defaults not applied | Satisfied |

### Test summary

| Suite             | Tests  | Passed | Failed | Skipped |
| ----------------- | ------ | ------ | ------ | ------- |
| Rust unit         | 27     | 27     | 0      | 0       |
| Python unit       | 50     | 50     | 0      | 0       |
| **Total (green)** | **77** | **77** | **0**  | **0**   |

### Linter status

| Linter       | Result |
| ------------ | ------ |
| ruff         | Clean  |
| basedpyright | Clean  |
| clippy       | Clean  |
| markdownlint | Clean  |

### Key technical notes

- Key rotation Celery task tests are deferred to a follow-up story once `syntek-tasks` (US015) is
  available. The task scaffolding design is documented in US076 and the Celery task will be wired
  up when US015 completes.
- `apply_proxy_settings` uses `settings._wrapped.__dict__` rather than `hasattr` to detect
  project-configured settings. Django's `LazySettings` exposes global defaults via `hasattr` (e.g.
  `SECURE_PROXY_SSL_HEADER = None` is always present), but only values explicitly set by the project
  appear in `_wrapped.__dict__`. This ensures Syntek defaults are applied only when the project has
  not set them.
- The key versioning prefix is a backwards-compatible extension to the ciphertext layout from US006.
  The US006 implementation in `rust/syntek-crypto` was updated in this branch to support the
  2-byte version prefix transparently across `encrypt_field`, `decrypt_field`,
  `encrypt_fields_batch`, and `decrypt_fields_batch`.

---

## Sprint 05 Total Test Count

| Story | Rust | Python | Integration | Total |
| ----- | ---- | ------ | ----------- | ----- |
| US008 | 13   | 42     | 4           | 59    |
| US076 | 27   | 50     | 0           | 77    |
| **Sprint 05** | **40** | **92** | **4** | **136** |

All 136 tests passing. All linters clean.

---

## Next Steps

- US009 (`syntek-auth`) can now begin — its US076 dependency is satisfied
- Run `/syntek-dev-suite:version` to bump versions for `syntek-security` (new package), `syntek-auth`, and `syntek-crypto`
- Run `/syntek-dev-suite:git` to raise PRs for `us076/security-policy`
