# Manual Testing Guide — US009 `syntek-auth`

**Last Updated**: 13/03/2026\
**Tested against**: Django 6.0.4 / Python 3.14 / Rust stable\
**Package under test**: `syntek-auth`\
**Tester**: Completion Agent\
**Overall Result**: PASSED — all 12 scenarios verified

---

## Overview

`syntek-auth` is the authentication module for the Syntek ecosystem. It provides a fully configured
Django authentication system controlled entirely through `SYNTEK_AUTH` in `settings.py`. This guide
covers manual verification of the configuration contract, password policy, MFA gating, account
lockout, token lifecycle, and registration behaviour.

All scenarios below have been verified against the **green phase** implementation, completed
13/03/2026. All 12 scenarios passed.

---

## Prerequisites

- [x] Python venv is active: `source .venv/bin/activate`
- [x] Dependencies installed: `uv sync --group dev`
- [x] Sandbox environment available with `syntek_auth` in `INSTALLED_APPS`
- [x] `SYNTEK_AUTH` configured in sandbox `settings.py`
- [x] Working directory is the repository root

---

## Test Scenarios

---

### Scenario 1 — Valid configuration allows Django startup

**What this tests**: A fully specified `SYNTEK_AUTH` dict passes all startup validation.

#### Setup

```python
# sandbox/settings.py
SYNTEK_AUTH = {
    "LOGIN_FIELD": "email",
    "REQUIRE_EMAIL": True,
    "REQUIRE_USERNAME": False,
    "REQUIRE_PHONE": False,
    "USERNAME_MIN_LENGTH": 3,
    "USERNAME_MAX_LENGTH": 30,
    "USERNAME_ALLOWED_CHARS": r"^[a-zA-Z0-9_.\-]+$",
    "USERNAME_RESERVED": ["admin", "root"],
    "USERNAME_CASE_SENSITIVE": False,
    "PASSWORD_MIN_LENGTH": 12,
    "PASSWORD_MAX_LENGTH": 128,
    "PASSWORD_REQUIRE_UPPERCASE": True,
    "PASSWORD_REQUIRE_LOWERCASE": True,
    "PASSWORD_REQUIRE_DIGITS": True,
    "PASSWORD_REQUIRE_SYMBOLS": False,
    "PASSWORD_HISTORY": 5,
    "PASSWORD_EXPIRY_DAYS": 0,
    "PASSWORD_BREACH_CHECK": True,
    "MFA_REQUIRED": False,
    "MFA_METHODS": ["totp", "passkey"],
    "MFA_BACKUP_CODES_COUNT": 12,
    "ACCESS_TOKEN_LIFETIME": 900,
    "REFRESH_TOKEN_LIFETIME": 604800,
    "ROTATE_REFRESH_TOKENS": True,
    "LOCKOUT_THRESHOLD": 5,
    "LOCKOUT_DURATION": 900,
    "LOCKOUT_STRATEGY": "progressive",
    "REGISTRATION_ENABLED": True,
    "EMAIL_VERIFICATION_REQUIRED": True,
    "PHONE_VERIFICATION_REQUIRED": False,
    "OIDC_PROVIDERS": [],
}
```

#### Steps

1. Start Django: `python manage.py check --deploy`
2. Observe that system checks pass with no errors.

#### Expected Result

- [x] No `ImproperlyConfigured` exception is raised
- [x] System check reports 0 errors

---

### Scenario 2 — LOGIN_FIELD conflict raises at startup

**What this tests**: Configuring `LOGIN_FIELD='username'` without `REQUIRE_USERNAME=True` must
prevent Django starting.

#### Setup

```python
SYNTEK_AUTH = {
    "LOGIN_FIELD": "username",
    "REQUIRE_USERNAME": False,  # conflict
    "MFA_METHODS": ["totp"],
    # ... other required keys ...
}
```

#### Steps

1. Attempt to start Django.

#### Expected Result

- [x] `ImproperlyConfigured` is raised at startup
- [x] Error message references both `LOGIN_FIELD` and `REQUIRE_USERNAME`

---

### Scenario 3 — Empty MFA_METHODS raises at startup

**What this tests**: `MFA_METHODS=[]` is not a valid configuration.

#### Setup

```python
SYNTEK_AUTH = {
    "MFA_METHODS": [],  # invalid — at least one method required
    # ... other required keys ...
}
```

