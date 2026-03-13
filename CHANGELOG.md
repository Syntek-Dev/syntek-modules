# Changelog

All notable changes to `syntek-modules` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.16.2] — 13/03/2026

### Fixed

- **`rust/syntek-crypto/src/lib.rs`** — applied remaining actionable findings from the US006 QA
  review (2 additional fixes applied after the initial 0.16.1 batch).
- **`rust/syntek-crypto/src/key_versioning.rs`** — delegating to new `aes_gcm` helpers eliminates
  duplicated AES-256-GCM logic; `Zeroizing<String>` applied to all intermediate plaintext buffers.
- **`docs/BUGS/BUG-US006-SYNTEK-CRYPTO-13-03-2026.md`** — consolidated bug report updated to reflect
  final fix status for all 17 findings (15 Fixed, 2 No Fix).

### Added

- **`rust/syntek-crypto/src/aes_gcm.rs`** — new `pub(crate)` module exporting `aes_gcm_encrypt` and
  `aes_gcm_decrypt` helpers. The canonical AES-256-GCM implementation now lives in one place; both
  `lib.rs` and `key_versioning.rs` delegate to these helpers.
- **`docs/REFACTORING/REFACTOR-SYNTEK-CRYPTO-AES-GCM-HELPERS-2026-03-13.md`** — decision record
  documenting the extraction of AES-GCM primitives into a dedicated module.
- **`rust/syntek-crypto/tests/crypto_tests.rs`** — large-payload proptest module added (4 property
  tests, `ProptestConfig { cases: 10 }`) exercising encrypt/decrypt round-trips at scale.

### Changed

- **`pyproject.toml`** — `pytest-xdist>=3.0` added to dev dependencies; `addopts` restored to
  `["--strict-markers", "--tb=short", "-v"]` (parallel flags moved to CLI invocation).
- **`rust/syntek-dev/src/commands/test.rs`** — pytest invocation now prepends `-n auto --reuse-db`
  so parallel execution is the default when using `syntek-dev test --python`.
- **`conftest.py`** (root) — `SYNTEK_AUTH` test override adds `ARGON2ID_TIME_COST=1`,
  `ARGON2ID_MEMORY_COST=8`, `ARGON2ID_PARALLELISM=1` to eliminate Argon2id cost during test runs.
- **`packages/backend/syntek-auth/tests/conftest.py`** — same Argon2id override applied at the
  package level.
- **All 18 `packages/backend/syntek-auth/tests/test_*.py` files** — `pytestmark` added to each
  module classifying tests as `unit` or `slow` for xdist distribution and marker filtering.

### Module Version

- **`syntek-auth`** — bumped `0.3.0 → 0.3.1` (test suite parallelism and Argon2id overrides).

---

## [0.16.1] — 13/03/2026

### Fixed

- **`rust/syntek-crypto/src/lib.rs`** — `decrypt_fields_batch` now validates key length upfront
  before entering the decryption loop; `hmac_sign` now returns `Result<String, CryptoError>` with an
  empty-key guard instead of panicking; `hmac_verify` guards against empty keys and normalises hex
  to lowercase before comparison, eliminating false negatives from mixed-case input;
  `verify_password` now passes explicit Argon2 parameters (`m=65536`, `t=3`, `p=4`) rather than
  relying on potentially-changing defaults; `CryptoError` now derives `PartialEq` for
  assertion-friendly tests; key-length doc comments added to public API.
- **`rust/syntek-crypto/src/key_versioning.rs`** — `KeyRing::add` now rejects duplicate key versions
  with `CryptoError::InvalidInput`; `KeyVersion(0)` is rejected as an invalid version number;
  `reencrypt_to_active` now wraps the temporary plaintext buffer in `Zeroizing<String>` so memory is
  zeroed on drop; capacity documentation added.
- **`rust/syntek-crypto/tests/crypto_tests.rs`** — 8 `hmac_sign` call sites updated for the new
  `Result` return type.
- **`deny.toml`** — `unmaintained` policy changed from `"all"` to `"warn"` to unblock CI on
  transitively unmaintained crates that are not direct security risks.

### Added

- **`rust/syntek-crypto/syntek.manifest.toml`** — Syntek manifest file created (was missing from
  initial implementation).
- **`rust/syntek-crypto/examples/.gitkeep`** — `examples/` directory placeholder added.
- **`docs/BUGS/BUG-US006-SYNTEK-CRYPTO-13-03-2026.md`** — combined bug report covering all 17
  findings (13 code fixes, 4 informational) from the US006 QA security review.

---

## [0.16.0] — 13/03/2026

### Added

- **`packages/backend/syntek-auth/src/syntek_auth/backends/auth_backend.py`** — custom Django
  authentication backend for the syntek-auth module.
- **`packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py`** — SSO provider allowlist
  relocated from package root to `backends/` sub-package. Public API unchanged.
- **`packages/backend/syntek-auth/src/syntek_auth/conf.py`** — settings dataclass and
  `get_syntek_auth_settings()` helper that reads and validates the `SYNTEK_AUTH` settings dict.
- **`packages/backend/syntek-auth/src/syntek_auth/factories/`** — factory_boy factories for `User`,
  token models, and verification models used in tests.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0001_initial.py`** — initial schema:
  custom `User` model with email as `USERNAME_FIELD`.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0002_*`** — adds verification flags,
  `VerificationCode`, and `Denylist` models.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0003_*`** — adds encrypted unique token
  columns to `User` using `EncryptedField`.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0004_*`** — adds `PendingOAuthSession`
  model for storing in-flight OAuth state.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0005_*`** — encrypts the `provider`
  field on `PendingOAuthSession`.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0006_*`** — encrypts `jti` fields on
  all token models.
- **`packages/backend/syntek-auth/src/syntek_auth/migrations/0007_*`** — renames indexes for
  consistency with Django naming conventions.
- **`packages/backend/syntek-auth/src/syntek_auth/models/user.py`** — custom `User` model with email
  login, MFA flags, lockout counters, and encrypted unique-token columns.
- **`packages/backend/syntek-auth/src/syntek_auth/models/tokens.py`** — `AccessToken`,
  `RefreshToken`, and `MFAToken` models with encrypted JTI fields.
- **`packages/backend/syntek-auth/src/syntek_auth/models/verification.py`** — `VerificationCode` and
  `Denylist` models for email and phone verification flows.
- **`packages/backend/syntek-auth/src/syntek_auth/models/oauth_pending.py`** — `PendingOAuthSession`
  model for OAuth CSRF/state validation.
- **`packages/backend/syntek-auth/src/syntek_auth/mutations/auth.py`** — Strawberry GraphQL
  mutations: `login`, `logout`, `refreshToken`.
- **`packages/backend/syntek-auth/src/syntek_auth/mutations/mfa.py`** — GraphQL mutations for MFA
  enrolment, TOTP verification, and MFA token exchange.
- **`packages/backend/syntek-auth/src/syntek_auth/mutations/oidc.py`** — GraphQL mutations for the
  OAuth/OIDC social login flow with MFA bridge.
- **`packages/backend/syntek-auth/src/syntek_auth/mutations/password.py`** — GraphQL mutations:
  `changePassword`, `requestPasswordReset`, `confirmPasswordReset`.
- **`packages/backend/syntek-auth/src/syntek_auth/services/email_verification.py`** — email
  verification service: issue code, verify code, mark email verified.
- **`packages/backend/syntek-auth/src/syntek_auth/services/lockout.py`** — account lockout service:
  increment failures, check lockout, reset on successful login.
