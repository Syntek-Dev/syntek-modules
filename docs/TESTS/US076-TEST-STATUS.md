# Test Status — US076 Security Policy

**Story**: US076 — Security Policy: MFA-Enforcing SSO, Key Rotation, and Network Architecture\
**Last Run**: `2026-03-11T00:00:00Z`\
**Run by**: Backend Agent (green phase)\
**Overall Result**: `PASS` — all 77 tests passing\
**Coverage**: Implementation complete for all tested units

---

## Summary

| Suite       | Tests  | Passed | Failed | Skipped |
| ----------- | ------ | ------ | ------ | ------- |
| Unit (Rust) | 27     | 27     | 0      | 0       |
| Unit (Py)   | 50     | 50     | 0      | 0       |
| Integration | 0      | 0      | 0      | 0       |
| E2E         | 0      | 0      | 0      | 0       |
| **Total**   | **77** | **77** | **0**  | **0**   |

---

## Rust Tests — `syntek-crypto` (key versioning)

File: `rust/syntek-crypto/tests/key_versioning_tests.rs`\
Run: `cargo test -p syntek-crypto --test key_versioning_tests`

### KeyVersion byte serialisation

- [x] `test_key_version_to_bytes_big_endian` — KeyVersion(1) serialises to [0x00, 0x01]
- [x] `test_key_version_to_bytes_256` — KeyVersion(256) serialises to [0x01, 0x00]
- [x] `test_key_version_from_bytes_roundtrip` — from_bytes(to_bytes(v)) == v for all u16 values

### KeyRing construction and active key

- [x] `test_keyring_new_is_empty` — new KeyRing must have len 0
- [x] `test_keyring_add_single_key_len_is_one` — ring has len 1 after one add
- [x] `test_keyring_active_returns_only_entry` — active() returns the sole entry
- [x] `test_keyring_active_returns_highest_version` — active() returns highest version number
- [x] `test_keyring_active_empty_ring_returns_error` — active() on empty ring → InvalidInput
- [x] `test_keyring_get_known_version_returns_key_bytes` — get(v1) and get(v2) return correct bytes
- [x] `test_keyring_get_unknown_version_returns_error` — get(99) → InvalidInput
- [x] `test_keyring_add_wrong_key_length_returns_error` — 16-byte key → InvalidInput

### encrypt_versioned / decrypt_versioned round-trip

- [x] `test_encrypt_decrypt_versioned_roundtrip_single_key` — round-trip with v1-only ring
- [x] `test_encrypt_decrypt_versioned_roundtrip_two_key_ring_uses_active` — uses highest version

### Version prefix in ciphertext blob

- [x] `test_encrypt_versioned_blob_starts_with_version_prefix` — bytes [0..2] == KeyVersion(1) for
      v1 ring
- [x] `test_encrypt_versioned_blob_prefix_reflects_active_version_2` — bytes [0..2] == KeyVersion(2)
      for v2 ring
- [x] `test_encrypt_versioned_blob_has_correct_byte_layout` — 2 version + 12 nonce + plaintext + 16
      tag

### Cross-version decryption

- [x] `test_decrypt_versioned_old_ciphertext_with_expanded_ring` — v1 ciphertext decrypts with v1+v2
      ring
- [x] `test_decrypt_versioned_unknown_version_returns_error` — v2 ciphertext rejected by v1-only
      ring

### Error cases

- [x] `test_encrypt_versioned_empty_ring_returns_error` — InvalidInput on empty ring
- [x] `test_decrypt_versioned_tampered_ciphertext_returns_decryption_error` — GCM tag failure →
      DecryptionError
- [x] `test_decrypt_versioned_invalid_base64_returns_error` — bad base64 → DecryptionError
- [x] `test_decrypt_versioned_blob_too_short_returns_error` — 1-byte blob → error
- [x] `test_decrypt_versioned_aad_mismatch_returns_error` — wrong model → DecryptionError

### reencrypt_to_active

- [x] `test_reencrypt_to_active_already_current_returns_unchanged` — no-op when already at active
      version
- [x] `test_reencrypt_to_active_migrates_old_version_to_current` — v1 ciphertext re-encrypted under
      v2
- [x] `test_reencrypt_to_active_unknown_version_returns_error` — missing key → error

### Nonce uniqueness

- [x] `test_encrypt_versioned_nonce_uniqueness_1000_encryptions` — 1,000 encryptions produce 1,000
      distinct nonces

---

## Python Tests — `syntek-auth` (SSO allowlist)