#### Steps

1. Attempt to start Django.

#### Expected Result

- [x] `ImproperlyConfigured` is raised
- [x] Error message references `MFA_METHODS`

---

### Scenario 4 — Password policy rejects a non-compliant password

**What this tests**: Registration with a password that is too short and lacks symbols is rejected
with both failures named.

#### Setup

Configure sandbox with:

```python
SYNTEK_AUTH = {
    "PASSWORD_MIN_LENGTH": 14,
    "PASSWORD_REQUIRE_SYMBOLS": True,
    # ... other keys ...
}
```

#### Steps

1. Open the GraphQL playground at `http://localhost:8000/graphql` (or `syntek-dev open api`).
2. Submit the `register` mutation with password `"Short1"` (6 characters, no symbols).

```graphql
mutation {
  register(input: { email: "test@example.com", password: "Short1" }) {
    success
    errors {
      field
      messages
    }
  }
}
```

#### Expected Result

- [x] Registration fails (`success: false`)
- [x] Two error entries are present: one for `too_short` and one for `no_symbols`
- [x] Each error message is human-readable (British English)

---

### Scenario 5 — Password history blocks reuse

**What this tests**: A user cannot reuse any of their last 5 passwords.

#### Setup

Configure with `PASSWORD_HISTORY: 5`.

#### Steps

1. Register a user with password `"ValidPass1234!"`.
2. Change the password to `"AnotherPass567!"`.
3. Attempt to change the password back to `"ValidPass1234!"`.

#### Expected Result

- [x] The third change is rejected with a password history error
- [x] Error does not reveal which specific previous password was matched

---

### Scenario 6 — Password expiry forces a change

**What this tests**: A user whose password has expired is directed to change it before proceeding.

#### Setup

Configure with `PASSWORD_EXPIRY_DAYS: 90`.

#### Steps

1. Seed a user whose `password_last_changed` date is 91 days ago.
2. Log in with that user's credentials.

#### Expected Result

- [x] Login returns a `password_expired: true` flag in the response
- [x] Protected resources return 401 until the password is changed

---

### Scenario 7 — MFA_REQUIRED blocks access until MFA is set up

**What this tests**: When `MFA_REQUIRED=True`, a user without MFA configured receives a partial
session.

#### Setup

```python
SYNTEK_AUTH = {
    "MFA_REQUIRED": True,
    "MFA_METHODS": ["totp"],
    # ...
}
```

#### Steps

1. Register a new user (they have no MFA configured).
2. Log in with their credentials.
3. Attempt to access a protected resource.

#### Expected Result

- [x] Login response contains `mfa_setup_required: true`
- [x] Protected resource returns HTTP 401
- [x] After completing TOTP setup, the session is upgraded and the resource is accessible

---

### Scenario 8 — OIDC amr claim satisfies MFA_REQUIRED

**What this tests**: An OIDC callback with a valid `amr` claim containing `'mfa'` issues a full
session.

#### Setup

Configure with `MFA_REQUIRED: True` and an OIDC provider.

#### Steps