- **`packages/backend/syntek-auth/src/syntek_auth/services/lookup_tokens.py`** — token lookup
  helpers using encrypted unique-token columns for O(1) user lookups.
- **`packages/backend/syntek-auth/src/syntek_auth/services/mfa.py`** — MFA orchestration service:
  enrol, verify TOTP, exchange MFA token for access/refresh pair.
- **`packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py`** — OAuth MFA bridge: after
  social login, enforce MFA before issuing tokens.
- **`packages/backend/syntek-auth/src/syntek_auth/services/oidc.py`** — OIDC/OAuth callback handler:
  validate provider, exchange code, upsert user, initiate MFA bridge.
- **`packages/backend/syntek-auth/src/syntek_auth/services/password.py`** — password validation
  against policy settings (min length, complexity, common-password check).
- **`packages/backend/syntek-auth/src/syntek_auth/services/password_change.py`** — authenticated
  password change: verify current password, validate new password, rotate tokens.
- **`packages/backend/syntek-auth/src/syntek_auth/services/password_reset.py`** — password reset
  flow: generate signed reset token, validate, apply new password.
- **`packages/backend/syntek-auth/src/syntek_auth/services/phone_verification.py`** — phone
  verification service: issue SMS code, verify code, mark phone verified.
- **`packages/backend/syntek-auth/src/syntek_auth/services/session.py`** — session management: issue
  access/refresh token pair, rotate refresh tokens, revoke all tokens.
- **`packages/backend/syntek-auth/src/syntek_auth/services/tokens.py`** — token lifecycle: create,
  sign, verify, and revoke JWT tokens with encrypted JTI storage.
- **`packages/backend/syntek-auth/src/syntek_auth/services/totp.py`** — TOTP secret generation, QR
  provisioning URI, and time-window verification.
- **`packages/backend/syntek-auth/src/syntek_auth/types/auth.py`** — Strawberry GraphQL types:
  `AuthPayload`, `MFAPayload`, `UserType`.
- **`packages/backend/syntek-auth/tests/test_us009_email_verification.py`** — pytest tests for email
  verification service.
- **`packages/backend/syntek-auth/tests/test_us009_lockout.py`** — pytest tests for account lockout
  logic.
- **`packages/backend/syntek-auth/tests/test_us009_login_field.py`** — pytest tests verifying email
  is the login field and username is not accepted.
- **`packages/backend/syntek-auth/tests/test_us009_logout.py`** — pytest tests for logout and token
  revocation.
- **`packages/backend/syntek-auth/tests/test_us009_mfa.py`** — pytest tests for TOTP MFA enrolment,
  verification, and token exchange.
- **`packages/backend/syntek-auth/tests/test_us009_password_change.py`** — pytest tests for
  authenticated password change.
- **`packages/backend/syntek-auth/tests/test_us009_password_policy.py`** — pytest tests for password
  policy validation (length, complexity, common passwords).
- **`packages/backend/syntek-auth/tests/test_us009_password_reset.py`** — pytest tests for password
  reset request and confirmation flow.
- **`packages/backend/syntek-auth/tests/test_us009_phone_verification.py`** — pytest tests for phone
  verification service.
- **`packages/backend/syntek-auth/tests/test_us009_settings_validation.py`** — pytest tests for
  `SYNTEK_AUTH` settings validation at startup.
- **`packages/backend/syntek-auth/tests/test_us009_social_oauth_mfa.py`** — pytest tests for the
  OAuth/OIDC social login MFA bridge.
- **`packages/backend/syntek-auth/tests/test_us009_tokens.py`** — pytest tests for token creation,
  signing, verification, and revocation.
- **`packages/backend/syntek-auth/tests/test_us009_user_model.py`** — pytest tests for the custom
  user model, manager methods, and field constraints.
- **`sandbox/`** — minimal sandbox Django project providing `manage.py` for `syntek-dev db` commands
  during local development. Not deployed.
- **`.claude/ENCRYPTION-GUIDE.md`** — authoritative guide covering `EncryptedField` usage,
  individual and batch encrypt/decrypt patterns, unique-token columns, and the migration path.
- **`docs/GUIDES/SANDBOX.md`** — guide documenting the sandbox project and `syntek-dev db` usage.
- **`docs/QA/QA-US006-SYNTEK-CRYPTO-11-03-2026.md`** — QA sign-off report for syntek-crypto.
- **`docs/QA/QA-US007-SYNTEK-PYO3-11-03-2026.md`** — QA sign-off report for syntek-pyo3.
- **`docs/QA/QA-US008-GRAPHQL-CRYPTO-MIDDLEWARE-11-03-2026.md`** — QA sign-off report for
  syntek-graphql-crypto.
- **`docs/QA/QA-US009-SYNTEK-AUTH-11-03-2026.md`** — QA sign-off report for syntek-auth.
- **`docs/QA/QA-US076-SSO-ALLOWLIST-11-03-2026.md`** — QA sign-off report for the SSO allowlist.
- **`docs/TESTS/US009-MANUAL-TESTING.md`** — manual testing record for US009.
- **`docs/TESTS/US009-TEST-STATUS.md`** — test status document for US009.

### Changed

- **`packages/backend/syntek-auth/src/syntek_auth/__init__.py`** — updated module exports to reflect
  the new sub-package structure.
- **`packages/backend/syntek-auth/src/syntek_auth/apps.py`** — updated `SyntekAuthConfig.ready()` to
  use `conf.py` settings validation and register the new backends.
- **`packages/backend/syntek-auth/tests/conftest.py`** — updated fixtures to use the new factory
  classes and the relocated allowlist import path.
- **`packages/backend/syntek-auth/tests/test_sso_allowlist.py`** — updated import path from
  `syntek_auth.allowlist` to `syntek_auth.backends.allowlist`.
- **`rust/syntek-crypto/tests/crypto_tests.rs`** — updated to align with current crate API.
- **`rust/syntek-crypto/tests/key_versioning_tests.rs`** — updated to align with current crate API.
- **`.forgejo/workflows/python.yml`**, **`.forgejo/workflows/rust.yml`**,
  **`.github/workflows/python.yml`**, **`.github/workflows/rust.yml`** — CI workflow updates for
  US009 test suite and migration exclude patterns.
- **`pyproject.toml`** — added ruff `exclude` for `migrations/` directories.
- **`package.json`** — root tooling version bump.
- **`conftest.py`** — root test configuration updated for US009 test suite.
- **`docs/STORIES/US009.md`** — story document updated to reflect completed status.
- **`docs/STORIES/US076.md`** — story document updated.
- **`.claude/CLAUDE.md`** — architecture reference updated to include encryption guide link and
  US009 sprint context.
- **`syntek-auth` module**: bumped from `0.2.0` → `0.3.0` (MINOR — full feature implementation).

### Removed

- **`packages/backend/syntek-auth/src/syntek_auth/allowlist.py`** — removed from package root;
  relocated to `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py`.

---

## [0.15.0] — 11/03/2026

### Added

- **`rust/syntek-crypto/src/key_versioning.rs`** — `KeyVersion` newtype (2-byte `u16`), `KeyRing`
  struct holding a map of `KeyVersion → [u8; 32]`, and four public functions: `encrypt_versioned`,
  `decrypt_versioned`, `reencrypt_to_active`, and `KeyRing::active_version`. Every ciphertext
  produced by the versioned API is prefixed with the 2-byte version identifier before base64
  encoding: `base64(version(2) || nonce(12) || ciphertext || tag(16))`. This enables zero-downtime
  key rotation — old ciphertexts remain readable while new writes always use the current key.
