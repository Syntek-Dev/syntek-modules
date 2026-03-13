# QA Report: US076 — Security Policy: MFA-Enforcing SSO, Key Rotation, and Network Architecture

**Date:** 11/03/2026 — **Updated:** 13/03/2026 **Analyst:** QA Agent (The Breaker) **Branch:**
`us009/syntek-auth` **Status:** CRITICAL ISSUES

---

## Revision Notes (13/03/2026)

The allowlist design was fundamentally revised between the original QA review and the current
branch. The `BLOCKED_PROVIDERS` set has been replaced by `MFA_GATED_PROVIDERS`. Providers such as
Google, Facebook, and Twitter/X are no longer rejected at startup — they pass startup validation and
are gated at the OAuth callback layer via `PendingOAuthSession`, requiring local MFA completion
before a full `TokenPair` is issued. This change resolves some original issues and introduces new
ones. The `oidc_callback` mutation is now fully implemented; it is no longer a stub.

**Issues resolved since last review:**

- ~~Issue 2~~ — `oidc_callback` is no longer a stub; runtime provider check is implemented.
- ~~Issue 3~~ — `oidc_amr_satisfies_mfa` function exists in `services/mfa.py` and is called in
  `oidc_callback` when `MFA_REQUIRED=True`.

**Issues updated:**

- Issue 1 reframed — concern now applies to `MFA_GATED_PROVIDERS` alias gaps rather than
  `BLOCKED_PROVIDERS` bypass.
- Issue 4 reframed — alias coverage concern now applies to `MFA_GATED_PROVIDERS`.

**New issues added:**

- NEW-C1 — Python 2 `except` syntax in `oauth_mfa.py` causes `SyntaxError` on import (critical).
- NEW-C2 — OIDC callback accepts `provider_id` from client input without verifying it against the
  session-stored provider (CSRF/provider-substitution attack vector).
- NEW-H1 — `_verify_mfa_proof` email_otp path calls `verify_email_token` without user binding (IDOR
  — any user's valid OTP satisfies another user's MFA challenge).
- NEW-H2 — No retry limit on `complete_oauth_mfa` with wrong MFA code.
- NEW-H3 — `_get_or_create_oidc_user` silently falls through `oidc_sub_hash` lookup; cross-provider
  account linking via email is unguarded.

---

## Summary

US076 introduces three independent security mechanisms: an SSO provider allowlist enforced at Django
startup, a versioned AES-256-GCM key-rotation scheme in the Rust layer, and proxy-trust settings
injected by `syntek-security`. The original "blocked" design has been replaced by an "MFA-gated"
approach: consumer OAuth providers now pass startup validation but require a local MFA challenge via
`completeSocialMfa`. The `oidcCallback` and `completeSocialMfa` mutations are now implemented.
Several new critical issues have been introduced in the OAuth MFA flow, most importantly a Python 2
`except` syntax error that crashes the module on import.

---

## CRITICAL (Blocks deployment)

### 1. `MFA_GATED_PROVIDERS` alias gaps — common library identifiers bypass gating entirely

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — lines 36–48

**Description:** `MFA_GATED_PROVIDERS` contains canonical provider strings: `"google"`,
`"facebook"`, `"twitter"`, `"x"`, `"apple"`, `"discord"`, `"microsoft"`. Third-party OAuth libraries
(`authlib`, `python-social-auth`, `httpx-oauth`) register these providers under different
identifiers: `"google_oauth2"`, `"twitter_oauth2"`, `"x_oauth2"`, `"twitterv2"`,
`"facebook_oauth2"`, `"sign_in_with_apple"`, `"apple_id"`, `"discord_oauth2"`. None of these are in
`MFA_GATED_PROVIDERS`.

An operator who configures a consumer Google OAuth provider as `"google_oauth2"` (as
`python-social-auth` names it) and sets `mfa_enforced: True` bypasses the `MFA_GATED_PROVIDERS`
gating entirely. The user receives a full token pair immediately — no `PendingOAuthSession` is
created, no local MFA is required. The consumer Google OAuth endpoint issues tokens without MFA, and
the `mfa_enforced: True` flag is self-certified with no verification.

**Attack Scenario:**

```python
SYNTEK_AUTH = {
    "OAUTH_PROVIDERS": [
        {"provider": "google_oauth2", "mfa_enforced": True},
    ]
}
```