File: `packages/backend/syntek-auth/tests/test_sso_allowlist.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

### Blocked providers raise ImproperlyConfigured

- [x] `test_blocked_provider_raises_improperly_configured[google]`
- [x] `test_blocked_provider_raises_improperly_configured[facebook]`
- [x] `test_blocked_provider_raises_improperly_configured[instagram]`
- [x] `test_blocked_provider_raises_improperly_configured[linkedin]`
- [x] `test_blocked_provider_raises_improperly_configured[twitter]`
- [x] `test_blocked_provider_raises_improperly_configured[x]`
- [x] `test_blocked_provider_raises_improperly_configured[apple]`
- [x] `test_blocked_provider_raises_improperly_configured[discord]`
- [x] `test_blocked_provider_raises_improperly_configured[microsoft]`
- [x] `test_google_blocked_names_provider_in_message` — error message names 'google'
- [x] `test_facebook_blocked_raises_improperly_configured`
- [x] `test_discord_blocked_raises_improperly_configured`
- [x] `test_twitter_blocked_raises_improperly_configured`
- [x] `test_error_message_includes_docs_reference` — message references OAUTH_ALLOWED_PROVIDERS
- [x] `test_blocked_provider_mixed_case_is_rejected` — 'Google' normalised and rejected
- [x] `test_first_blocked_provider_fails_fast` — first blocked provider named in error

### Allowed built-in providers pass

- [x] `test_allowed_provider_does_not_raise[github]`
- [x] `test_allowed_provider_does_not_raise[gitlab]`
- [x] `test_allowed_provider_does_not_raise[okta]`
- [x] `test_allowed_provider_does_not_raise[entra]`
- [x] `test_allowed_provider_does_not_raise[azure_ad]`
- [x] `test_allowed_provider_does_not_raise[authentik]`
- [x] `test_allowed_provider_does_not_raise[keycloak]`
- [x] `test_allowed_provider_does_not_raise[defguard]`
- [x] `test_github_allowed_does_not_raise`
- [x] `test_okta_allowed_does_not_raise`
- [x] `test_entra_allowed_does_not_raise`
- [x] `test_multiple_allowed_providers_pass`

### Custom / self-hosted OIDC providers

- [x] `test_custom_provider_without_mfa_enforced_raises`
- [x] `test_custom_provider_with_mfa_enforced_false_raises`
- [x] `test_custom_provider_with_mfa_enforced_true_passes`
- [x] `test_defguard_self_hosted_with_mfa_enforced_true_passes`
- [x] `test_mixed_valid_and_invalid_custom_providers_raises`

### Empty / missing provider list

- [x] `test_empty_providers_list_does_not_raise`
- [x] `test_missing_oauth_providers_key_does_not_raise`

### SyntekAuthConfig.ready()

- [x] `test_ready_with_blocked_provider_raises_improperly_configured`
- [x] `test_ready_with_allowed_provider_does_not_raise`
- [x] `test_ready_with_no_syntek_auth_setting_does_not_raise`

---

## Python Tests — `syntek-security` (proxy trust settings)

File: `packages/backend/syntek-security/tests/test_proxy_settings.py`\
Run: `syntek-dev test --python --python-package syntek-security`

### apply_proxy_settings injects required settings

- [x] `test_sets_secure_proxy_ssl_header`
- [x] `test_secure_proxy_ssl_header_value_is_correct_tuple` — must be ("HTTP_X_FORWARDED_PROTO",
      "https")
- [x] `test_sets_use_x_forwarded_host_true`
- [x] `test_sets_secure_ssl_redirect_true`
- [x] `test_all_three_settings_applied_in_single_call`

### Existing project settings not overridden

- [x] `test_does_not_override_existing_secure_proxy_ssl_header`
- [x] `test_does_not_override_existing_use_x_forwarded_host`
- [x] `test_does_not_override_existing_secure_ssl_redirect`
- [x] `test_idempotent_second_call_does_not_raise`

### SyntekSecurityConfig.ready()

- [x] `test_ready_sets_secure_proxy_ssl_header`
- [x] `test_ready_sets_use_x_forwarded_host`
- [x] `test_ready_sets_secure_ssl_redirect`

---

## Known Failures

None — all tests pass in the green phase.

---

## How to Run

```bash
# All Rust key versioning tests
cargo test -p syntek-crypto --test key_versioning_tests

# Python SSO allowlist tests
syntek-dev test --python --python-package syntek-auth

# Python proxy settings tests
syntek-dev test --python --python-package syntek-security

# Everything at once
syntek-dev test --rust
syntek-dev test --python
```

---

## Notes

- `apply_proxy_settings` uses `settings._wrapped.__dict__` to detect whether a setting was
  explicitly configured by the consuming project, rather than `hasattr`. Django's `LazySettings`
  exposes global-settings defaults via `hasattr` (e.g. `SECURE_PROXY_SSL_HEADER = None`) but only
  project-configured values appear in `_wrapped.__dict__`. This distinction ensures Syntek defaults
  are applied when the project has not overridden them, while project-level overrides are always
  respected.
- The parametrised `test_blocked_provider_raises_improperly_configured` test runs once for each
  entry in `BLOCKED_PROVIDERS` (9 providers).
- The parametrised `test_allowed_provider_does_not_raise` runs once for each entry in
  `BUILTIN_ALLOWED_PROVIDERS` (8 providers).
- Key rotation Celery task tests are deferred to a separate story task once `syntek-tasks` is
  available as a dependency (see US076 task list).