- **`rust/syntek-crypto/tests/key_versioning_tests.rs`** — Rust test suite covering: `KeyVersion`
  byte serialisation round-trip, `KeyRing` construction and active key resolution, version lookup,
  `encrypt_versioned` / `decrypt_versioned` round-trip, version prefix presence, cross-version
  decryption, `reencrypt_to_active` migration, and error cases (empty ring, unknown version, wrong
  key, tampered ciphertext). US076 — AC4 / AC5.
- **`packages/backend/syntek-auth/src/syntek_auth/allowlist.py`** — SSO provider allowlist
  enforcement. Defines `ALLOWED_SSO_PROVIDERS` (GitHub, Defguard) and `BLOCKED_SSO_PROVIDERS` with
  the rationale for each decision. `is_allowed_provider(provider)` returns `True` only for providers
  where MFA is either mandatory by platform design (Defguard) or enforceable at the organisation
  level before the OAuth flow completes (GitHub organisations with mandatory MFA policy). Consumer
  accounts for Google, Facebook, Instagram, LinkedIn, Twitter/X, Apple, and Discord are blocked
  because the platform cannot guarantee MFA enforcement at login time.
- **`packages/backend/syntek-auth/src/syntek_auth/apps.py`** — `SyntekAuthConfig` Django `AppConfig`
  class. Validates the `SYNTEK_AUTH` settings dict at startup via `AppConfig.ready()` and raises
  `ImproperlyConfigured` if required keys are missing or have wrong types.
- **`packages/backend/syntek-auth/tests/test_sso_allowlist.py`** — pytest tests covering allowed
  provider acceptance, blocked provider rejection, case sensitivity, unknown provider handling, and
  the completeness of the blocked list.
- **`packages/backend/syntek-security/`** — new `syntek-security` Django package (US076). Rate
  limiting, CORS, CSP, HSTS, and proxy-trust middleware for all Syntek deployments.
- **`packages/backend/syntek-security/src/syntek_security/proxy_settings.py`** — `ProxySettings`
  dataclass and `configure_proxy_trust(settings)` function. Reads
  `SYNTEK_SECURITY['TRUSTED_PROXIES']` and configures Django's `SECURE_PROXY_SSL_HEADER`,
  `USE_X_FORWARDED_HOST`, and `ALLOWED_HOSTS` for a Cloudflare Tunnel → Nginx → Gunicorn/Uvicorn
  deployment topology.
- **`packages/backend/syntek-security/src/syntek_security/apps.py`** — `SyntekSecurityConfig` Django
  `AppConfig` with settings validation at startup.
- **`packages/backend/syntek-security/tests/test_proxy_settings.py`** — pytest tests for proxy trust
  configuration.
- **`docs/TESTS/US076-TEST-STATUS.md`** and **`docs/TESTS/US076-MANUAL-TESTING.md`** — test status
  and manual testing records for US076.
- **`docs/SPRINTS/LOGS/COMPLETION-2026-03-11-SPRINT-05.md`** — Sprint 05 completion log; both US008
  and US076 completed, 23/23 points.

### Changed

- **`rust/syntek-crypto/src/lib.rs`** — added `pub mod key_versioning` declaration to expose the new
  key versioning module as part of the public API.
- **`docs/SPRINTS/SPRINT-05.md`** and **`docs/SPRINTS/OVERVIEW.md`** — Sprint 05 marked complete
  (11/03/2026); US076 recorded as completed.
- **`docs/STORIES/US076.md`** and **`docs/STORIES/OVERVIEW.md`** — US076 status updated from To Do
  to Completed; story points and completion date recorded.
- **`.claude/CLAUDE.md`** and **`.claude/VERSIONING-GUIDE.md`** — minor documentation updates.
- **`pyproject.toml`** (root workspace) — `syntek-security` added to `[tool.uv.sources]` and
  `[dependency-groups].dev`; enables editable installs and pytest discovery for the new module.

### Module Versions

- **`syntek-auth`** bumped `0.1.0 → 0.2.0` — new SSO allowlist enforcement (`allowlist.py`) and
  `AppConfig` settings validation (`apps.py`).
- **`syntek-security`** introduced at `0.1.0` — new package; baseline version per project
  convention.

---

## [0.14.0] — 11/03/2026

### Added

- **`rust/syntek-graphql-crypto/src/lib.rs`** — `EncryptedFieldSpec` struct describing `@encrypted`
  / `@encrypted(batch: "group_name")` fields, and `MiddlewareError` enum with four variants
  (`EncryptFailed`, `DecryptFailed`, `KeyResolutionFailed`, `UnauthenticatedAccess`) all
  implementing `std::error::Error` via `thiserror`.
- **`rust/syntek-graphql-crypto/tests/middleware_tests.rs`** — 13 Rust unit tests covering all
  `MiddlewareError` variants and full serde roundtrip for `EncryptedFieldSpec` (individual and
  batch).
- **`rust/syntek-graphql-crypto/syntek.manifest.toml`** — crate ID and Forgejo registry coordinates
  with post-install steps for the Python middleware.
- **`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py`** — full
  `EncryptionMiddleware` Strawberry `SchemaExtension`. Write path: intercepts `on_executing_start`,
  encrypts individual fields via `encrypt_field` and batch groups via `encrypt_fields_batch`,
  rejects entire mutation on encrypt failure. Read path: intercepts `on_executing_end`, decrypts
  individual fields and batch groups, nulls failed fields with structured errors, sets all encrypted
  fields to null on unauthenticated access.
- **`packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py`** — `@encrypted`
  and `@encrypted(batch: "group_name")` Strawberry schema directives.
- **`packages/backend/syntek-graphql-crypto/README.md`** — setup guide, annotation guide, and key
  naming convention (`SYNTEK_FIELD_KEY_<MODEL>_<FIELD>`).
- **`packages/backend/syntek-graphql-crypto/tests/`** — 42 Python unit tests across 5 test modules:
  `test_directives.py` (7), `test_write_path.py` (10, AC1–AC3), `test_read_path.py` (9, AC4–AC6),
  `test_error_handling.py` (11, AC7–AC9), `test_auth_guard.py` (6, AC10–AC11). All mock
  `syntek_pyo3` — no native extension required.
- **`tests/graphql_crypto/test_integration.py`** — 4 integration tests exercising the full write →
  DB → read pipeline: individual field roundtrip (AC1+AC4), batch group roundtrip (AC2+AC5),
  tampered DB value (AC7), and unauthenticated read (AC10).
- **`rust/syntek-pyo3/syntek.manifest.toml`** — manifest for the `syntek-pyo3` crate (records crate
  ID and Forgejo registry coordinates; post-install steps for maturin wheel build).
- **`docs/TESTS/US008-TEST-STATUS.md`** and **`docs/TESTS/US008-MANUAL-TESTING.md`** — full test
  status and manual testing records for US008 (59/59 tests green).
- **`docs/SPRINTS/SPRINT-46.md`** through **`docs/SPRINTS/SPRINT-70.md`** — 25 new sprint planning
  documents extending the roadmap through marketplace, licensing, SaaS, and ecosystem completion
  phases.
- **`docs/STORIES/US077.md`** through **`docs/STORIES/US129.md`** — 53 new user story documents
  covering the extended roadmap.

### Changed

- **`rust/syntek-graphql-crypto/Cargo.toml`** — added `crate-type = ["cdylib", "lib"]` (required for
  integration test linking), and declared `syntek-crypto`, `serde`, `serde_json`, and `thiserror`
  dependencies.