Startup passes. `is_mfa_gated_provider("google_oauth2")` returns `False` (not in the set). The
callback issues a full `TokenPair` directly, skipping the pending session flow entirely.

**Impact:** The MFA gating for consumer OAuth providers can be bypassed by any operator using
library-specific provider identifier strings. The security guarantee of the US076 policy is voided
for these deployments.

**Reproduce:** Configure `{"provider": "google_oauth2", "mfa_enforced": True}`. Call `oidcCallback`.
Observe `is_mfa_gated_provider("google_oauth2")` returns `False` → full token pair issued, no MFA.

**Recommended fix direction:** Expand `MFA_GATED_PROVIDERS` to include common library-specific
aliases, or use prefix/pattern matching, or (most robust) use a closed allowlist that requires all
provider identifiers to be on either `MFA_GATED_PROVIDERS` or `BUILTIN_ALLOWED_PROVIDERS` without
any third category.

---

### NEW-C1 — Python 2 `except` syntax in `complete_oauth_mfa` crashes on import

**File:** `packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py` — line 281

**Description:**

```python
except ValueError, AttributeError:
```

This is Python 2 syntax. Python 3 requires `except (ValueError, AttributeError):`. This is a
`SyntaxError` that prevents the entire `oauth_mfa` module from being imported. Any code that imports
`complete_oauth_mfa`, `issue_oauth_pending_session`, or any other name from this module will fail at
import time with an uncaught `SyntaxError`.

**Impact:** The entire `completeSocialMfa` mutation and the `oidcCallback` MFA-gating flow are
non-functional. Any import of `syntek_auth.services.oauth_mfa` — including by `mutations/oidc.py` at
resolver execution time — raises `SyntaxError`. This silently breaks the OAuth MFA flow in any
environment that imports this module.

**Reproduce:** `from syntek_auth.services.oauth_mfa import complete_oauth_mfa` — raises
`SyntaxError: invalid syntax` on the `except ValueError, AttributeError:` line.

**Recommended fix direction:** Replace `except ValueError, AttributeError:` with
`except (ValueError, AttributeError):`.

---

### NEW-C2 — OIDC callback accepts `provider_id` from client without session verification

**File:** `packages/backend/syntek-auth/src/syntek_auth/mutations/oidc.py` — lines 157–213

**Description:** `oidc_callback` stores `oidc_provider_id` in the session during `oidc_auth_url`
(line 86) but never retrieves or validates it against `input.provider_id` during the callback (lines
157–213). The `state` parameter is validated correctly (constant-time comparison against
`session["oidc_state"]`), but `input.provider_id` is accepted as-is from the client request.

An attacker who initiates a legitimate auth flow for a MFA-gated provider (e.g. Google) but then
substitutes `provider_id="github"` in the callback POST can trigger
`is_mfa_gated_provider("github")` which returns `False` (GitHub is a `BUILTIN_ALLOWED_PROVIDER`).
The callback then issues a full `TokenPair` without creating a `PendingOAuthSession`.

**Attack Scenario:**

1. Attacker starts login flow for Google → `oidc_state` and `oidc_provider_id="google"` stored in
   session.
2. Attacker completes Google OAuth (obtains code + state).
3. Attacker calls `oidcCallback` with `provider_id="github"` and valid `state`.
4. State validates. `get_provider_config("github")` is called — this fails with `ValueError` only if
   the consumer has not configured GitHub as a provider. If GitHub IS configured (and most Syntek
   deployments will have it), the callback proceeds to exchange the code against GitHub's token
   endpoint with the Google authorisation code — which will fail at the exchange step. But if the
   attacker can obtain a valid GitHub code via a parallel flow, this opens a provider-substitution
   window.

More critically: if an attacker supplies a provider_id that is on `BUILTIN_ALLOWED_PROVIDERS` but is
not actually configured in `SYNTEK_AUTH['OAUTH_PROVIDERS']`, `get_provider_config` raises
`ValueError`, propagating as an unhandled error. This is an information-disclosure vector revealing
the configured provider list.

**Impact:** Provider-identity substitution bypass of the MFA gating system. Session-bound `state`
only validates replay but does not bind the callback to the originally requested provider.

**Recommended fix direction:** Retrieve `session["oidc_provider_id"]` in `oidc_callback` and assert
`input.provider_id == session["oidc_provider_id"]` using `_constant_time_eq` before proceeding with
any discovery or token exchange.

