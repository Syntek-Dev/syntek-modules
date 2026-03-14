# QA Report: US009 — `syntek-auth` Authentication Module

**Date:** 11/03/2026 — **Updated:** 14/03/2026 **Analyst:** QA Agent (The Breaker) **Branch:**
`us009/syntek-auth` **Status:** CRITICAL ISSUES FOUND

---

## Revision Notes (13/03/2026)

Significant implementation work has been added since the original QA review. The model layer,
services, and mutations have been substantially expanded. Key changes:

**Issues resolved since last review:**

- ~~Issue 12~~ — `email` field no longer carries `unique=True` or `db_index=True`. Uniqueness is now
  correctly enforced via companion `email_token`, `phone_token`, and `username_token` columns
  (HMAC-SHA256 of the normalised plaintext).

**Issues partially addressed:**

- Issue 3 (EncryptedField stub) — `EncryptedField.pre_save` now handles `None` values and delegates
  validation to `syntek_pyo3` when available. The deployment trap (plaintext stored when
  `syntek_pyo3` is absent) remains.

**New issues added:**

- NEW-C1 — Python 2 `except` syntax in `oauth_mfa.py` causes `SyntaxError` on import (critical).
- NEW-C2 — `_verify_mfa_proof` email_otp path calls `verify_email_token` without user binding (IDOR
  — any user's valid OTP satisfies another user's MFA challenge).
- NEW-C3 — `oidcCallback` accepts `provider_id` from client without verifying against the stored
  session provider ID (allows provider substitution to bypass MFA gating).
- NEW-C4 — `_SIGNING_SECRET` is ephemeral (generated at process startup with `secrets.token_bytes`)
  — tokens are invalidated on every restart and cannot be validated across workers in a
  multi-process deployment (critical correctness failure).
- NEW-H1 — No MFA retry limit in `complete_oauth_mfa` — unlimited brute force of pending OTPs.
- NEW-H2 — `make_jti_token` requires `FIELD_HMAC_KEY` at runtime; missing key raises
  `ImproperlyConfigured` mid-request during token rotation.
- NEW-H3 — `SyntekUserManager.create_user` uses a single `FIELD_KEY` for all PII fields — per-field
  key isolation violated.
- NEW-H4 — `_get_or_create_oidc_user` silently falls through `oidc_sub_hash` lookup (field does not
  exist on model); cross-provider account collision via email is unguarded.
- NEW-O1 — HS256 (symmetric) is the wrong algorithm choice for a distributed system. ES256
  (asymmetric ECDSA/P-256) should replace it: eliminates the shared-secret problem, enables a JWKS
  endpoint, is consistent with the RS256/ES256 the OIDC client already accepts, and produces smaller
  tokens than RS256. Recorded as an architectural observation pending design decision.

---

## Summary

The `syntek-auth` module has solid structural foundations — settings validation, lockout logic, MFA
gating, companion token columns for encrypted field uniqueness, and the allowlist are all
well-designed for this stage. However, the expanded OAuth MFA flow introduces multiple new critical
issues including a Python syntax error that prevents import, a cross-user MFA bypass (IDOR), and a
provider-substitution attack vector in `oidcCallback`. The token signing architecture has two
critical flaws: an ephemeral per-process signing key (breaks multi-worker deployments entirely) and
a symmetric HS256 design that should migrate to asymmetric ES256 before the green phase. Earlier
critical issues (progressive lockout overflow, in-process revocation store) remain unresolved.
Fifteen original issues plus nine new issues are identified.

---

## CRITICAL (Blocks deployment)

### 1. HS256 Token Signing — Algorithm Confusion and Weak-Secret Attack Surface

**Location:** `src/syntek_auth/services/tokens.py:27, 85, 126`

The JWT implementation uses HS256 (HMAC-SHA256) with a module-level secret generated at process
start (`_SIGNING_SECRET: bytes = secrets.token_bytes(32)`). The header is hard-coded to
`{"alg": "HS256", "typ": "JWT"}` during signing, but `_decode_jwt` never reads or validates the
`alg` field from the incoming token header before computing the expected HMAC. This creates two
distinct attack surfaces:

- **Algorithm confusion / `alg: none` attack:** A crafted token with `{"alg": "none", "typ": "JWT"}`
  and an empty signature part (`"header.payload."`) passes the `hmac.compare_digest` check only if
  the HMAC of `header.payload` with the secret happens to produce an empty byte string — which it
  never does. However, a custom client could forge a token by submitting `"header.payload."` with a
  trailing dot; the three-part split succeeds and `sig_b64` is an empty string. The
  `hmac.compare_digest` then compares the expected 44-character base64 signature against `""` which
  correctly fails. This specific `alg: none` path is blocked by the HMAC comparison, **but only
  incidentally** — there is no explicit header validation that would catch future refactors that
  weaken this check.
- **Missing header validation is a latent critical:** Any green-phase change that adjusts how the
  signature is assembled (e.g. accepting RS256 for OIDC token compatibility) without adding header
  validation would immediately open `alg: none` or algorithm-switching attacks. The absence of
  explicit `alg` header verification is a design-level flaw that must be corrected before the green
  phase adds new signing modes.

**Impact:** If the green phase introduces RS256 alongside HS256 (required for OIDC — see US009
tasks), an attacker could submit an RS256 token with the server's public key as the HS256 secret to
forge arbitrary payloads.

**Reproduce:** Issue a token, decode the header, change `alg` to a different value, recompute
signature using HS256 with the known secret. Submit. Current code rejects this because the HMAC
mismatch still fires — but add an RS256 path and it breaks.

**Recommended fix direction:** Two separate actions are required.