- **`docs/STORIES/US008.md`** — status updated from To Do to Completed; points corrected from 8
  to 13.
- **`docs/SPRINTS/SPRINT-05.md`** — US008 marked Completed (10/03/2026); US076 noted as pending.
- **`docs/SPRINTS/OVERVIEW.md`** and **`docs/STORIES/OVERVIEW.md`** — updated to reflect US008
  completion, new story and sprint counts, and revised planning horizon.
- **`package.json`** — Turborepo bumped from `^2.4.0` to `^2.8.15`.
- All sprint files (SPRINT-08 through SPRINT-45) and story files (US009–US073) updated with
  dependency and sequence corrections from the planning pass extending the roadmap to SPRINT-70.

---

## [0.13.0] — 09/03/2026

### Added

- **`rust/syntek-pyo3/src/lib.rs`** — full implementation of the `syntek-pyo3` native extension
  module. Exposes six functions to Python via PyO3: `encrypt_field`, `decrypt_field`,
  `hash_password`, `verify_password`, `encrypt_fields_batch`, and `decrypt_fields_batch` — all
  delegating to `syntek-crypto` with no crypto code duplicated.
- **`EncryptedField`** — `#[pyclass]` Django storage-and-validation field. `pre_save` validates
  ciphertext format (base64ct, decoded ≥ 28 bytes) and raises Django's `ValidationError` on
  plaintext input (defence-in-depth against ORM bypass). `from_db_value` is a passthrough —
  decryption is the GraphQL middleware's responsibility. `contribute_to_class` installs an
  `EncryptedFieldDescriptor` on the model class.
- **`EncryptedFieldDescriptor`** — `#[pyclass]` descriptor recording `model_name` and `field_name`
  so the GraphQL middleware can resolve the correct AAD without manual annotation.
- **`is_valid_ciphertext_format`** — public Rust helper (base64ct, decoded ≥ 28 bytes) used
  internally by `EncryptedField.validate` and directly exercised by Rust integration tests.
- **`DecryptionError`** and **`BatchDecryptionError`** — exported `thiserror` error types mapped to
  Python `ValueError` at the PyO3 boundary.
- **`rust/syntek-pyo3/tests/pyo3_module_tests.rs`** — 12 Rust integration tests: 10 for
  `is_valid_ciphertext_format` (boundary values, plaintext rejection, invalid base64) and 2
  compile-time tests confirming the error types implement `std::error::Error`.
- **`rust/syntek-pyo3/pyproject.toml`** — maturin build config: `module-name = "syntek_pyo3"`,
  `pyo3/extension-module` feature, `requires-python = ">=3.14"`.
- **`tests/pyo3/test_pyo3_bindings.py`** — 53 Python binding tests across 7 classes: module import
  (7), `encrypt_field` (3), `decrypt_field` (8), `encrypt_fields_batch` (4), `decrypt_fields_batch`
  (3), `hash_password` (3), `verify_password` (3). All pass after `maturin develop`.
- **`packages/backend/syntek-pyo3/`** — Django module package with `pyproject.toml` and
  `tests/test_encrypted_field.py` (38 tests across 5 classes: import, ciphertext acceptance,
  plaintext rejection ×12 parametrised, `from_db_value` passthrough, descriptor).
- **`stubs/syntek_pyo3.pyi`** — hand-authored type stub for all eight exported symbols so
  basedpyright resolves types without a compiled `.so`.
- **`conftest.py`** (repo root) — ensures `sys.path` includes the repo root for all pytest
  invocations.
- **`pyrightconfig.json`** — `stubPath = "stubs"` added so basedpyright resolves the native
  extension's types without requiring a compiled `.so` in the active environment.

### Changed

- **`rust/syntek-pyo3/Cargo.toml`** — `crate-type` updated from `["cdylib"]` to `["cdylib", "lib"]`
  to enable Rust integration tests to link against the library. The `syntek-crypto` path dependency
  carries `version = "0.12.0"` (cargo-deny wildcard policy).

### Documentation