---

### 3. `mfa_enforced: True` is entirely operator self-certification with no verification

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — lines 133–139

**Description:** For providers not in `MFA_GATED_PROVIDERS` and not in `BUILTIN_ALLOWED_PROVIDERS`,
the only check is `entry.get("mfa_enforced", False)`. No OIDC discovery document check, no `amr`
claim validation, no cryptographic proof. An operator who configures a locally hosted mock IdP with
`mfa_enforced: True` passes startup with no runtime MFA enforcement.

The `oidc_callback` mutation does check `oidc_amr_satisfies_mfa` when `MFA_REQUIRED=True` (line
187). However this check applies to ALL providers (both allowlisted and custom), not specifically to
`mfa_enforced: True` self-certified providers. A self-certified custom provider that does not
include an `amr` claim will only be rejected if `MFA_REQUIRED=True` globally. If
`MFA_REQUIRED=False`, the amr check is skipped entirely, and the custom provider is trusted with no
MFA verification.

**Impact:** Custom OIDC providers where `MFA_REQUIRED=False` are fully trusted on operator
self-certification alone. No runtime MFA verification occurs.

**Recommended fix direction:** When `entry.get("mfa_enforced", True)` is set for a custom provider,
the `oidc_callback` must always verify the `amr` claim from the ID token, regardless of the global
`MFA_REQUIRED` setting. The `mfa_enforced` certification should bind a per-provider amr check, not
just operate as a startup-time flag.

---

## HIGH (Must fix before sign-off)

### NEW-H1 — `_verify_mfa_proof` email_otp path has no user binding — IDOR

**File:** `packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py` — lines 161–165

**Description:**

```python
if mfa_method == "email_otp":
    from syntek_auth.services.email_verification import verify_email_token
    result = verify_email_token(token=mfa_proof)
    return result.success
```

`verify_email_token` is called with only `token=mfa_proof` — the `user_id` parameter is not passed.
The email verification service validates the token against the `VerificationCode` table. If the
token lookup is not scoped to the user associated with the `PendingOAuthSession`, any valid email
verification token belonging to _any user in the system_ satisfies the MFA challenge for the pending
session.

**Attack Scenario:**

1. Attacker has a valid (unexpired) email verification token for their own account (e.g. from their
   own registration flow that they did not complete).
2. Attacker initiates `completeSocialMfa` for victim's pending session UUID.
3. Attacker submits their own email OTP as `mfa_proof`.
4. `verify_email_token` validates the token (it is valid) and returns `success=True`.
5. Victim's full `TokenPair` is issued to the attacker.

**Impact:** Complete account takeover for any user who has an active `PendingOAuthSession`, by any
attacker who holds a valid email OTP token for any account.

**Recommended fix direction:** `verify_email_token` must accept a `user_id` parameter and validate
that the token belongs to the specified user. The call in `_verify_mfa_proof` must pass
`user_id=user_id` to bind the verification to the correct account.

---

### NEW-H2 — No retry limit on `complete_oauth_mfa` with an incorrect MFA code

**File:** `packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py` — lines 316–322

**Description:** When `_verify_mfa_proof` returns `False`, `complete_oauth_mfa` returns
`error_code="invalid_mfa_code"` and the `PendingOAuthSession` row is NOT deleted. There is no
attempt counter, no rate limit, and no lockout mechanism on the `complete_oauth_mfa` endpoint.

An attacker who obtains a victim's `pending_token` UUID (possible if the UUID is transmitted over an
insecure channel or guessable) can brute-force the OTP by submitting guesses until expiry, with no
throttling.

**Impact:** The `pending_token` + unlimited OTP guessing defeats the MFA gating. A 6-digit TOTP code
has 10^6 possibilities; at 600 seconds TTL, even modest retry rates would exhaust the space before
expiry.

**Recommended fix direction:** Add an attempt counter to `PendingOAuthSession`. After N failed
attempts (e.g. 3), delete the row and return `error_code="too_many_attempts"`. The client must
restart the OAuth flow.

---

<!-- markdownlint-disable MD013 -->

### NEW-H3 — `_get_or_create_oidc_user` — `oidc_sub_hash` field does not exist on `AbstractSyntekUser`; cross-provider account collision via email

<!-- markdownlint-enable MD013 -->