Immediate: `_decode_jwt` must decode the incoming token header, extract the `alg` field, and assert
it is exactly `"HS256"` before computing the HMAC. Reject any token whose header specifies a
different algorithm with a constant-time path to avoid timing oracle leaks.

Architectural (before green phase sign-off): Migrate from HS256 to **ES256** (ECDSA/P-256). HS256 is
symmetric — any process that can verify tokens can also forge them, the secret must be shared across
all workers, and no JWKS endpoint is possible. ES256 eliminates all three problems: the private key
signs, a derivable public key verifies, resource services never see the private key, and a
`/.well-known/jwks.json` endpoint becomes possible for downstream consumers. ES256 is already
supported on the inbound side (the OIDC client accepts RS256 and ES256), produces smaller tokens
than RS256, and is the correct choice for any system that may eventually expose token validation to
external parties. Migration requires replacing the hand-rolled `_make_jwt` / `_decode_jwt` with
`PyJWT` + `cryptography`, loading the private key from `SYNTEK_AUTH['JWT_SIGNING_KEY']` (PEM, from
env), and exposing the public key via `SYNTEK_AUTH['JWT_PUBLIC_KEY']`. The hand-rolled
implementation is acceptable for HS256 but must not be extended to handle asymmetric algorithms
without a dedicated JWT library, as algorithm confusion is trivially exploitable in custom
implementations.

---

### 2. In-Process Revocation Store — Not Shared Across Workers, Not Persisted

**Location:** `src/syntek_auth/services/tokens.py:33, 238-242`

`_REVOKED_TOKENS: dict[str, bool] = {}` is a plain module-level Python dict. This means:

- In a multi-worker deployment (Gunicorn, uWSGI, Daphne with multiple processes) each worker
  maintains its own independent revocation set. A refresh token revoked by worker A is invisible to
  worker B. An attacker can replay a revoked refresh token by routing subsequent requests to a
  different worker.
- On any process restart (deploy, crash, OOM kill) the entire revocation store is wiped. All
  previously revoked refresh tokens become valid again until their `exp` claim expires, which could
  be up to seven days later.
- The dict is also not protected by any lock. Under Python's GIL, dict operations are generally safe
  for single reads/writes, but concurrent `rotate_refresh_token` calls for the same `jti` could
  result in a TOCTOU window where the revocation write and the reuse check race.