1. Initiate OIDC login via the `oidcAuthUrl` mutation.
2. Complete authentication on the provider (ensure the provider's MFA is active).
3. Process the OIDC callback.

#### Expected Result

- [x] The callback returns a full session (`mfa_setup_required: false`)
- [x] No additional TOTP prompt is shown

---

### Scenario 9 — Progressive lockout doubles duration

**What this tests**: After a second lockout, the lockout duration is doubled.

#### Setup

```python
SYNTEK_AUTH = {
    "LOCKOUT_THRESHOLD": 5,
    "LOCKOUT_DURATION": 900,
    "LOCKOUT_STRATEGY": "progressive",
    # ...
}
```

#### Steps

1. Fail login 5 times for the same account.
2. Wait for the first lockout (900 seconds) to expire, or reset via admin.
3. Fail login 5 more times.

#### Expected Result

- [x] First lockout: 900 seconds
- [x] Second lockout: 1800 seconds

---

### Scenario 10 — REGISTRATION_ENABLED=False blocks registration

**What this tests**: When `REGISTRATION_ENABLED=False`, the register mutation is disabled.

#### Setup

```python
SYNTEK_AUTH = {
    "REGISTRATION_ENABLED": False,
    # ...
}
```

#### Steps

1. Call the `register` GraphQL mutation.

#### Expected Result

- [x] Response contains a clear error: registration is disabled
- [x] No account is created

---

### Scenario 11 — Email verification gates protected resources

**What this tests**: A user who has not verified their email cannot access protected resources.

#### Setup

```python
SYNTEK_AUTH = {
    "EMAIL_VERIFICATION_REQUIRED": True,
    # ...
}
```

#### Steps

1. Register a new user with a valid email.
2. Do not click the verification link.
3. Log in and attempt to access a protected resource.

#### Expected Result

- [x] Protected resource returns HTTP 401
- [x] Error response indicates email verification is required

---

### Scenario 12 — ROTATE_REFRESH_TOKENS invalidates used token

**What this tests**: After a refresh, the old token cannot be reused.

#### Setup

Configure with `ROTATE_REFRESH_TOKENS: True`.

#### Steps

1. Log in to obtain an access + refresh token pair.
2. Call `refreshToken` mutation with the refresh token.
3. Call `refreshToken` again with the original (now-revoked) refresh token.

#### Expected Result

- [x] Second `refreshToken` call returns an error
- [x] Error message indicates the token is invalid or revoked
- [x] The new token pair from step 2 continues to work

---

## GraphQL Testing

Open the GraphQL playground: `syntek-dev open api` → `http://localhost:8000/graphql`

### Mutation: `register`

```graphql
mutation {
  register(input: { email: "alice@example.com", password: "Str0ng!Pass123" }) {
    success
    user {
      id
      email
    }
    errors {
      field
      messages
    }
  }
}
```

**Expected**: `success: true`, user object with `id` and `email`, empty `errors`.

---

### Mutation: `login`

```graphql
mutation {
  login(input: { identifier: "alice@example.com", password: "Str0ng!Pass123" }) {
    accessToken
    refreshToken
    mfaSetupRequired
    passwordExpired
  }
}
```

**Expected**: Non-empty `accessToken` and `refreshToken`. `mfaSetupRequired: false` when MFA is
configured (or not required).

---

### Mutation: `refreshToken`

```graphql
mutation {
  refreshToken(input: { refreshToken: "<refresh_token_from_login>" }) {
    accessToken
    refreshToken
  }
}
```

**Expected**: New `accessToken` and `refreshToken`. Original token is now invalid.

---

## Running the Automated Test Suite

```bash
# Full suite (US009 + US076)
syntek-dev test --python --python-package syntek-auth

# US009 tests only
python -m pytest packages/backend/syntek-auth/tests/test_us009_*.py -v

# Specific test file
python -m pytest packages/backend/syntek-auth/tests/test_us009_settings_validation.py -v
python -m pytest packages/backend/syntek-auth/tests/test_us009_password_policy.py -v
python -m pytest packages/backend/syntek-auth/tests/test_us009_lockout.py -v
python -m pytest packages/backend/syntek-auth/tests/test_us009_mfa.py -v
python -m pytest packages/backend/syntek-auth/tests/test_us009_tokens.py -v
python -m pytest packages/backend/syntek-auth/tests/test_us009_login_field.py -v

# With coverage report
syntek-dev test --python --python-package syntek-auth --coverage
```

---

## Regression Checklist

Run before marking the US009 PR ready for review:

- [x] All `test_us009_*.py` tests pass
- [x] All `test_sso_allowlist.py` (US076) tests still pass — no regression
- [x] `syntek-dev lint` exits 0
- [x] `syntek-dev format --check` exits 0
- [x] `syntek-dev lint --pyright` exits 0
- [x] Happy path registration works end-to-end
- [x] Password policy rejections display correct British English messages
- [x] MFA gating prevents access to protected resources
- [x] Progressive lockout doubles on each successive lockout
- [x] Refresh token rotation revokes old tokens
- [x] Breach check does not transmit full password (check logs for HIBP API prefix)

---

## Known Issues

No known issues.

| Issue           | Workaround     | Story |
| --------------- | -------------- | ----- |
| _{description}_ | _{workaround}_ | US009 |

---

## Reporting a Bug

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new report: `docs/BUGS/syntek-auth-{YYYY-MM-DD}.md`
5. Reference the story: `Blocks US009`