**File:** `packages/backend/syntek-auth/src/syntek_auth/mutations/oidc.py` — lines 344–374

**Description:** `_get_or_create_oidc_user` attempts `manager.get(oidc_sub_hash=lookup_key)` to find
an existing user by provider+sub hash. The `oidc_sub_hash` field does not exist on
`AbstractSyntekUser` or `User` in `models/user.py`. The lookup always raises an exception (caught by
`contextlib.suppress(Exception)`) and falls through to the email-based lookup.

This means OIDC user binding is entirely email-based:

- A user who logs in via Google with `email=alice@example.com` and later via GitHub with the same
  email will be resolved to the same account with no explicit linking step or consent.
- A user who changes their email at the provider level will create a duplicate account.
- There is no sub-based binding to prevent cross-provider account merging.

Additionally, new OIDC users are created via `manager.create_user(email=email, password=None)` with
no `email_verified` flag, no account activation step, and no rate limiting. A provider that issues
ID tokens for any email address (e.g. a misconfigured self-hosted Keycloak) can silently create
accounts for arbitrary email addresses.

**Impact:** Unintended cross-provider account linkage and silent account creation for any email
address validated by a configured OIDC provider.

**Recommended fix direction:** Add `oidc_sub_hash` as a field to `AbstractSyntekUser` (or a related
`OidcIdentity` model). New OIDC accounts must be created in an unverified state and subject to the
same `EMAIL_VERIFICATION_REQUIRED` gating as password-based registrations.

---

### 4. `"x"` is gated but `"twitter_oauth2"`, `"twitterv2"`, `"x_oauth2"` are not

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — lines 36–48

**Description:** (Updated from original Issue 4.) The concern now applies to `MFA_GATED_PROVIDERS`
rather than `BLOCKED_PROVIDERS`. `"twitter"` and `"x"` are in the set, but `"twitter_oauth2"`,
`"twitterv2"`, `"x_oauth2"`, and `"x.com"` are not. An operator using any of these strings passes
through to the `mfa_enforced: True` path and bypasses the `PendingOAuthSession` flow.

The same alias gap exists for `"apple"` (variants: `"apple_id"`, `"sign_in_with_apple"`, `"siwa"`),
`"google"` (variants: `"google_oauth2"`, `"googleapis"`), and `"facebook"` (variants:
`"facebook_oauth2"`, `"fb"`).

**Impact:** MFA gating is bypassed for consumer OAuth providers configured under library-specific
alias strings.

**Recommended fix direction:** Expand `MFA_GATED_PROVIDERS` to include documented library aliases,
or prefer a closed-allowlist model.

---

### 5. Key version `0` is reserved but not rejected at `KeyRing.add()` — reserved version can be inserted silently

**File:** `rust/syntek-crypto/src/key_versioning.rs` — lines 73–84

_(Unchanged from original report — issue still present.)_

**Description:** `KeyRing::add()` does not reject `KeyVersion(0)`. A caller can insert a version-0
key into the ring. `KeyVersion(0)` occupies byte prefix `[0x00, 0x00]`, which could collide with
unversioned ciphertexts stored before the US076 key versioning was introduced. Decryption of a
legacy ciphertext via `decrypt_versioned` would interpret the first two nonce bytes as a version
number and fail with a "key version not in ring" error rather than a helpful "unversioned
ciphertext" diagnostic.

**Impact:** Silent data corruption path during migration from unversioned (US006) to versioned
ciphertexts.

**Reproduce:** `ring.add(KeyVersion(0), &[0u8; 32])` — returns `Ok(())`.

**Recommended fix direction:** `KeyRing::add()` should return `CryptoError::InvalidInput` for
`KeyVersion(0)`.

---

### 6. `reencrypt_to_active` decodes the blob twice

**File:** `rust/syntek-crypto/src/key_versioning.rs` — lines 253–282

_(Unchanged from original report — issue still present.)_

`reencrypt_to_active` decodes the base64 blob to inspect the 2-byte version prefix, then calls
`decrypt_versioned` which decodes the same base64 string again. Violates the principle that
security-critical code should not redundantly re-parse untrusted input. Not an immediate
vulnerability due to `base64ct` determinism, but structurally introduces a TOCTOU risk if the
function is ever refactored.

**Recommended fix direction:** Extract a helper that accepts `&[u8]` (already-decoded bytes) and
call it from both `decrypt_versioned` and `reencrypt_to_active`.