The docstring acknowledges the limitation ("Production deployments should replace the revocation
store with a shared cache") but this warning exists only in source comments and is not surfaced as a
startup warning or enforced configuration check.

**Impact:** Refresh token reuse is silently permitted in any multi-process or restarted deployment,
completely undermining the rotation security guarantee. An attacker with a stolen refresh token can
replay it indefinitely after a server restart.

**Reproduce:** Rotate a refresh token to revoke it. Restart the Django process. Attempt to rotate
the original token again. It succeeds.

**Recommended fix direction:** The revocation store must be Valkey/Redis-backed from the outset. The
in-process dict must not be used in any environment where more than one process runs. A startup
check in `AppConfig.ready()` should warn (or optionally raise) when the revocation backend is not
configured. The US009 task list references `syntek-cache` (Redis/Valkey) — this must be wired up
before the green phase sign-off, not deferred.

---

### 3. `EncryptedField` Is a Plain `TextField` Stub — No Encryption on Any Write

**Location:** `src/syntek_auth/models/user.py:35-42, 153-165`

`EncryptedField` is declared as a direct subclass of `models.TextField` with zero additional
behaviour. All PII fields (`email`, `phone`) declared with `EncryptedField` on `AbstractSyntekUser`
will be written to and read from the database as **plain text** until the real implementation is
wired up from `syntek-pyo3`.

This is an expected red-phase condition, but the danger is that it creates a significant deployment
trap:

- If any consuming project installs this package and runs `migrate` before the green phase delivers
  the real `EncryptedField`, all user PII will be stored in plain text. There is no enforcement
  mechanism preventing this.
- The placeholder class name (`EncryptedField`) and its docstring imply encryption is active, which
  could mislead consumers into believing the field protects data when it does not.
- Migrations generated against the stub will use `TextField` as the column type. When the real
  `EncryptedField` is introduced, all existing rows will contain unencrypted data with no migration
  path to encrypt them retroactively.

**Impact:** GDPR Article 32 violation, UK DPA 2018 breach, total loss of the zero-plaintext
guarantee for any deployment during the red phase.

**Reproduce:** Configure `AUTH_USER_MODEL = 'syntek_auth.User'`, run `migrate`, create a user. Query
the database directly — `email` is stored as plain text.

**Recommended fix direction:** The stub must be clearly gated. Consider raising
`ImproperlyConfigured` in `EncryptedField.__init__` unless a specific internal bypass flag is set,
to prevent accidental deployment. Alternatively, the green phase must be the first published version
of this package — the stub must never be published to the Forgejo registry.

---

### 4. JWT `exp` Claim — No `nbf` / Future-Issued Token Handling

**Location:** `src/syntek_auth/services/tokens.py:140-143`

`_decode_jwt` checks `if exp is not None and time.time() > exp` but does not validate:

- `nbf` (not-before) claim — a token can carry an `nbf` far in the future and still be accepted.
- `iat` (issued-at) drift — a token with `iat` in the future is not rejected, meaning a stolen
  signing key can produce tokens backdated to extend their validity window silently.

More critically, the expiry check uses `time.time()` (wall clock) with no clock-skew tolerance and
no leeway. In distributed deployments where servers have slight clock differences, a valid token
could be rejected milliseconds before its actual expiry.

**Impact:** Tokens with manipulated `iat` or missing `nbf` pass validation. In a key-compromise
scenario, an attacker can issue tokens with future `iat` values to extend their effective lifetime
beyond what the server would issue.

**Recommended fix direction:** Validate `iat` is not in the future (with a small tolerance, e.g. 30
seconds). Add a configurable clock-skew leeway (default 30 seconds) to the expiry check. Reject
tokens where `typ` is not the expected value (`"access"` for `validate_access_token`).

---

### 5. `validate_access_token` Does Not Check the `typ` Claim

**Location:** `src/syntek_auth/services/tokens.py:251-272`

`validate_access_token` calls `_decode_jwt` and returns the payload. It does not assert that
`payload["typ"] == "access"`. This means a valid **refresh token** can be submitted to any endpoint
that calls `validate_access_token` and it will pass validation. The refresh token has a much longer
lifetime (seven days), so an attacker who obtains a refresh token (e.g. from a cookie or log) can
use it as an access token for the full seven-day period.

Similarly, `rotate_refresh_token` does not assert that `payload["typ"] == "refresh"` before
accepting the token, meaning an access token could be submitted to the rotation endpoint.

**Impact:** A fifteen-minute access token lifetime provides no security if any refresh token (valid
for seven days) can be presented as an access token.

**Reproduce:** Call `issue_token_pair`. Take the `refresh_token` value. Pass it directly to
`validate_access_token`. It returns a valid payload with no error.

**Recommended fix direction:** `validate_access_token` must assert `payload.get("typ") == "access"`.
`rotate_refresh_token` must assert `payload.get("typ") == "refresh"`. Both should raise `ValueError`
on mismatch with a message that does not reveal which type was provided.

---

### 6. Progressive Lockout — Integer Overflow for Large `lockout_count`

**Location:** `src/syntek_auth/services/lockout.py:62`

`return base_duration * (2 ** (lockout_count - 1))`

Python integers are arbitrary precision and will not overflow, but the resulting value can become
astronomically large. With a default `LOCKOUT_DURATION` of 900 seconds and `lockout_count` of 64,
the computed duration is `900 * 2^63 = 8,294,967,296,000,000,000,000` seconds — far beyond any
meaningful timeout and potentially exceeding the maximum value that Redis/Valkey can store as a TTL
(which is a 64-bit integer in seconds, maximum ~292 years). Setting a TTL of this magnitude in Redis
would either be rejected or silently clamped, causing the lockout to either fail to be applied or to
be permanent.

No upper bound is applied to the computed duration. The `should_lock_account` function correctly
identifies overflow risk in lockout counts, but there is no guard in `compute_lockout_duration`.

**Impact:** After 64+ lockout cycles, the computed duration exceeds Redis TTL limits, potentially
causing the lockout to be permanent (account effectively destroyed) or to fail silently (account
immediately unlocked). Additionally, the acceptance criterion states "duration doubles" but sets no
ceiling — a legitimate user locked out many times could be locked out for centuries.

**Reproduce:** Call
`compute_lockout_duration(base_duration=900, lockout_count=100, strategy="progressive")`. The result
is a number larger than `2^96`. No test covers this.

**Recommended fix direction:** Apply a maximum cap to the computed duration (e.g. capped at
`LOCKOUT_DURATION * 2^10` or a configurable `LOCKOUT_MAX_DURATION` setting). The cap should be
validated in `validate_settings`.

---

### NEW-C1 — Python 2 `except` syntax in `oauth_mfa.py` causes `SyntaxError` on import

**Location:** `src/syntek_auth/services/oauth_mfa.py:281`

**Description:**

```python
except ValueError, AttributeError:
```

This is Python 2 syntax. Python 3 (3.14.3 is in use) requires
`except (ValueError, AttributeError):`. This is a `SyntaxError` that prevents the entire `oauth_mfa`
module from being imported. Any import of `syntek_auth.services.oauth_mfa` — including the deferred
import inside `mutations/oidc.py` at resolver execution time — raises `SyntaxError`. The entire
`completeSocialMfa` mutation and the `oidcCallback` MFA-gating flow are non-functional.

**Reproduce:** `from syntek_auth.services.oauth_mfa import complete_oauth_mfa` — raises
`SyntaxError: invalid syntax`.

**Recommended fix direction:** Replace `except ValueError, AttributeError:` with
`except (ValueError, AttributeError):`.

---

### NEW-C2 — `_verify_mfa_proof` email_otp path has no user binding — IDOR

**Location:** `src/syntek_auth/services/oauth_mfa.py:161–165`

**Description:**

```python
if mfa_method == "email_otp":
    from syntek_auth.services.email_verification import verify_email_token
    result = verify_email_token(token=mfa_proof)
    return result.success
```

`verify_email_token` is called with only `token=mfa_proof` — `user_id` is not passed. If the email
verification service validates the token without scoping to the calling user, any valid email OTP
token belonging to _any user in the system_ satisfies the MFA challenge for the
`PendingOAuthSession`.

**Attack Scenario:**

1. Attacker has a valid (unexpired) email verification token from their own registration flow.
2. Attacker calls `completeSocialMfa` for victim's `pending_token`.
3. `verify_email_token(token=attacker_token)` returns `success=True`.
4. Victim's `PendingOAuthSession` is consumed and a full `TokenPair` is issued to the attacker.

**Impact:** Complete account takeover for any user with an active `PendingOAuthSession`.

**Reproduce:** Obtain a valid email OTP for attacker's account. Call `completeSocialMfa` with
victim's `pending_token` and `mfa_method="email_otp"`. If `verify_email_token` is not user-scoped,
it returns `success=True`.

**Recommended fix direction:** `verify_email_token` must accept and require a `user_id` parameter,
validating the token belongs to that user. The call at line 164 must pass `user_id=user_id`.

---

### NEW-C3 — `oidcCallback` accepts `provider_id` from client without verifying against session

**Location:** `src/syntek_auth/mutations/oidc.py:157–210`

**Description:** `oidc_auth_url` stores `oidc_provider_id` in the session (line 86). `oidc_callback`
never retrieves it or validates that `input.provider_id` matches the session-stored value. The
`state` parameter is correctly validated in constant time, but `input.provider_id` is accepted as-is
from the client request.

An attacker who initiates a Google auth flow (Google is in `MFA_GATED_PROVIDERS`) but substitutes
`provider_id="github"` in the callback can bypass the MFA gating: `is_mfa_gated_provider("github")`
returns `False`, and a full `TokenPair` is issued directly instead of creating a
`PendingOAuthSession`.

**Impact:** The entire `MFA_GATED_PROVIDERS` enforcement in `oidcCallback` is defeatable by
provider_id substitution on the inbound callback request.

**Recommended fix direction:** Retrieve `session.get("oidc_provider_id")` in `oidc_callback` and
assert `input.provider_id == stored_provider_id` using `_constant_time_eq` before any discovery or
token exchange.

---

### NEW-C4 — `_SIGNING_SECRET` Is Ephemeral — Tokens Invalidated on Every Restart, Broken Across Workers

**Location:** `src/syntek_auth/services/tokens.py:29`

```python
_SIGNING_SECRET: bytes = secrets.token_bytes(32)
```

This secret is generated once at module import time and stored in a module-level variable. It is
never read from configuration, never persisted, and differs between processes. This creates two
distinct production failures:

**Process-restart invalidation:** Every time the Django process restarts (deploy, crash, OOM kill,
`gunicorn --reload`), a new `_SIGNING_SECRET` is generated. All previously issued access and refresh
tokens are immediately invalid because they were signed with the old secret. Every logged-in user is
silently logged out on the next request with no warning. The 7-day refresh token lifetime becomes
meaningless — effective token lifetime is bounded by process uptime.

**Multi-worker signing incompatibility:** Gunicorn runs multiple worker processes (typically 4–8).
Each worker imports `tokens.py` independently and generates its own random `_SIGNING_SECRET`. A
token signed by worker 1 carries a signature computed with worker 1's secret. When worker 2 receives
a subsequent request from the same client, it computes the expected HMAC with its own different
secret, the `hmac.compare_digest` check fails, and the request is rejected with 401. This is not a
timing-dependent race — it is a deterministic failure for every request handled by a different
worker than the one that issued the token. In a standard Gunicorn deployment, this effectively means
~75% of authenticated requests fail after the initial token issuance.

The docstring at line 9 acknowledges that `_REVOKED_TOKENS` needs to be replaced with a shared cache
for multi-process use, but does not mention the signing secret issue at all — the more severe of the
two problems.

**Impact:** Functionally breaks authentication in any standard production deployment. Not a subtle
timing issue or edge case — any multi-worker or restarted process fails to validate tokens
deterministically.

**Reproduce:**

1. Start two Django processes with distinct `_SIGNING_SECRET` values (simulate two Gunicorn workers
   by importing `tokens` in two separate Python sessions).
2. Call `issue_token_pair` in process 1 to obtain an access token.
3. Call `validate_access_token` with that token in process 2. Raises
   `ValueError: JWT signature verification failed`.

**Recommended fix direction:** Load the signing secret from `SYNTEK_AUTH['JWT_SIGNING_SECRET']`
(bytes or hex string, minimum 32 bytes, from env var). Validate this key is present and correctly
sized in `AppConfig.ready()` — raise `ImproperlyConfigured` at startup if absent. Remove the
module-level `secrets.token_bytes(32)` fallback entirely; there must be no code path that allows a
randomly generated per-process secret in any environment. When the architectural migration to ES256
described in Issue 1 is completed, this key becomes the private key PEM — the startup validation
must be updated accordingly.

---

## HIGH (Must fix before green phase sign-off)

### 7. `SYNTEK_AUTH` Entirely Absent — No Defaults, No Validation

**Location:** `src/syntek_auth/apps.py:42-43`

```python
if syntek_auth_settings:
    validate_settings(syntek_auth_settings)
```

When `SYNTEK_AUTH` is not present in Django settings at all, `syntek_auth_settings` is an empty dict
`{}`, which is falsy. `validate_settings` is never called, and all defaults fall back to whatever
the implementation assumes. The module silently operates with no validated configuration.

This is particularly dangerous because a consumer who forgets to add `SYNTEK_AUTH` to their
`settings.py` gets no error — the module starts silently with unchecked defaults (e.g. no MFA
required, no password expiry, plaintext EncryptedField).

**Impact:** A consumer project that installs `syntek-auth` without configuring `SYNTEK_AUTH` would
deploy with all security controls at their weakest defaults, with no startup warning.

**Recommended fix direction:** If `SYNTEK_AUTH` is missing from settings entirely, the module should
either raise `ImproperlyConfigured` (secure-by-default) or apply documented safe defaults and log a
startup warning. The current silent pass is dangerous. The acceptance criteria state "all required
keys are validated" — this implies the key must be present.

---

### 8. Settings Key Name Mismatch — `OIDC_PROVIDERS` vs `OAUTH_PROVIDERS`

**Location:** `src/syntek_auth/backends/allowlist.py:87`, `src/syntek_auth/conf.py` (absent),
`docs/STORIES/US009.md:72`

The US009 configuration contract (story doc and `validate_settings` test helper) uses the key name
`OIDC_PROVIDERS`. The allowlist validator (`validate_oauth_providers`) reads from `OAUTH_PROVIDERS`.
These are different keys.

A consumer who configures `OIDC_PROVIDERS` as documented will have their provider list silently
ignored by the allowlist check (which reads `OAUTH_PROVIDERS` and finds nothing), meaning blocked
providers like Google would pass startup validation without error.

**Impact:** The security enforcement of the allowlist (US076) is bypassed entirely for any consumer
who follows the documented configuration contract.

**Reproduce:** Configure `SYNTEK_AUTH = {'OIDC_PROVIDERS': [{'provider': 'google'}]}`. Run
`app_config.ready()`. No `ImproperlyConfigured` is raised. Google is silently permitted.

**Recommended fix direction:** Standardise on one key name. `OIDC_PROVIDERS` is used in the story
doc and matches the OIDC nomenclature. The allowlist validator must read from the same key. The
existing allowlist tests use the `OAUTH_PROVIDERS` key — these tests and the validator must be
reconciled.

---

<!-- markdownlint-disable MD013 -->

### 9. `resolve_session_state` — MFA_REQUIRED=True With MFA Configured Issues Full Session Without Verifying MFA Was Actually Completed

<!-- markdownlint-enable MD013 -->

**Location:** `src/syntek_auth/services/mfa.py:90-91`

```python
if user_has_mfa_configured:
    return MfaSessionState(full_session=True, mfa_setup_required=False)
```

`resolve_session_state` takes a boolean `user_has_mfa_configured` — meaning a user who has MFA set
up but has **not yet completed the MFA challenge in the current login flow** would receive
`full_session=True` if the caller passes `True` for `user_has_mfa_configured` before the challenge
is verified.

The function signature conflates "has MFA enrolled" with "has passed MFA for this session". In the
green-phase login flow, the caller must distinguish between these two states and must not issue a
full session until the challenge response has been verified. The current API makes it trivially easy
for the caller to get this wrong.

**Impact:** If the green-phase login mutation calls
`resolve_session_state(user_has_mfa_configured=True, mfa_required=True)` immediately after password
verification (before TOTP/passkey challenge), it issues a full session to an unauthenticated-MFA
user.

**Recommended fix direction:** The function parameter should be renamed to `mfa_challenge_completed`
or the function should accept separate `enrolled` and `challenge_completed` booleans. The acceptance
criterion says "a partial session with `mfa_setup_required: true` is issued" for users without MFA —
the session state for "has MFA enrolled but not yet completed the challenge" is entirely absent from
the current design.

---

### 10. `check_password_history` — Uses Django's Default Hasher, Not Argon2id

**Location:** `src/syntek_auth/services/password.py:176`

`check_password_history` delegates to `django.contrib.auth.hashers.check_password`. The red-phase
test fixture (`test_us009_password_policy.py:218-220`) uses PBKDF2-SHA256 hashes, which is Django's
default hasher. The module is supposed to replace Django's password hasher with Argon2id via
`syntek-pyo3`, but `check_password_history` will use whichever hasher Django has configured.

If the green phase correctly configures Argon2id as the primary hasher, existing history hashes
stored as PBKDF2 would need `check_password` to support the legacy hasher — Django does support this
transparently via its hasher list, but only if PBKDF2 remains in `PASSWORD_HASHERS`. If it is
removed (which a hardened deployment might do), old history hashes become unverifiable and
`check_password_history` would silently return `False` for all of them, disabling the history check.

**Impact:** Password history enforcement silently fails when hasher migration removes PBKDF2 from
the hasher list.

**Recommended fix direction:** Password history hashes must always be stored and verified using the
same algorithm (Argon2id via `syntek-pyo3`). The history check should use `verify_password` from
`syntek-pyo3` directly, not Django's generic `check_password`. The test fixtures should use Argon2id
test hashes, not PBKDF2.

---

### 11. `USERNAME_FIELD` Hardcoded to `"email"` — Not Overridden by `LOGIN_FIELD` Setting

**Location:** `src/syntek_auth/models/user.py:180`

The docstring states: "`USERNAME_FIELD` defaults to `"email"` and may be overridden at runtime via
the `LOGIN_FIELD` setting." However, `AbstractSyntekUser.USERNAME_FIELD = "email"` is a class
attribute set at definition time. There is no mechanism in the current code to override it from
settings.

Django's `AbstractBaseUser.USERNAME_FIELD` must point to the field used for authentication lookup.
If `LOGIN_FIELD` is `'username'` or `'phone'`, `USERNAME_FIELD` should match. Django itself reads
`USERNAME_FIELD` in admin, createsuperuser, and other places. A mismatch between `USERNAME_FIELD`
and the actual login field will cause admin login to use the wrong field.

**Impact:** When `LOGIN_FIELD='username'`, the Django admin and `createsuperuser` management command
will attempt to authenticate against `email`, not `username`, breaking the entire admin interface
for username-mode deployments.

**Recommended fix direction:** `USERNAME_FIELD` must be dynamically derived from `LOGIN_FIELD` at
startup. Since class attributes cannot be set from runtime config in a clean way, the correct
approach is to document that `USERNAME_FIELD` is always `"email"` on the model and the `LOGIN_FIELD`
setting governs only the `resolve_login_field` dispatcher — not the model's `USERNAME_FIELD`.
Alternatively, provide concrete subclasses for each `LOGIN_FIELD` mode. The current docstring is
misleading and must be corrected regardless.

---

### ~~12. `email` Field Declared With `unique=True` and `db_index=True` on an `EncryptedField`~~

**RESOLVED (13/03/2026)**

The `email`, `phone`, and `username` fields on `AbstractSyntekUser` no longer carry `unique=True` or
`db_index=True`. Uniqueness is now correctly enforced via companion `email_token`, `phone_token`,
and `username_token` columns (HMAC-SHA256 of the normalised plaintext, computed by
`SyntekUserManager.create_user` and stored as `CharField(max_length=64, unique=True)`). The
`EncryptedField` columns have no database-level uniqueness or index constraints.

---

### NEW-H1 — No MFA retry limit in `complete_oauth_mfa` — unlimited brute force

**Location:** `src/syntek_auth/services/oauth_mfa.py:316–322`

When `_verify_mfa_proof` returns `False`, the `PendingOAuthSession` row is NOT deleted and no
attempt counter is maintained. An attacker who obtains a victim's `pending_token` UUID can
brute-force TOTP codes (10^6 possibilities) or short email OTPs within the 600-second TTL with no
throttling.

**Impact:** `PendingOAuthSession` pending tokens are vulnerable to brute-force within TTL.

**Recommended fix direction:** Add an attempt counter column to `PendingOAuthSession`. After N
failed attempts (e.g. 3), delete the row and return `error_code="too_many_attempts"`.

---

### NEW-H2 — `make_jti_token` requires `FIELD_HMAC_KEY` at runtime; missing key raises mid-request

**Location:** `src/syntek_auth/services/lookup_tokens.py:29–45`,
`src/syntek_auth/services/tokens.py:240–244`

`rotate_refresh_token` and `revoke_refresh_token` call `make_jti_token(jti)`, which calls
`_hmac_key()`. `_hmac_key()` raises `ImproperlyConfigured` if `SYNTEK_AUTH['FIELD_HMAC_KEY']` is
absent or empty. This check occurs at request time, not at startup.

A consumer who configures `SYNTEK_AUTH` without `FIELD_HMAC_KEY` receives no error at startup
(`validate_settings` only validates keys that are present). The first token rotation request crashes
with `ImproperlyConfigured`, producing a 500 error visible to the client.

**Recommended fix direction:** `FIELD_HMAC_KEY` must be a required key validated at startup in
`validate_settings` — not presence-only, but mandatory.

---

### NEW-H3 — `SyntekUserManager.create_user` uses a single `FIELD_KEY` for all PII fields

**Location:** `src/syntek_auth/models/user.py:195–211`

`create_user` calls `encrypt_fields_batch(_fields_to_encrypt, _field_key, _model_name)` where
`_field_key` is read from `SYNTEK_AUTH['FIELD_KEY']` — a single key applied to all PII fields
(`email`, `phone`, `username`). The US008 / `SYNTEK_FIELD_KEY_*` convention implies per-field key
isolation.

Using a single shared key:

1. Violates per-field key isolation — rotating the email key forces re-encryption of phone and
   username.
2. Means `encrypt_fields_batch` applies one key to all fields — if the Rust API was designed for
   per-field keys, the Python manager is using it incorrectly.

**Recommended fix direction:** Clarify whether the design calls for per-field keys or a shared model
key. If per-field, resolve per-field keys in `create_user` and confirm the batch API signature.
Document the resolution explicitly.

---

### NEW-H4 — `_get_or_create_oidc_user` silently falls through `oidc_sub_hash` lookup

**Location:** `src/syntek_auth/mutations/oidc.py:344–374`

`_get_or_create_oidc_user` attempts `manager.get(oidc_sub_hash=lookup_key)`. The `oidc_sub_hash`
field does not exist on `AbstractSyntekUser` or `User`. The lookup always raises an exception
(caught by `contextlib.suppress(Exception)`) and falls through to email-based matching.

All OIDC user binding is therefore email-only, with no sub-based identifier stored:

- Users logging in via two providers with the same email are silently linked to the same account
  with no consent step.
- New OIDC users are created via `create_user(email=email, password=None)` with no email
  verification gating, bypassing `EMAIL_VERIFICATION_REQUIRED`.

**Recommended fix direction:** Add `oidc_sub_hash` to `AbstractSyntekUser` (or an `OidcIdentity`
related model). New OIDC accounts must be subject to `EMAIL_VERIFICATION_REQUIRED`.

---

## MEDIUM (Should fix soon, non-blocking for sign-off)

### 13. `conf.py` — Absence of `SYNTEK_AUTH` Key Does Not Validate Required Keys

**Location:** `src/syntek_auth/conf.py:103-182`

`validate_settings` is a partial-key validator — it only checks keys that are **present** in the
supplied dict. If a consumer supplies a minimal dict (e.g. only `LOGIN_FIELD`), all other keys are
silently skipped. There is no list of **required** keys that must be present.

For example, a consumer could supply `{'MFA_METHODS': ['totp']}` and omit `LOCKOUT_THRESHOLD`
entirely. The module would start with no lockout threshold enforced. There is no mechanism to
require that all keys above a security baseline are explicitly set.

**Impact:** Consumers who partially configure `SYNTEK_AUTH` receive no guidance that they have left
security-relevant settings unconfigured.

**Recommended fix direction:** Define a set of security-critical required keys (e.g.
`LOCKOUT_THRESHOLD`, `MFA_METHODS`, `LOGIN_FIELD`) that must always be present. Raise
`ImproperlyConfigured` if any required key is absent. Optional keys can retain their current
presence-only validation.

---

### 14. `enabled_mfa_methods` — Silent Filtering of Unrecognised Methods

**Location:** `src/syntek_auth/services/mfa.py:59`

```python
active = frozenset(configured_methods) & _VALID_MFA_METHODS
```

If a consumer passes an unrecognised method string (e.g. a typo like `"totpp"`), it is silently
dropped from the result. The consumer receives no feedback that a configured method is being
ignored. `conf.py:validate_settings` does catch unrecognised method names at startup, but only if
`MFA_METHODS` is present in the settings dict. If `enabled_mfa_methods` is called with a value that
bypasses settings validation (e.g. from a cached or dynamically loaded config), silent filtering
occurs.

**Impact:** A typo in `MFA_METHODS` after the initial validated startup (e.g. per-tenant config
overrides in a future feature) silently disables configured MFA methods with no log entry.

**Recommended fix direction:** Log a warning when an unrecognised method is filtered out. This is
defence-in-depth given the startup validation already catches this, but the service layer should not
fail silently.

---

### 15. `validate_oauth_providers` — `provider` Key Absence Not Handled

**Location:** `src/syntek_auth/backends/allowlist.py:90`

```python
provider_id: str = str(entry.get("provider", "")).lower()
```

If a provider dict is missing the `provider` key entirely, `provider_id` becomes `""` (empty
string). An empty string is not in `BLOCKED_PROVIDERS` and not in `BUILTIN_ALLOWED_PROVIDERS`. The
`mfa_enforced` check then fires and raises `ImproperlyConfigured` with a message that names the
empty string as the provider — which is a confusing and unhelpful error.

**Impact:** A misconfigured provider dict produces a cryptic error message that does not help the
consumer identify the actual problem (missing `provider` key).

**Recommended fix direction:** Explicitly check that the `provider` key is present and non-empty.
Raise `ImproperlyConfigured` with a message that says "a provider entry is missing the required
`provider` key" rather than falling through to the empty-string path.

---

## LOW / Observations

### L1. `compute_lockout_duration` — Zero `lockout_count` Not Guarded

**Location:** `src/syntek_auth/services/lockout.py:62`

`lockout_count=0` produces `base_duration * (2^-1)` which in Python integer arithmetic is
`base_duration * 0` (because `2**-1 = 0.5` and `int * 0.5 = float`). This would return a float, not
an int, breaking the return type annotation. No test covers `lockout_count=0`. The docstring states
it is "1-based" but no guard enforces this.

---

### L2. `_decode_jwt` — Broad `except Exception` on Payload Decode

**Location:** `src/syntek_auth/services/tokens.py:136`

```python
except Exception as exc:
    raise ValueError(f"JWT payload is not valid JSON: {exc}") from exc
```

A bare `except Exception` that catches and re-raises with a different message discards the original
exception type information. This makes debugging harder. Use `json.JSONDecodeError` and
`UnicodeDecodeError` specifically.

---

### L3. Factory Default Password Is Too Weak for Policy Compliance

**Location:** `src/syntek_auth/factories.py:67`

`UserFactory` defaults to `"testpassword123"` as the password. When `PASSWORD_REQUIRE_UPPERCASE` is
`True` (the default), this password fails the policy check. Tests that use `UserFactory.create()`
and then attempt any policy-validated operation will fail with unexpected policy violations rather
than the test's intended assertion. The default test password should satisfy all active policy
constraints.

---

### L4. Missing `PHONE_VERIFICATION_REQUIRED` in Boolean Key Validation List

**Location:** `src/syntek_auth/conf.py:43-56`

`PHONE_VERIFICATION_REQUIRED` is included in the documented configuration contract and in the test
helper (`minimal_valid_settings`) but is absent from `_BOOL_KEYS` in `conf.py`. A consumer who sets
`PHONE_VERIFICATION_REQUIRED = 1` (integer 1 instead of `True`) receives no validation error at
startup.

---

### L5. `allowlist.py` Error Messages Reference `OAUTH_ALLOWED_PROVIDERS` (Undocumented Key)

**Location:** `src/syntek_auth/backends/allowlist.py:95, 104`

Both `ImproperlyConfigured` messages direct consumers to "See
`SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS']` docs." This key does not appear anywhere in the documented
configuration contract (US009 story doc) or in `conf.py`. Consumers following the error message will
find no documentation for this key.

---

### L6. `rotate_refresh_token` — `payload["sub"]` Key Access Without `.get()`

**Location:** `src/syntek_auth/services/tokens.py:244`

```python
user_id=payload["sub"],
```

This will raise a bare `KeyError` (not a `ValueError`) if a malformed refresh token somehow passes
the HMAC check but lacks a `sub` claim. The caller catches `ValueError` but not `KeyError`, so the
raw exception would propagate up unhandled.

---

### L7. Tests — `TestRotateRefreshToken` Tests Share Global `_REVOKED_TOKENS` State

**Location:** `tests/test_us009_tokens.py:92-158`

All token tests operate against the module-level `_REVOKED_TOKENS` dict. Tests that rotate tokens
add entries to this dict which persist across other tests in the same process. If tests run in a
different order, a JTI generated in one test might appear in the revocation store from a prior test.
No fixture resets `_REVOKED_TOKENS` between tests. This is an existing test isolation gap that will
cause intermittent failures as the token test suite grows.

---

### NEW-L1 — `_user_has_mfa_configured` silently returns `False` on any DB error

**Location:** `src/syntek_auth/services/oauth_mfa.py:121–135`

Double `contextlib.suppress(Exception)` nesting means a DB timeout or ORM exception causes the
function to return `False`, incorrectly signalling that a user has no MFA configured. The user is
presented with `mfa_setup_required=True` when MFA is already set up, leading to incorrect UX in
degraded-DB scenarios. Low security impact; high friction impact.

---

### NEW-L2 — `complete_oauth_mfa` token pair issue does not handle non-integer token lifetime

**Location:** `src/syntek_auth/services/oauth_mfa.py:332–334`

`int(cfg.get("ACCESS_TOKEN_LIFETIME", 900))` raises `ValueError` if the setting is a non-integer
string (e.g. from a misconfigured env var). At this point in the function the `PendingOAuthSession`
has already been deleted (line 325) — the user cannot retry and must restart the OAuth flow. A
`validate_settings` check for integer type would catch this at startup.

---

## Missing Test Scenarios

The following scenarios are entirely absent from the current test suite:

1. `validate_access_token` called with a refresh token — should raise `ValueError` (typ mismatch)
2. `rotate_refresh_token` called with an access token — should raise `ValueError` (typ mismatch)
3. `compute_lockout_duration` with `lockout_count=0` — verify type and value correctness
4. `compute_lockout_duration` with very large `lockout_count` (e.g. 64, 100) — verify cap behaviour
5. `validate_settings` with `SYNTEK_AUTH` entirely absent from Django settings — verify behaviour
6. `PHONE_VERIFICATION_REQUIRED = 1` (non-bool) — verify `ImproperlyConfigured` is raised
7. A provider dict missing the `provider` key entirely — verify meaningful error message
8. `enabled_mfa_methods([])` — verify empty input returns empty list without error
9. `oidc_amr_satisfies_mfa` with only `"swk"` or only `"hwk"` in isolation
10. `is_password_expired` with `last_changed_days_ago=0` — newly set password is never expired
11. Session fixation test — verify a new session ID is issued after successful login
12. IDOR test — verify that `validate_access_token` payload `sub` cannot be used to access another
    user's resources without authorisation checks
13. Concurrent `rotate_refresh_token` calls with the same JTI — verify exactly one succeeds
14. `_REVOKED_TOKENS` reset fixture — all token tests need isolated state
15. **NEW** — `from syntek_auth.services.oauth_mfa import complete_oauth_mfa` — verify import
    succeeds after syntax fix (NEW-C1)
16. **NEW** — `completeSocialMfa` with email_otp belonging to a different user — verify
    `invalid_mfa_code` is returned, not `success=True` (NEW-C2)
17. **NEW** — `completeSocialMfa` called 4+ times with wrong codes — verify row is deleted and
    `too_many_attempts` is returned (NEW-H1)
18. **NEW** — `oidcCallback` with `provider_id="github"` but session `oidc_provider_id="google"` —
    verify rejection (NEW-C3)
19. **NEW** — `rotate_refresh_token` called without `FIELD_HMAC_KEY` configured — verify
    `ImproperlyConfigured` is raised at startup, not mid-request (NEW-H2)
20. **NEW** — `create_user` with separate per-field keys — verify each field is encrypted with the
    correct key (NEW-H3)
21. **NEW** — Two OIDC logins from different providers with the same email — verify explicit linking
    is required, not silent account merge (NEW-H4)
22. **NEW** — Start two processes with independent `_SIGNING_SECRET` values, issue a token in
    process 1, validate in process 2 — verify `ValueError` is raised with the current code, and that
    the fix (loading from config) resolves it (NEW-C4)
23. **NEW** — Restart the Django process (re-import `tokens.py`) after issuing a token — verify the
    token is invalid post-restart with the current code, and valid post-restart after the config-key
    fix (NEW-C4)
24. **NEW** — `SYNTEK_AUTH` missing `JWT_SIGNING_SECRET` (or `JWT_SIGNING_KEY` post-ES256 migration)
    — verify `ImproperlyConfigured` raised at startup, not at first token issuance (NEW-C4)

---

## Handoff Recommendations

- Run `/syntek-dev-suite:backend` to:
  - Fix Python 2 `except` syntax in `oauth_mfa.py` (NEW-C1) — blocks all other OAuth MFA work
  - Add user binding to `_verify_mfa_proof` email_otp (NEW-C2)
  - Add `session["oidc_provider_id"]` check in `oidcCallback` (NEW-C3)
  - Replace ephemeral `_SIGNING_SECRET` with a stable key loaded from
    `SYNTEK_AUTH['JWT_SIGNING_SECRET']` validated at startup (NEW-C4) — fix this before the ES256
    migration so the fix path is clean
  - Add `alg` header validation to `_decode_jwt` (Issue 1 immediate fix)
  - Add MFA attempt counter to `PendingOAuthSession` (NEW-H1)
  - Make `FIELD_HMAC_KEY` a required key validated at startup (NEW-H2)
  - Clarify and fix per-field key isolation in `SyntekUserManager` (NEW-H3)
  - Add `oidc_sub_hash` field and gate OIDC user creation on email verification (NEW-H4)
  - Implement green phase with all critical issues as blocking requirements.
- Run `/syntek-dev-suite:backend` (separate pass, post-stabilisation) to migrate JWT signing from
  HS256 to ES256 via PyJWT + cryptography (Issue 1 architectural fix, NEW-O1). Sequencing: stable
  config key first (NEW-C4), then `alg` header validation, then ES256 migration. Do not attempt the
  ES256 migration while the ephemeral secret or hand-rolled `_decode_jwt` are in place.
- Run `/syntek-dev-suite:test-writer` to add the missing test scenarios above, particularly items
  15–24 (new), items 1–2 (typ claim tests), and item 13 (concurrent rotation).
- Run `/syntek-dev-suite:debug` to investigate the `OIDC_PROVIDERS` vs `OAUTH_PROVIDERS` key
  mismatch (Issue 8) and determine the authoritative key name before the green phase writes any
  further code against either.