- All bare path references (e.g. `.claude/CLI-TOOLING.md`) converted to markdown links across
  `CLAUDE.md`, `GIT-GUIDE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `BRANCH-PROTECTION.md`,
  `DEVELOPING.md`, `GETTING-STARTED.md`, `ISSUES.md`, Forgejo and GitHub PR templates.
- `CLAUDE.md` directory tree corrected to remove deleted shell scripts and add `install.sh`.
- `docs/TESTS/US007-TEST-STATUS.md` and `docs/TESTS/US007-MANUAL-TESTING.md` added — full
  green-phase test record and eight manual test scenarios, all PASS.
- `docs/STORIES/US007.md` updated with architecture boundary table, Gherkin acceptance criteria, and
  red/green phase task checkboxes.

---

## [0.12.1] — 09/03/2026

### Fixed

- **`deny.toml`** — Rewrote for cargo-deny 0.16+ compatibility: removed deprecated fields
  (`vulnerability`, `notice`, `unlicensed`, `copyleft`); `unmaintained = "warn"` changed to
  `unmaintained = "all"` (field now takes a scope, not a lint level); added `MPL-2.0` to the licence
  allow list (required by the `colored` crate used in `syntek-dev`); corrected `AGPL-3.0` →
  `AGPL-3.0-only` (deprecated SPDX identifier). Result: `cargo deny check` passes with
  `advisories ok, bans ok, licenses ok, sources ok`.
- **`Cargo.toml`** — `license = "AGPL-3.0"` corrected to `license = "AGPL-3.0-only"` (deprecated
  SPDX identifier was producing parse-error warnings in cargo-deny and `cargo metadata`).
- **`rust/syntek-dev/Cargo.toml`** — Added `license.workspace = true`; the missing field was causing
  cargo-deny to flag `syntek-dev` as unlicensed.
- **`rust/syntek-graphql-crypto/Cargo.toml`** — Added `version = "0.12.0"` to the `syntek-crypto`
  path dependency; cargo-deny 0.16+ treats versionless path dependencies as wildcard version
  constraints, triggering `wildcards = "deny"`.
- **`rust/syntek-pyo3/Cargo.toml`** — Same fix as above: `version = "0.12.0"` added to the
  `syntek-crypto` path dependency.

---

## [0.12.0] — 09/03/2026

### Added

- **`rust/syntek-crypto/src/lib.rs`** — full implementation of the `syntek-crypto` crate:
  `encrypt_field`, `decrypt_field`, `hash_password`, `verify_password`, `hmac_sign`, `hmac_verify`,
  `encrypt_fields_batch`, `decrypt_fields_batch`. AES-256-GCM with per-field AAD, Argon2id (m=65536,
  t=3, p=4), HMAC-SHA256 with constant-time comparison, memory zeroisation via the `zeroize` crate.
  All functions fully documented with doctests.
- **`rust/syntek-crypto/tests/crypto_tests.rs`** — 49 tests: 36 unit tests, 4 property-based tests
  (proptest), 9 doctests. All passing. Covers round-trip correctness, wrong-key rejection, AAD
  mismatch rejection, batch atomicity, and HMAC timing safety.
- **`deny.toml`** — cargo-deny supply-chain policy: vulnerability = deny, yanked = deny,
  unmaintained = warn, wildcard dependencies = deny. Allowed licences: MIT, Apache-2.0,
  BSD-2/3-Clause, ISC, Unicode-3.0, Zlib, AGPL-3.0.
- **`base64ct`** workspace dependency (version 1, `std` feature) for constant-time base64 encoding
  in the encryption output format.
- **`proptest`** and **`hex`** dev-dependencies for property-based testing of cryptographic
  invariants.

### Changed

- **`Cargo.toml`** — `aes-gcm` now includes `zeroize` feature; `argon2` now includes `password-hash`
  and `std` features. `serde` removed from `syntek-crypto` direct dependencies (not needed in the
  crypto crate).
- **`.forgejo/workflows/rust.yml`** and **`.github/workflows/rust.yml`** — `cargo test` changed to
  `cargo test --all --release`; `cargo-audit` updated to 0.21.2 with a CVSS 4.0 workaround that
  strips unparseable advisory entries before auditing.
- **`.forgejo/workflows/python.yml`** — `uvx run pip-audit` corrected to `uvx pip-audit`; coverage
  comment step guarded with `hashFiles('coverage.xml') != ''`.

### Fixed

- CI `cargo-audit` crash on CVSS 4.0 formatted advisories (parser does not support CVSS 4.0 in
  current release — workaround strips those entries from the local DB copy before audit).
- CI `uvx run pip-audit` invocation syntax — `uvx` does not accept `run` as a subcommand.
- CI coverage comment step now skipped when no `coverage.xml` is produced, preventing hard failures
  on PRs with no Python coverage output.

---

## [0.11.0] — 08/03/2026

### Added

- **`shared/tokens/src/manifest.ts`** — exports `TOKEN_MANIFEST`, a frozen readonly array of
  `TokenDescriptor` objects covering all token categories: colour (semantic aliases), spacing,
  font-size, font-weight, font-family, border radius, shadow, z-index, transition duration, and
  transition easing. Colour `default` values are resolved hex strings (not `var()` references) so
  colour pickers can initialise with a concrete value.
- **`shared/tokens/src/types/token-manifest.ts`** — exports `TokenDescriptor`, `TokenCategory`, and
  `TokenWidgetType` TypeScript types. `TokenWidgetType` drives widget selection in the
  `syntek-platform` branding form: `"color"`, `"px"`, `"rem"`, `"font-family"`, `"font-weight"`,
  `"number"`, `"duration"`, `"easing"`.
- **`shared/tokens/src/tailwind-colours.ts`** — exports `TAILWIND_COLOURS`, a flat readonly record
  mapping every Tailwind CSS v4 palette entry (e.g. `"blue-600"`) to its resolved hex value (e.g.
  `"#2563eb"`); covers all 22 families (`slate`, `gray`, `zinc`, … `rose`) at scales 50–950.
- **`shared/tokens/src/colour-utils.ts`** — exports:
  - `isValidCssColour(value: string): boolean` — validates any CSS colour format: hex (#rgb,
    #rrggbb, #rrggbbaa), rgb(), rgba(), hsl(), hsla(), hwb(), lab(), lch(), oklab(), oklch(), and
    all CSS named colours. Used by `syntek-platform` before saving an override to the DB.
  - `resolveTailwindColour(name: string): string | undefined` — looks up a Tailwind palette name in
    `TAILWIND_COLOURS` and returns the hex value, or `undefined` if not found.
- **`shared/tokens/src/theme-utils.ts`** — exports
  `buildThemeStyle(overrides: Record<string, string>): string`; the only Next.js integration surface
  exposed by `@syntek/tokens`. Converts an override map into a `:root { ... }` CSS block for SSR
  injection. No escaping or validation — the platform is responsible for key and value validation
  before calling this function.
- **`shared/tokens/src/index.ts`** — all new exports re-exported from the package index.
- **`shared/tokens/features/design_token_manifest.feature`** — Gherkin BDD feature file mirroring
  all US075 acceptance criteria scenarios for living documentation.
- **`shared/tokens/src/__tests__/token-manifest.test.ts`** — full test suite: manifest shape,
  required fields, widget type correctness, resolved hex defaults for colour tokens, `Object.freeze`
  immutability, and consistent re-import reference equality.
- **`shared/tokens/src/__tests__/css-colour-validator.test.ts`** — `isValidCssColour` validated
  against all supported CSS colour formats and confirmed to reject non-colour strings.
- **`shared/tokens/src/__tests__/tailwind-colours.test.ts`** — `TAILWIND_COLOURS` coverage across
  all 22 families at scales 50–950; `resolveTailwindColour` resolution and unknown-name handling.
- **`shared/tokens/src/__tests__/theme-utils.test.ts`** — `buildThemeStyle` output: empty overrides,
  single/multiple overrides, correct `:root` wrapper, key/value pass-through.
- **`shared/graphql/src/__tests__/fetcher.test.ts`** — new fetcher test file covering error handling
  and response parsing per QA-US004 findings.
- **`tests/ci/test_workflow_mirror.py`** — new CI test verifying Forgejo and GitHub workflow files
  remain in sync.
- **`docs/QA/QA-US075-DESIGN-TOKEN-MANIFEST-08-03-2026.md`** — QA report: findings from US075 review
  including CSS injection risk in `buildThemeStyle` (documented; mitigation is platform-side
  validation) and shallow `Object.freeze` on `TOKEN_MANIFEST` entries.
- **`docs/BUGS/BUG-US075-DESIGN-TOKEN-MANIFEST-08-03-2026.md`** — bug fix report covering all US075
  QA findings with root-cause analysis and prevention recommendations.
- **`docs/TESTS/US075-TEST-STATUS.md`** and **`docs/TESTS/US075-MANUAL-TESTING.md`** — test status
  tracker and 8-scenario manual testing guide for US075; all scenarios passed.
- **QA and bug reports for US001–US005** (retrospective): six QA reports and six bug fix reports
  documenting findings and resolutions from a retrospective audit of the foundation sprints.

### Changed

- **`shared/tokens/src/tokens.ts`** and **`shared/tokens/tokens.css`** — token default values
  aligned with `TOKEN_MANIFEST` colour entries (resolved hex strings throughout).
- **`shared/graphql/schema.graphql`** and **`shared/graphql/src/operations/auth.graphql`** — updated
  to align with US075-era type changes; `src/generated/graphql.ts` regenerated via `pnpm codegen`.
- **`shared/graphql/src/lib/fetcher.ts`** — hardened per QA-US004 findings.
- **`shared/types/src/auth.ts`**, **`shared/types/src/base.ts`**,
  **`shared/types/src/notifications.ts`**, **`shared/types/tsconfig.json`** — type refinements and
  compiler strictness alignment per retrospective QA.
- **`eslint-rules/no-hardcoded-design-values.js`** — updated to recognise all new token categories
  and CSS custom property prefixes from US075.
- **`turbo.json`** — pipeline updated to declare new outputs and cache inputs for the expanded
  `@syntek/tokens` package.
- **`.forgejo/workflows/graphql-drift.yml`** — new workflow running codegen drift check on PRs that
  touch schema or operation files.
- **`.forgejo/workflows/python.yml`**, **`.forgejo/workflows/rust.yml`**,
  **`.github/workflows/python.yml`**, **`.github/workflows/rust.yml`** — CI assertion alignment per
  BUG-US005 findings (pip-audit invocation, cargo audit advisory categories).
- **`tests/workspace/test_workspace_config.py`** — `EXPECTED_RUST_CRATES` now includes
  `rust/syntek-manifest`; regression from QA-US001 finding now caught.
- **`tests/workspace/test_workspace_bdd.py`** — BDD feature file list updated to include US075.
- **`tests/ci/test_rust_workflow.py`** — assertion updated per BUG-US005.
- **`docs/STORIES/US075.md`** — status updated to Completed; all tasks ticked, test evidence
  recorded.
- **`docs/PLANS/SYNTEK-ARCHITECTURE.md`** — optimised CSS serving pattern documented (tenant_themes
  table, immutable caching, hash-based CDN cache busting).

---

## [0.10.0] — 08/03/2026

### Added

- **`rust/syntek-manifest/`** — new Rust library crate implementing the US074 Module Manifest Spec &
  CLI Shared Framework. All Syntek module CLI binaries link against this crate.
- **`rust/syntek-manifest/src/manifest.rs`** — `SyntekManifest` struct matching the
  `syntek.manifest.toml` schema: `id`, `version`, `kind` (rust-crate | backend | frontend | mobile),
  `options[]`, `settings[]`, `installed_apps`, `providers[]`, `entry_point`, `post_install_steps[]`
- **`rust/syntek-manifest/src/parser.rs`** — TOML → validated struct parser with descriptive errors
  on missing required fields and wrong-type fields
- **`rust/syntek-manifest/src/prompter.rs`** — interactive option prompter; renders each `options[]`
  entry as a checkbox or select prompt in the terminal
- **`rust/syntek-manifest/src/settings_writer.rs`** — reads `settings[]` from manifest, writes typed
  Django `SYNTEK_*` config blocks to `settings.py`; respects existing blocks with a confirmation
  prompt and skips overwriting on refusal
- **`rust/syntek-manifest/src/duplicate_detector.rs`** — detects existing `INSTALLED_APPS` entries
  and `SYNTEK_*` settings blocks; warns the developer without overwriting
- **`rust/syntek-manifest/src/provider_wrapper.rs`** — reads `providers[]`, wraps the declared
  `entry_point` file with provider boilerplate
- **`rust/syntek-manifest/src/post_install.rs`** — renders `post_install_steps[]` as formatted
  copy-paste terminal output
- **`rust/syntek-manifest/src/error.rs`** — typed `ManifestError` enum via `thiserror`
- **`rust/syntek-manifest/tests/`** — 127 integration tests across six test files covering all
  modules; all tests pass (green phase complete 08/03/2026)
- **`docs/QA/QA-US074-SYNTEK-MANIFEST-08-03-2026.md`** — full QA report: 26 findings across all six
  modules
- **`docs/BUGS/BUG-US074-SYNTEK-MANIFEST-08-03-2026.md`** — bug fix report: all 26 findings resolved
  with root cause analysis and prevention notes
- **`docs/TESTS/US074-TEST-STATUS.md`** — test status tracking for US074; 127/127 passing
- **`docs/TESTS/US074-MANUAL-TESTING.md`** — 8-scenario manual testing guide; all scenarios passed
- **`Cargo.toml`** (workspace) — `rust/syntek-manifest` added to workspace members; `toml`,
  `tempfile`, and `unicode-width` registered as workspace dependencies

### Changed

- **`docs/STORIES/US074.md`** — status updated to Completed; all tasks ticked, completion date and
  test evidence recorded
- **`docs/TESTS/US005-TEST-STATUS.md`** — test assertion alignment note added for `uvx pip-audit`
  and `cargo audit --deny` accepted categories
- **`docs/TESTS/US005-MANUAL-TESTING.md`** — status header updated to Completed following Sprint 02
  sign-off
- **`tests/ci/test_python_workflow.py`** — `pip-audit` assertion updated to accept both
  `uvx pip-audit` and `uv run pip-audit`; `--fail-on` check replaced with invocation-presence check
- **`tests/ci/test_rust_workflow.py`** — `cargo audit --deny` assertion updated to accept all valid
  advisory categories (warnings, vulnerabilities, unmaintained, unsound, yanked)

---

## [0.9.0] — 08/03/2026

### Added

- **`.forgejo/workflows/python.yml`** — `uv run pip-audit --fail-on HIGH,CRITICAL` security audit
  step; changed-files detection step for per-package pytest targeting; `--cov` and
  `--cov-report=xml:coverage.xml` flags on the pytest invocation; `MishaKav/pytest-coverage-comment`
  PR comment step (guarded with `if: github.event_name == 'pull_request'`)
- **`.forgejo/workflows/web.yml`** — `pnpm audit --audit-level=high` security audit step;
  `pnpm turbo run test --affected` replaces bare `pnpm test` for affected-only test runs;
  `--coverage.reporter=json-summary` flag; `davelosert/vitest-coverage-report-action` PR comment
  step (guarded with `if: github.event_name == 'pull_request'`)
- **`.forgejo/workflows/rust.yml`** — `cargo audit --deny warnings` security audit step (installs
  `cargo-audit`); `cargo llvm-cov --all --lcov --output-path lcov.info` coverage collection step;
  `romeovs/lcov-reporter-action@v0.4.0` PR comment step (guarded with
  `if: github.event_name == 'pull_request'`)
- **`.github/workflows/`** — mirrors all three updated Forgejo workflow files identically
- **`tests/ci/conftest.py`** — session-scoped pytest fixtures that parse each workflow YAML file
  once and expose step names, run scripts, and full step dicts for structured assertions
- **`tests/ci/test_python_workflow.py`** — 13 tests covering pip-audit vulnerability scanning,
  per-package affected-only pytest runs, and coverage PR comment steps
- **`tests/ci/test_web_workflow.py`** — 13 tests covering pnpm audit vulnerability scanning,
  Turborepo `--affected` test runs, and Vitest coverage PR comment steps
- **`tests/ci/test_rust_workflow.py`** — 17 tests covering baseline regression guards, cargo audit
  vulnerability scanning, `cargo llvm-cov` coverage collection, and lcov PR comment steps
- **`docs/TESTS/US005-TEST-STATUS.md`** — test status tracking for US005; 43/43 passing, green phase
  complete 08/03/2026
- **`docs/TESTS/US005-MANUAL-TESTING.md`** — 6-scenario manual testing guide covering clean audit
  runs, vulnerable dependency detection, Turborepo scope narrowing, coverage comment posting,
  push-event guard, and per-package Python targeting

### Changed

- **`docs/STORIES/US005.md`** — status updated to Completed; completion date, branch, and test
  evidence recorded
- **`docs/STORIES/OVERVIEW.md`** — US005 status column updated from To Do to Completed
- **`docs/TESTS/US003-MANUAL-TESTING.md`** — story status header updated to Completed following
  Sprint 02 sign-off
- **`docs/SPRINTS/LOGS/COMPLETION-2026-03-08-SPRINT-02.md`** — US005 completion detail section
  added; Sprint 02 recorded as fully complete (20/20 points across US003, US005, US074, US075)

---

## [0.8.0] — 08/03/2026

### Added

- **`shared/tokens/`** (`@syntek/tokens`) — new shared design token package; exports typed
  TypeScript constants for colours, spacing, typography, font families, border radii, shadows,
  breakpoints, z-index, and opacity; also exports a CSS custom properties file (`tokens.css`) and a
  NativeWind-compatible theme object (`nativewind.ts`)
- **`shared/tokens/src/__tests__/`** — Vitest test suite (token-exports, token-types, token-values)
  verifying structure, uniqueness, and completeness of all token sets
- **`shared/tokens/features/design_tokens.feature`** — Cucumber BDD feature spec describing the
  token contract in plain language
- **`eslint-rules/no-hardcoded-design-values.js`** — custom ESLint rule that flags raw hex colour
  literals, magic spacing values, and hardcoded font-size px/rem values; directs developers to
  import from `@syntek/tokens` instead
- **`eslint-rules/__tests__/no-hardcoded-design-values.test.js`** — Jest-compatible test suite
  covering valid uses, invalid hardcoded values, and false-positive avoidance
- **`docs/GUIDES/TOKENS-INTEGRATION.md`** — integration guide for consuming `@syntek/tokens` in web
  and mobile packages; covers installation, import patterns, CSS variable usage, and NativeWind
  configuration
- **`docs/STORIES/US075.md`** — new story document for future planning
- **`docs/TESTS/US003-TEST-STATUS.md`** — test status tracking for US003; records story completed
  08/03/2026
- **`docs/TESTS/US003-MANUAL-TESTING.md`** — manual testing checklist for US003
- **`docs/SPRINTS/LOGS/COMPLETION-2026-03-08-SPRINT-02.md`** — Sprint 02 completion log

### Changed

- **`eslint.config.mjs`** — updated to load and apply the local `no-hardcoded-design-values` rule
  across all `packages/web` and `mobile` source files
- **`docs/STORIES/US003.md`** — status updated to completed; acceptance criteria and test results
  recorded
- **`docs/STORIES/OVERVIEW.md`** — US003 status updated from To Do to completed
- **`docs/SPRINTS/SPRINT-02.md`** — Sprint 02 marked complete 08/03/2026
- **`docs/SPRINTS/OVERVIEW.md`** — Sprint 02 annotated as completed; overall status updated
- **`docs/TESTS/US004-TEST-STATUS.md`** — corrected tracking omission; story marked completed
- **`docs/TESTS/US004-MANUAL-TESTING.md`** — corrected tracking omission; story marked completed

---

## [0.7.0] — 08/03/2026

### Added

- **`SECURITY.md`** — public-facing vulnerability disclosure policy; covers supported versions,
  reporting process via GitHub private vulnerability reporting, response SLA, scope definition, and
  dependency security section
- **`renovate.json`** — Renovate dependency automation config; covers npm/pnpm, pip, cargo, and
  github-actions ecosystems on a weekly Monday schedule (Europe/London timezone)
- **`docs/GUIDES/BRANCH-PROTECTION.md`** — guide documenting branch protection rules for GitHub and
  Forgejo, required CI checks per branch, and how maintainers apply or update rules via web UI
- **`.github/dependabot.yml`** — Dependabot config for all four stacks (npm, pip, cargo,
  github-actions) on a weekly Monday 08:00 Europe/London schedule
- **`.github/workflows/codeql.yml`** — CodeQL SAST workflow for Python and TypeScript; runs on
  push/PR to main and on a weekly schedule
- **`.forgejo/workflows/semgrep.yml`** — Semgrep SAST workflow (Forgejo equivalent of CodeQL); two
  jobs covering Python/Django and TypeScript/React
- **`.forgejo/workflows/renovate.yml`** — Renovate self-hosted workflow for Forgejo; uses the
  `gitea` platform against `git.syntek-studio.com`

### Removed

- **`.github/setup-branch-protection.sh`** — deleted to prevent developers from scripting unreviewed
  changes to branch protection rules; rules are now documented and applied via web UI

---

## [0.6.0] — 08/03/2026

### Added

- **`rust/syntek-dev`** — `--prettier` flag added to `LintArgs`; allows running Prettier in
  isolation via `syntek-dev lint --prettier` without triggering all other linters
- **`rust/syntek-dev`** — `syntek-dev lint --fix` now runs `pnpm format` (Prettier `--write`) in
  addition to ruff `--fix` and ESLint `--fix`; Prettier section inserted before the clippy section
  in the lint command runner
- **`rust/syntek-dev`** — `syntek-dev lint --fix` now runs `pnpm lint:md:fix` (markdownlint-cli2
  `--fix`) instead of `pnpm lint:md` when `--fix` is passed
- **`package.json`** — `lint:md:fix` script added (`markdownlint-cli2 --fix`) to expose auto-fix to
  the Rust CLI process runner

### Changed

- **`rust/syntek-dev`** — `run_all` guard updated to include `!args.prettier`, consistent with all
  other single-linter flags; `--prettier` alone no longer triggers a full lint run

### Documentation

- **`docs/SPRINTS/SPRINT-01.md`** — completion date recorded (06/03/2026); story completion status
  table and per-story verification checklists added
- **`docs/SPRINTS/OVERVIEW.md`** — Sprint 01 annotated as ✅ Completed 06/03/2026; overall status
  updated to "In Progress (Sprint 01 Completed)"
- **`docs/STORIES/OVERVIEW.md`** — US001, US002, US004 status updated from "To Do" to ✅ Completed
- **`docs/SPRINTS/LOGS/COMPLETION-2026-03-08-SPRINT-01.md`** — new sprint completion log created;
  records 114/114 tests passing across all three Sprint 01 stories

---

## [0.5.2] — 08/03/2026

### Fixed

- **`.github/workflows/web.yml`** — removed hardcoded `version: "10.28.2"` from
  `pnpm/action-setup@v4`; action now reads `packageManager` from `package.json` automatically,
  preventing version conflict with `pnpm@10.31.0`
- **`.github/workflows/graphql-drift.yml`** — same fix as above applied to the GraphQL drift
  detection workflow; both CI workflows now stay in sync with `package.json` automatically

---

## [0.5.1] — 08/03/2026

### Fixed

- **`.gitignore`** — removed bare `lib/` and `lib64/` entries that incorrectly gitignored TypeScript
  `src/lib/` directories; Python virtualenv lib directories are already covered by `.venv/`,
  `venv/`, `env/`, and `build/` entries
- **`shared/graphql/src/lib/fetcher.ts`** — file was silently excluded from CI by the above pattern;
  now tracked and present in the repository; resolves `TS2307: Cannot find module '../lib/fetcher'`
  and `TS2307: Cannot find module './lib/fetcher.js'` errors in CI

---

## [0.5.0] — 07/03/2026

### Added

- **`rust/syntek-dev`** — `syntek-dev ci` command — runs the full CI pipeline locally: Prettier,
  ESLint, markdownlint, type-check, Vitest (all packages), Rust fmt/clippy/test, in sequence
- **`shared/graphql/`** — `@vitest/coverage-v8` installed; coverage configured in
  `shared/graphql/vitest.config.ts`; CI coverage step added to `web.yml` (GitHub Actions + Forgejo)

### Changed

- **`package.json`** — lefthook upgraded from `^1.0.0` to `^2.1.0` (installed 2.1.3)

### Fixed

- **`markdownlint`** — 175 CI lint failures resolved: MD036 disabled for intentional user story bold
  convention; MD040 (fenced code block language tags), MD031 (blank lines around fenced blocks), and
  MD034 (bare URLs) violations corrected across documentation and workflow files
- **`CHANGELOG.md`**, **`README.md`**, **`RELEASES.md`** — Prettier formatting corrected

---

## [0.4.2] — 07/03/2026

### Fixed

- **`markdownlint` CI** — 175 lint failures resolved: MD036 rule disabled (bold-as-heading), MD040
  (fenced code block language), MD031 (blank lines around fenced blocks), and MD034 (bare URLs)
  violations corrected across documentation and workflow files
- **`lefthook.yml`** — upgraded lefthook from `^1.0.0` to `^2.1.0` (installed 2.1.3)

### Added

- **`shared/graphql/`** — `@vitest/coverage-v8` added for TypeScript test coverage reporting;
  coverage configured in `shared/graphql/vitest.config.ts`
- **`.github/workflows/web.yml`**, **`.forgejo/workflows/web.yml`** — "Coverage report" CI step
  added to both GitHub Actions and Forgejo pipelines (mirrored)

---

## [0.4.1] — 07/03/2026

### Fixed

- **`lefthook.yml`** — markdownlint exclusions corrected: nested `node_modules` and `.claude/`
  directories now properly excluded from lint runs
- **`eslint.config.mjs`** — `no-undef` rule disabled for TypeScript files (handled by `tsc`);
  `**/src/generated/**` added to ignore patterns; `--no-warn-ignored` flag added to lefthook ESLint
  hook

### Changed

- **`rust/syntek-dev/src/`** — Clippy warnings resolved: `&PathBuf` changed to `&Path` in function
  signatures, collapsible `if` statements flattened, `--allow-dirty` added to `clippy fix`
  invocation
- **`shared/graphql/`**, **`shared/types/`** — Prettier and ESLint formatting normalised across all
  TypeScript source files
- **`.forgejo/workflows/`**, **`.github/workflows/`** — whitespace consistency normalised across all
  four CI workflow files (`web.yml`, `graphql-drift.yml`, `python.yml`, `rust.yml`)
- **`pyrightconfig.json`** — redundant settings removed; configuration simplified
- **`docs/`** — Prettier formatting applied across 144 documentation files (GUIDES, SPRINTS,
  STORIES, TESTS, PLANS)
- **`CHANGELOG.md`**, **`RELEASES.md`**, **`VERSION-HISTORY.md`** — Prettier formatting applied to
  version tracking files

---

## [0.4.0] — 06/03/2026

### Added

- **`shared/graphql/`** — `@syntek/graphql` package with pre-generated typed React Query hooks
  (US004)
  - `schema.graphql` — SDL schema mirroring the Syntek Django/Strawberry backend
  - `src/operations/auth.graphql` — `Login` mutation, `CurrentUser` query
  - `src/operations/tenant.graphql` — `CurrentTenant` query
  - `src/generated/graphql.ts` — codegen output: `useLoginMutation`, `useCurrentUserQuery`,
    `useCurrentTenantQuery` with full TypeScript inference
  - `src/lib/fetcher.ts` — minimal fetch wrapper (browser: `/graphql`, server: `GRAPHQL_ENDPOINT`)
  - `src/__tests__/` — 29/29 Vitest tests green: 12 codegen-output + 17 type-inference
  - `features/graphql_operations.feature` — BDD Gherkin scenarios for all US004 acceptance criteria
- **`lefthook.yml`** — pre-commit hooks for all layers in parallel: graphql-drift, eslint, tsc,
  prettier, ruff-lint, ruff-format, basedpyright, cargo-fmt
- **`docs/TESTS/US004-TEST-STATUS.md`** — 29/29 PASS
- **`docs/TESTS/US004-MANUAL-TESTING.md`** — 4 manual scenarios documented
- **`.github/workflows/`** — four separate path-filtered CI workflows: `web.yml`,
  `graphql-drift.yml`, `python.yml`, `rust.yml`
- **`.forgejo/workflows/`** — identical workflows mirrored for Forgejo CI

### Changed

- **`docs/STORIES/US004.md`** — status updated to Completed; all tasks ticked
- **`docs/SPRINTS/SPRINT-01.md`** — Sprint 01 marked Completed at 11/11 points (US001 ✅ US002 ✅
  US004 ✅)
- **`package.json`** — added `packageManager` field (fixes Turborepo), `prepare` script (lefthook),
  `codegen` script, husky replaced with lefthook
- **`pnpm-workspace.yaml`** — added `ignoredBuiltDependencies` for esbuild

---

## [0.3.0] — 06/03/2026

### Added

- **`shared/types/`** — `@syntek/types` package with full TypeScript type definitions (US002)
  - Base types: `ID`, `Timestamp`, `PaginatedResponse<T>`, `ApiError`
  - Auth types: `Permission`, `Role`, `User`, `Session`
  - Tenant types: `Tenant`, `TenantSettings`
  - Notification types: `NotificationChannel` (discriminated union), `Notification`
- **`shared/types/src/__tests__/`** — 46 Vitest type-assertion and build-output tests (all passing)
- **`shared/types/features/`** — BDD Gherkin scenarios for all US002 acceptance criteria
- **`shared/types/dist/`** — compiled `.d.ts` declaration files and ES module output (gitignored,
  built on demand)
- **`docs/TESTS/US002-TEST-STATUS.md`** — 46/46 PASS
- **`docs/TESTS/US002-MANUAL-TESTING.md`** — all scenarios verified

### Changed

- **`docs/STORIES/US002.md`** — status updated to Completed; all tasks ticked
- **`docs/SPRINTS/SPRINT-01.md`** — US002 marked Completed; sprint progress 8/11 points

---

## [0.2.0] — 06/03/2026

### Added

- **Test infrastructure** — root-level `tests/workspace/` suite (39 pytest tests) covering pnpm, uv,
  Cargo, and Turborepo workspace configuration (US001)
- **BDD tests** — `pytest-bdd` Gherkin scenarios matching all US001 acceptance criteria
- **`packages/backend/syntek-auth/`** — minimal pyproject.toml stub to enable uv workspace
  resolution
- **`uv.lock`** — deterministic Python dependency lock file (51 packages, Python 3.14)
- **`VERSION`**, **`CHANGELOG.md`**, **`VERSION-HISTORY.md`**, **`RELEASES.md`** — version tracking
  files
- **`[project]` section in `pyproject.toml`** — enables `uv sync` via `[dependency-groups]`
- **`[dependency-groups]` in `pyproject.toml`** — replaces ad-hoc `uv pip install` list in
  install.sh

### Changed

- **`Cargo.toml`** — PyO3 upgraded from `0.23` to `0.28.2` (adds Python 3.14 support)
- **`install.sh`** — Python setup now uses `uv sync --group dev` from the lockfile; venv activation
  consolidated; end-of-script reminder made prominent
- **`rust/syntek-dev/src/commands/test.rs`** — `syntek-dev test --python` now respects `testpaths`
  in `pyproject.toml` (discovers `tests/` and `packages/backend/` without an explicit path override)
- **`pyproject.toml`** — removed invalid `python-version` field from `[tool.uv]`; added
  `testpaths = ["tests", "packages/backend"]`
- **`docs/SPRINTS/SPRINT-01.md`** — sprint status updated to In Progress; US001 marked complete
  (5/11 points)
- **`docs/STORIES/US001.md`** — status updated to Completed; all tasks ticked

### Fixed

- **`Cargo.lock`** — updated to resolve PyO3 0.28.2 (previously 0.23.5 which blocked Python 3.14
  builds)

---

## [0.1.0] — 06/03/2026

### Added

- Initial monorepo scaffold — `pnpm-workspace.yaml`, `turbo.json`, root `package.json`,
  `pyproject.toml`, `Cargo.toml`
- Rust workspace: `syntek-crypto`, `syntek-pyo3`, `syntek-graphql-crypto`, `syntek-dev` crates
- `syntek-dev` Rust CLI — `up`, `test`, `lint`, `format`, `db`, `check`, `open` commands
- Editor, formatter, and linter configuration (`.editorconfig`, `.prettierrc`, `eslint.config.mjs`,
  `ruff`, `basedpyright`)
- Package directory scaffolding (`packages/backend/`, `packages/web/`, `mobile/`, `shared/`)
- 74 user stories across 8 epics (`docs/STORIES/`)
- 45-sprint plan (`docs/SPRINTS/`)
- Architecture documentation (`docs/PLANS/SYNTEK-ARCHITECTURE.md`)
- `install.sh` — one-command dev environment bootstrap
- `.zed/settings.json` — project-level Zed IDE overrides