---

### 7. `apply_proxy_settings` uses `settings._wrapped.__dict__` — Django private API

**File:** `packages/backend/syntek-security/src/syntek_security/proxy_settings.py` — line 47

_(Unchanged from original report — issue still present.)_

`_wrapped` is not guaranteed stable across Django major versions. If `_wrapped` is `None` (before
settings are configured), accessing `settings._wrapped.__dict__` raises `AttributeError`. A
deployment that assumes proxy settings are active when the module is installed could serve HTTP
without HTTPS redirect, with no error at startup.

---

## MEDIUM (Should fix)

### 8. Error message references `SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS']` — key does not exist

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — line 138

_(Unchanged from original report — issue still present.)_

The error message directs operators to `SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS']`. The actual settings
key is `SYNTEK_AUTH['OAUTH_PROVIDERS']`. Operators who read the error and search their configuration
for `OAUTH_ALLOWED_PROVIDERS` will find nothing.

---

### 9. `OAUTH_PROVIDERS` entry with no `provider` key silently resolves to empty string

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — line 121

_(Unchanged from original report — issue still present.)_

`provider_id: str = str(entry.get("provider", "")).lower()` defaults to `""`. An entry
`{"mfa_enforced": True}` (missing `provider`) raises `ImproperlyConfigured` with a confusing message
naming `""` as the provider rather than identifying the missing key.

---

### 10. `validate_oauth_providers` accepts a non-list `OAUTH_PROVIDERS` without a clear error

**File:** `packages/backend/syntek-auth/src/syntek_auth/backends/allowlist.py` — line 118

_(Unchanged from original report — issue still present.)_

If `OAUTH_PROVIDERS` is a dict or string, iterating over it produces `AttributeError` from
`entry.get(...)` rather than an `ImproperlyConfigured` with a useful message.

---

### 11. `KeyRing` allows duplicate version entries

**File:** `rust/syntek-crypto/src/key_versioning.rs` — lines 73–84

_(Unchanged from original report — issue still present.)_

`KeyRing::add()` pushes to a `Vec` without checking for duplicate `KeyVersion` values. Two adds for
the same version create two entries; `active()` resolves non-deterministically.

---

### 12. The network architecture document is not a separate file

**Description:** The story task is marked `[x]` complete: "Publish network architecture diagram and
reference to `docs/GUIDES/NETWORK-ARCHITECTURE.md`." The architecture content now lives as a section
within `docs/STORIES/US076.md`, not as a standalone file at `docs/GUIDES/NETWORK-ARCHITECTURE.md`.

The path `docs/GUIDES/NETWORK-ARCHITECTURE.md` does not exist. Downstream consumers
(`syntek-platform`, `syntek-templates`) that are expected to reference this path will not find it.

**Recommended fix direction:** Either create `docs/GUIDES/NETWORK-ARCHITECTURE.md` (with the content
from the US076 story section) or update the story task to reflect that the document is embedded in
the story file and update all cross-references accordingly.

---

### 13. `syntek-auth` module README does not document the MFA-gated provider table

_(Unchanged from original report — issue still present.)_

No `README.md` exists in `packages/backend/syntek-auth/`. The story task is marked `[x]` complete.
Operators installing `syntek-auth` have no module-level documentation of the MFA gating policy.

---

### 14. Celery key rotation task absent — ACs marked Satisfied but deferred

_(Unchanged from original report — issue still present.)_

Key rotation acceptance criteria (90-day automatic rotation, batch re-encryption, failure handling,
key retirement) are marked Satisfied in the completion record but are noted as deferred in the story
Notes. No Celery task exists anywhere in the codebase. No follow-up story ID is referenced.

---

## LOW / Observations

### 15. `mfa_enforced` type not strictly validated (truthy non-boolean passes)

_(Unchanged from original report — issue still present.)_

`entry.get("mfa_enforced", False)` accepts truthy non-booleans. Not consistent with `conf.py` which
uses strict `isinstance(value, bool)` checks.

---

### 16. `reencrypt_to_active` blob 3–29 bytes gap untested

_(Unchanged from original report — issue still present.)_

A blob of 3–29 bytes passes the 2-byte version check but fails inside `decrypt_versioned`. The gap
between the two guards is not covered by any test.

---

### 17. `test_proxy_settings.py` uses `delattr` without monkeypatch teardown

