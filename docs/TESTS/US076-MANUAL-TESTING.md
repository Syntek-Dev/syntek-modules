# Manual Testing Guide — US076 Security Policy

**Last Updated**: 2026-03-11 — Green phase complete\
**Tested against**: Django 6.0.4 / Python 3.14 / Rust stable\
**Packages under test**: `syntek-auth`, `syntek-security`, `syntek-crypto`

---

## Overview

US076 hardens three areas of the Syntek security baseline:

1. **SSO provider allowlist** (`syntek-auth`) — only OAuth providers where MFA is enforced at the
   platform level are permitted. Blocked providers cause Django startup to fail with an
   `ImproperlyConfigured` error naming the blocked provider.

2. **Encryption key rotation** (`syntek-crypto`) — AES-256-GCM ciphertexts carry a 2-byte key
   version prefix. A `KeyRing` maps version numbers to key bytes, enabling zero-downtime key
   rotation via the lazy re-encryption pattern.

3. **Proxy trust settings** (`syntek-security`) — `SyntekSecurityConfig.ready()` injects
   `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, and `SECURE_SSL_REDIRECT` into Django settings
   at startup.

---

## Prerequisites

- [ ] Python venv is active: `source .venv/bin/activate`
- [ ] Dependencies installed: `uv sync --group dev`
- [ ] Rust toolchain available: `cargo --version`
- [ ] Working directory is the repository root

---

## Test Scenarios

---

### Scenario 1 — Blocked provider raises at Django startup

**What this tests**: Configuring Google as an OAuth provider must prevent Django from starting up.

#### Setup

Create a minimal test settings file or add a temporary entry to a sandbox `settings.py`:

```python
# settings.py (sandbox)
SYNTEK_AUTH = {
    "OAUTH_PROVIDERS": [
        {"provider": "google"},
    ]
}
INSTALLED_APPS = [
    ...
    "syntek_auth",
]
```

#### Steps

1. With the sandbox running, attempt to start the Django development server:

   ```bash
   python manage.py runserver
   ```

2. Observe the output in the terminal.

#### Expected Result

- [ ] Django startup fails immediately with `django.core.exceptions.ImproperlyConfigured`
- [ ] The error message contains the word `google` (case-insensitive)
- [ ] The error message references `OAUTH_ALLOWED_PROVIDERS` or explains that Google does not
      enforce MFA at the platform level
- [ ] No request is served — startup is aborted before the server is ready

**Pass Criteria**: Server fails to start and error message is clear about the reason.

---

### Scenario 2 — Allowed provider passes startup

**What this tests**: Configuring GitHub as an OAuth provider must allow Django to start normally.

#### Setup

```python
SYNTEK_AUTH = {
    "OAUTH_PROVIDERS": [
        {"provider": "github"},
    ]
}
```

#### Steps

1. Start the Django development server.
2. Observe that startup completes without error.

#### Expected Result

- [ ] Django starts successfully
- [ ] No `ImproperlyConfigured` is raised
- [ ] The application is ready to serve requests

---

### Scenario 3 — Custom OIDC provider without certification is rejected

**What this tests**: A self-hosted OIDC provider that does not carry `mfa_enforced: True` must be
rejected.

#### Setup

```python
SYNTEK_AUTH = {
    "OAUTH_PROVIDERS": [
        {"provider": "my-company-sso"},  # no mfa_enforced key
    ]
}
```

#### Steps

1. Attempt to start Django.

#### Expected Result

- [ ] Startup fails with `ImproperlyConfigured`
- [ ] Error message names `my-company-sso` or refers to missing MFA certification

---

### Scenario 4 — Custom OIDC provider with certification passes

**What this tests**: A self-hosted OIDC provider with `mfa_enforced: True` passes.

#### Setup

```python
SYNTEK_AUTH = {
    "OAUTH_PROVIDERS": [
        {"provider": "my-company-sso", "mfa_enforced": True},
    ]
}
```

#### Steps

1. Start Django.

#### Expected Result

- [ ] Django starts successfully — no error

---

### Scenario 5 — Key versioning round-trip via Rust unit tests

**What this tests**: Ciphertexts produced by `encrypt_versioned` carry the 2-byte version prefix and
decrypt correctly across key versions.

#### Steps

1. Run the key versioning test suite:

   ```bash
   cargo test -p syntek-crypto --test key_versioning_tests
   ```

2. Observe results.

#### Expected Result

- [ ] All 27 tests pass in the green phase
- [ ] `test_encrypt_versioned_blob_starts_with_version_prefix` confirms bytes 0–1 of the decoded
      blob equal the active key version
- [ ] `test_decrypt_versioned_old_ciphertext_with_expanded_ring` confirms v1 ciphertext decrypts
      with a ring containing both v1 and v2

---

### Scenario 6 — Proxy trust settings are applied at startup

**What this tests**: `SyntekSecurityConfig.ready()` applies the three proxy-trust settings to
Django's live configuration.

#### Steps

1. In a Django shell with `syntek_security` in `INSTALLED_APPS`, inspect settings after setup:

   ```python
   import django
   from django.conf import settings
   print(settings.SECURE_PROXY_SSL_HEADER)
   print(settings.USE_X_FORWARDED_HOST)
   print(settings.SECURE_SSL_REDIRECT)
   ```

2. Verify the values.

#### Expected Result

- [ ] `SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")`
- [ ] `USE_X_FORWARDED_HOST == True`
- [ ] `SECURE_SSL_REDIRECT == True`

---

### Scenario 7 — Existing proxy settings are not overridden

**What this tests**: A project that has already set `SECURE_PROXY_SSL_HEADER` must have its value
preserved.

#### Setup

```python
# settings.py
SECURE_PROXY_SSL_HEADER = ("HTTP_X_CUSTOM_HEADER", "yes")
INSTALLED_APPS = [..., "syntek_security"]
```

#### Steps

1. Start Django and inspect `settings.SECURE_PROXY_SSL_HEADER`.

#### Expected Result

- [ ] Value remains `("HTTP_X_CUSTOM_HEADER", "yes")` — not overridden by the module default

---

## Running the Automated Test Suites

```bash
# SSO allowlist (syntek-auth)
python -m pytest packages/backend/syntek-auth/tests/test_sso_allowlist.py -v

# Proxy trust settings (syntek-security)
python -m pytest packages/backend/syntek-security/tests/test_proxy_settings.py -v

# Key versioning (syntek-crypto, Rust)
cargo test -p syntek-crypto --test key_versioning_tests

# Full Python suite
syntek-dev test --python

# Full Rust suite
syntek-dev test --rust
```

---

## Regression Checklist

Run before marking the US076 PR ready for review:

- [x] All `test_sso_allowlist.py` tests pass
- [x] All `test_proxy_settings.py` tests pass
- [x] All `key_versioning_tests.rs` tests pass
- [x] Existing `crypto_tests.rs` tests still pass (no regression to US006)
- [x] `cargo test -p syntek-pyo3` still passes
- [x] `syntek-dev lint` exits 0
- [x] `syntek-dev format --check` exits 0
- [x] `syntek-dev lint --pyright` exits 0

---

## Known Issues

No known issues at red phase.

| Issue           | Workaround     | Story |
| --------------- | -------------- | ----- |
| _{description}_ | _{workaround}_ | US076 |

---

## Reporting a Bug

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new report: `docs/BUGS/syntek-auth-{YYYY-MM-DD}.md` or
   `docs/BUGS/syntek-security-{YYYY-MM-DD}.md`
5. Reference the story: `Blocks US076`