_(Unchanged from original report — issue still present.)_

---

### 18. `decrypt_versioned` minimum blob length comment is technically correct but misleading

_(Unchanged from original report — documentation-only observation.)_

---

### 19. `validate_settings` (US009) skips validation on empty dict

_(Unchanged from original report — issue still present.)_

---

### NEW-L1 — `_user_has_mfa_configured` silently returns `False` on any DB error

**File:** `packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py` — lines 121–135

`contextlib.suppress(Exception)` is used around the user lookup. Any DB error (timeout, connection
failure, ORM exception) causes `_user_has_mfa_configured` to return `False`, signalling that the
user has no MFA configured when they may well have it configured. This causes
`issue_oauth_pending_session` to return `mfa_setup_required=True` incorrectly — the user will be
directed to configure MFA they have already set up. Low immediate security impact; high UX impact in
degraded-DB scenarios.

---

### NEW-L2 — `complete_oauth_mfa` tokens issued without `SYNTEK_AUTH` defaults validation

**File:** `packages/backend/syntek-auth/src/syntek_auth/services/oauth_mfa.py` — lines 332–334

`int(cfg.get("ACCESS_TOKEN_LIFETIME", 900))` and `int(cfg.get("REFRESH_TOKEN_LIFETIME", 604800))`
are read directly with `int()` cast and no type validation. If an operator sets these to a
non-integer value (e.g. a string from an env var), the `int()` cast will raise `ValueError`
mid-request, producing a 500 error after MFA has already been verified. The user's pending session
has been deleted by this point (`session.delete()` on line 325) — the user cannot retry and must
restart the OAuth flow.

---

## Missing Test Scenarios

1. **`MFA_GATED_PROVIDERS` alias bypass** — `{"provider": "google_oauth2", "mfa_enforced": True}`
   should trigger `PendingOAuthSession`; currently passes startup and issues full token pair.
2. **`oidcCallback` with mismatched `provider_id`** — verify `provider_id` is validated against
   `session["oidc_provider_id"]`.
3. **`complete_oauth_mfa` syntax error** — `oauth_mfa.py` currently cannot be imported; verify
   import succeeds after syntax fix.
4. **`complete_oauth_mfa` with another user's email OTP** — verify `verify_email_token` is
   user-scoped and the cross-user OTP path is blocked.
5. **`complete_oauth_mfa` brute force** — submitting 4+ wrong codes should invalidate the pending
   session.
6. **`_get_or_create_oidc_user` with matching email across two providers** — verify an explicit
   linking step is required.
7. **`KeyVersion(0)` passed to `KeyRing::add()`** — should return `CryptoError::InvalidInput`.
8. **Duplicate version in `KeyRing::add()`** — adding the same version twice should fail.
9. **`reencrypt_to_active` with blob lengths 3–29** — gap between 2-byte and 30-byte guards.
10. **`apply_proxy_settings` when `settings._wrapped` is `None`** — should not raise
    `AttributeError`.
11. **`OAUTH_PROVIDERS` set to a non-list type** — should raise `ImproperlyConfigured`.
12. **Rotation task deferred** — cannot be written until `syntek-tasks` is available; must be
    tracked.

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to:
  - Fix Python 2 `except` syntax in `oauth_mfa.py` (NEW-C1)
  - Add `session["oidc_provider_id"]` check in `oidcCallback` (NEW-C2)
  - Add user binding to `_verify_mfa_proof` email_otp path (NEW-H1)
  - Add MFA attempt counter to `PendingOAuthSession` (NEW-H2)
  - Add `oidc_sub_hash` field or `OidcIdentity` model (NEW-H3)
  - Fix `MFA_GATED_PROVIDERS` alias coverage (Issue 1 / Issue 4)
  - Fix `OAUTH_ALLOWED_PROVIDERS` key name inconsistency in error message (Issue 8)
  - Guard `settings._wrapped` against `None` (Issue 7)
  - Enforce `KeyVersion(0)` rejection in `KeyRing::add()` (Issue 5)
  - Enforce duplicate version rejection in `KeyRing::add()` (Issue 11)

- Run `/syntek-dev-suite:test-writer` to add tests covering all missing scenarios above.

- Run `/syntek-dev-suite:completion` to update the US076 story status to reflect:
  - Celery rotation task is deferred (not complete)
  - Network architecture document path is incorrect (embedded in story, not a separate file)
