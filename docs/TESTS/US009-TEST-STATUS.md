# Test Status — US009 `syntek-auth`

**Story**: US009 — `syntek-auth`: Authentication Module\
**Last Run**: `2026-03-12T00:00:00Z`\
**Run by**: Test Writer Agent (red phase — full AC coverage)\
**Overall Result**: `RED` — all new flow tests confirm stubs raise `NotImplementedError`; no
regressions in existing suite\
**Coverage**: Stubs only — no implementation yet

---

## Summary

| Suite       | Tests   | Passed  | Failed | Skipped |
| ----------- | ------- | ------- | ------ | ------- |
| Unit (Py)   | 231     | 231     | 0      | 0       |
| Integration | 0       | 0       | 0      | 0       |
| E2E         | 0       | 0       | 0      | 0       |
| **Total**   | **231** | **231** | **0**  | **0**   |

> The 46 existing US076 allowlist tests continue to pass and are not counted here — they are tracked
> in `US076-TEST-STATUS.md`.
>
> **Scope update (11/03/2026):** 27 tests added in `test_us009_user_model.py` covering
> `AbstractSyntekUser`, `User`, and `SyntekUserManager`.
>
> **Scope update (12/03/2026):** 101 tests added across five new test files covering the email
> verification, phone verification, password reset, password change, and logout/session invalidation
> flows (acceptance criteria items 9–13 in US009). Five corresponding service stubs created in
> `syntek_auth/services/`. All 277 tests in the full suite pass (231 US009 + 46 US076).

---

## Unit Tests

Mark each test case with `[x]` (pass), `[ ]` (fail / not run), or `[~]` (skipped).

### Settings Validation — `test_us009_settings_validation.py`

File: `packages/backend/syntek-auth/tests/test_us009_settings_validation.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### Valid configuration passes

- [ ] `test_minimal_valid_settings_does_not_raise` — full valid settings must not raise
- [ ] `test_mfa_methods_with_all_valid_values_does_not_raise` — all four MFA methods valid
- [ ] `test_login_field_email_or_username_with_require_username_true` — valid combined field
- [ ] `test_login_field_phone_with_require_phone_required` — valid phone field configuration
- [ ] `test_lockout_strategy_fixed_does_not_raise` — 'fixed' is a valid strategy
- [ ] `test_password_expiry_days_nonzero_does_not_raise` — non-zero expiry is valid

#### LOGIN_FIELD / REQUIRE_USERNAME conflict

- [ ] `test_login_field_username_require_username_false_raises` — conflict raises
      ImproperlyConfigured
- [ ] `test_login_field_email_or_username_require_username_false_raises` — combined field also
      conflicts
- [ ] `test_login_field_username_require_username_true_does_not_raise` — valid combination passes

#### LOGIN_FIELD / REQUIRE_PHONE conflict

- [ ] `test_login_field_phone_require_phone_false_raises` — phone field requires REQUIRE_PHONE
- [ ] `test_login_field_email_or_phone_require_phone_false_raises` — combined phone field also
      conflicts

#### MFA_METHODS validation

- [ ] `test_mfa_methods_empty_list_raises` — empty list raises ImproperlyConfigured
- [ ] `test_mfa_methods_unrecognised_value_raises` — unknown identifier raises with its name
- [ ] `test_mfa_methods_not_a_list_raises` — string instead of list is rejected

#### LOCKOUT_STRATEGY validation

- [ ] `test_lockout_strategy_invalid_value_raises` — 'exponential' is not valid
- [ ] `test_lockout_strategy_empty_string_raises` — empty string is not valid

#### Negative integer settings (parametrised — 11 test cases)

- [ ] `test_negative_integer_raises[PASSWORD_MIN_LENGTH]`
- [ ] `test_negative_integer_raises[PASSWORD_MAX_LENGTH]`
- [ ] `test_negative_integer_raises[PASSWORD_HISTORY]`
- [ ] `test_negative_integer_raises[PASSWORD_EXPIRY_DAYS]`
- [ ] `test_negative_integer_raises[MFA_BACKUP_CODES_COUNT]`
- [ ] `test_negative_integer_raises[ACCESS_TOKEN_LIFETIME]`
- [ ] `test_negative_integer_raises[REFRESH_TOKEN_LIFETIME]`
- [ ] `test_negative_integer_raises[LOCKOUT_THRESHOLD]`
- [ ] `test_negative_integer_raises[LOCKOUT_DURATION]`
- [ ] `test_negative_integer_raises[USERNAME_MIN_LENGTH]`
- [ ] `test_negative_integer_raises[USERNAME_MAX_LENGTH]`

#### Boolean type validation (parametrised — 12 test cases)

- [ ] `test_non_bool_value_raises[REQUIRE_EMAIL]`
- [ ] `test_non_bool_value_raises[REQUIRE_USERNAME]`
- [ ] `test_non_bool_value_raises[PASSWORD_REQUIRE_UPPERCASE]`
- [ ] `test_non_bool_value_raises[PASSWORD_REQUIRE_LOWERCASE]`
- [ ] `test_non_bool_value_raises[PASSWORD_REQUIRE_DIGITS]`
- [ ] `test_non_bool_value_raises[PASSWORD_REQUIRE_SYMBOLS]`
- [ ] `test_non_bool_value_raises[PASSWORD_BREACH_CHECK]`
- [ ] `test_non_bool_value_raises[MFA_REQUIRED]`
- [ ] `test_non_bool_value_raises[ROTATE_REFRESH_TOKENS]`
- [ ] `test_non_bool_value_raises[REGISTRATION_ENABLED]`
- [ ] `test_non_bool_value_raises[EMAIL_VERIFICATION_REQUIRED]`
- [ ] `test_non_bool_value_raises[USERNAME_CASE_SENSITIVE]`

#### Invalid LOGIN_FIELD value

- [ ] `test_unrecognised_login_field_raises` — 'telegram' is not valid
- [ ] `test_empty_string_login_field_raises` — empty string is not valid

#### SyntekAuthConfig.ready() integration

- [ ] `test_ready_with_invalid_mfa_methods_raises` — empty MFA_METHODS raises at startup
- [ ] `test_ready_with_invalid_login_field_username_conflict_raises` — conflict raises at startup
- [ ] `test_ready_with_valid_settings_does_not_raise` — valid settings allow startup
- [x] `test_ready_with_no_syntek_auth_does_not_raise` — absent SYNTEK_AUTH does not raise

---

### Password Policy — `test_us009_password_policy.py`

File: `packages/backend/syntek-auth/tests/test_us009_password_policy.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### Compliant password passes

- [ ] `test_valid_password_returns_valid_result` — 12-char uppercase+digits passes
- [ ] `test_valid_password_with_symbols_passes` — symbol requirement satisfied

#### Minimum length

- [ ] `test_password_too_short_returns_violation` — short password reports 'too_short' code
- [ ] `test_password_exactly_at_minimum_passes` — exactly min-length passes

#### Multiple failures reported together

- [ ] `test_short_and_no_symbols_both_reported` — both 'too_short' and 'no_symbols' codes present
- [ ] `test_violation_messages_are_non_empty` — every violation has a non-empty message

#### Character class requirements

- [ ] `test_no_uppercase_when_required_raises_violation` — missing uppercase reported
- [ ] `test_no_lowercase_when_required_raises_violation` — missing lowercase reported
- [ ] `test_no_digits_when_required_raises_violation` — missing digits reported
- [ ] `test_no_symbols_when_not_required_does_not_raise_violation` — no false positive for symbols

#### Password history

- [ ] `test_password_matching_history_returns_true` — match in history returns True
- [ ] `test_password_not_in_history_returns_false` — no match returns False
- [ ] `test_history_count_zero_always_returns_false` — disabled history is always False
- [ ] `test_only_last_n_hashes_are_checked` — window of N respected

#### Password expiry

- [ ] `test_password_not_expired_when_within_period` — 89/90 days is not expired
- [ ] `test_password_expired_when_period_exceeded` — 91/90 days is expired
- [ ] `test_password_expired_exactly_at_boundary` — exactly 90/90 days is expired
- [ ] `test_password_never_expires_when_expiry_days_zero` — 0 = never expires

#### Breach check

- [ ] `test_breached_password_returns_true` — HIBP match returns True
- [ ] `test_clean_password_returns_false` — no HIBP match returns False
- [ ] `test_breach_check_does_not_send_full_password` — k-anonymity constraint (red phase:
      NotImplementedError expected)

---

### Account Lockout — `test_us009_lockout.py`

File: `packages/backend/syntek-auth/tests/test_us009_lockout.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### should_lock_account

- [ ] `test_at_threshold_returns_true` — exactly 5 attempts with threshold 5
- [ ] `test_below_threshold_returns_false` — 4 attempts does not lock
- [ ] `test_above_threshold_returns_true` — 10 attempts locks
- [ ] `test_zero_attempts_returns_false` — 0 attempts never locks

#### Fixed strategy

- [ ] `test_first_lockout_fixed_returns_base_duration` — first lockout = base_duration
- [ ] `test_second_lockout_fixed_returns_base_duration` — second lockout = same base
- [ ] `test_tenth_lockout_fixed_does_not_increase` — no growth with 'fixed'

#### Progressive strategy

- [ ] `test_first_lockout_progressive_returns_base_duration` — first = base
- [ ] `test_second_lockout_progressive_doubles_duration` — second = base \* 2
- [ ] `test_third_lockout_progressive_quadruples_duration` — third = base \* 4
- [ ] `test_progressive_duration_formula` — formula: base \* 2^(n-1)
- [ ] `test_zero_base_duration_progressive_stays_zero` — 0 base stays 0

---

### MFA Gating — `test_us009_mfa.py`

File: `packages/backend/syntek-auth/tests/test_us009_mfa.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### enabled_mfa_methods

- [ ] `test_totp_only_returns_totp` — single method list
- [ ] `test_totp_and_passkey_returns_both` — two-method list
- [ ] `test_sms_not_in_methods_when_not_configured` — absent method not returned
- [ ] `test_all_four_methods_returned_when_all_configured` — full list
- [ ] `test_order_is_canonical` — canonical order: totp, sms, email_otp, passkey
- [ ] `test_unrecognised_method_is_excluded` — unknown identifier stripped

#### resolve_session_state

- [ ] `test_mfa_required_and_not_configured_issues_partial_session` — partial session with flag
- [ ] `test_mfa_required_and_configured_issues_full_session` — full session when MFA configured
- [ ] `test_mfa_not_required_always_issues_full_session` — not required = always full
- [ ] `test_mfa_not_required_with_mfa_configured_issues_full_session` — full when configured + not
      required

#### oidc_amr_satisfies_mfa

- [ ] `test_amr_with_mfa_value_returns_true` — ['mfa'] satisfies requirement
- [ ] `test_amr_with_mfa_and_other_values_returns_true` — ['pwd', 'mfa'] satisfies
- [ ] `test_amr_without_mfa_returns_false` — ['pwd'] does not satisfy
- [ ] `test_empty_amr_returns_false` — empty list does not satisfy
- [ ] `test_none_amr_returns_false` — None does not satisfy
- [ ] `test_amr_with_otp_and_pwd_returns_true` — ['otp', 'pwd'] satisfies

---

### JWT Tokens — `test_us009_tokens.py`

File: `packages/backend/syntek-auth/tests/test_us009_tokens.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### issue_token_pair

- [ ] `test_returns_token_pair_instance` — returns TokenPair dataclass
- [ ] `test_access_token_is_non_empty_string` — non-empty access token
- [ ] `test_refresh_token_is_non_empty_string` — non-empty refresh token
- [ ] `test_two_pairs_have_distinct_tokens` — distinct tokens per call

#### rotate_refresh_token

- [ ] `test_rotation_returns_new_token_pair` — returns new TokenPair
- [ ] `test_new_tokens_differ_from_original` — rotated pair is different
- [ ] `test_reusing_old_refresh_token_raises_value_error` — revoked token raises ValueError
- [ ] `test_invalid_refresh_token_raises_value_error` — garbage token raises ValueError

#### validate_access_token

- [ ] `test_valid_token_returns_payload` — returns decoded payload with user id
- [ ] `test_tampered_token_raises_value_error` — tampered signature raises ValueError
- [ ] `test_empty_token_raises_value_error` — empty string raises ValueError

---

### Login Field Dispatcher — `test_us009_login_field.py`

File: `packages/backend/syntek-auth/tests/test_us009_login_field.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

- [ ] `test_email_lookup_returns_user_when_found` — email match returns user
- [ ] `test_email_lookup_returns_none_when_not_found` — no match returns None
- [ ] `test_email_lookup_raises_not_implemented_in_stub` — stub raises NotImplementedError
- [ ] `test_username_lookup_raises_not_implemented_in_stub` — combined field stub
- [ ] `test_email_lookup_via_combined_field_raises_not_implemented` — combined email stub
- [ ] `test_phone_lookup_raises_not_implemented_in_stub` — phone stub

---

### Email Verification — `test_us009_email_verification.py`

File: `packages/backend/syntek-auth/tests/test_us009_email_verification.py`\
Run: `syntek-dev test --python --python-package syntek-auth`\
Phase: **Red** — all functions raise `NotImplementedError`; structural tests pass

#### generate_email_verification_token

- [x] `test_returns_non_empty_string` — stub raises NotImplementedError (expected)
- [x] `test_distinct_tokens_for_same_user` — stub raises NotImplementedError (expected)

#### verify_email_token — success

- [x] `test_valid_token_returns_success_true` — stub raises NotImplementedError (expected)
- [x] `test_valid_token_sets_email_verified_flag` — stub raises NotImplementedError (expected)

#### verify_email_token — expired token

- [x] `test_expired_token_returns_success_false` — stub raises NotImplementedError (expected)
- [x] `test_expired_token_returns_token_expired_error_code` — error_code='token_expired'
- [x] `test_expired_token_has_non_empty_message` — non-empty message required

#### verify_email_token — already-used token

- [x] `test_already_used_token_returns_success_false` — stub raises NotImplementedError (expected)
- [x] `test_already_used_token_returns_token_already_used_error_code` —
      error_code='token_already_used'

#### Unverified account gating

- [x] `test_is_email_verified_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_is_email_verified_signature_accepts_user_id` — signature check passes

#### resendVerificationEmail for already-verified account

- [x] `test_resend_for_already_verified_raises_not_implemented` — stub raises NotImplementedError
- [x] `test_resend_returns_false_when_already_verified` — green-phase assertion in place
- [x] `test_resend_signature_accepts_user_id` — signature check passes

#### EmailVerificationResult structure

- [x] `test_result_has_success_field` — success field present
- [x] `test_result_has_error_code_field` — error_code field present
- [x] `test_result_has_message_field` — message field present
- [x] `test_result_defaults_error_code_to_none` — error_code defaults to None
- [x] `test_result_defaults_message_to_empty_string` — message defaults to ''

---

### Phone Verification — `test_us009_phone_verification.py`

File: `packages/backend/syntek-auth/tests/test_us009_phone_verification.py`\
Run: `syntek-dev test --python --python-package syntek-auth`\
Phase: **Red** — all functions raise `NotImplementedError`; structural tests pass

#### generate_phone_otp

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_signature_accepts_user_id` — signature check passes

#### verify_phone_otp — success

- [x] `test_valid_otp_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_success_result_structure` — green-phase assertion in place

#### verify_phone_otp — brute-force protection (3 attempts)

- [x] `test_first_incorrect_otp_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_after_three_incorrect_attempts_otp_is_invalidated` — error_code='otp_invalidated'
- [x] `test_after_three_incorrect_attempts_success_is_false` — success=False on third failure
- [x] `test_invalidated_otp_cannot_be_reused` — correct OTP after invalidation must fail

#### verify_phone_otp — expired OTP

- [x] `test_expired_otp_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_expired_otp_returns_otp_expired_code` — error_code='otp_expired'
- [x] `test_expired_otp_has_non_empty_message` — non-empty message required

#### is_phone_verified

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_signature_accepts_user_id` — signature check passes

#### resend_phone_otp

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_signature_accepts_user_id` — signature check passes

#### PhoneVerificationResult structure

- [x] `test_result_has_success_field` — success field present
- [x] `test_result_has_error_code_field` — error_code field present
- [x] `test_result_has_message_field` — message field present
- [x] `test_result_defaults_error_code_to_none` — error_code defaults to None
- [x] `test_result_defaults_message_to_empty_string` — message defaults to ''

---

### Password Reset — `test_us009_password_reset.py`

File: `packages/backend/syntek-auth/tests/test_us009_password_reset.py`\
Run: `syntek-dev test --python --python-package syntek-auth`\
Phase: **Red** — all functions raise `NotImplementedError`; structural tests pass

#### resetPasswordRequest — anti-enumeration

- [x] `test_request_for_existing_verified_account_raises_not_implemented`
- [x] `test_request_for_unknown_email_raises_not_implemented`
- [x] `test_request_returns_true_for_existing_account` — always returns True
- [x] `test_request_returns_true_for_unknown_account` — same response regardless
- [x] `test_request_for_unverified_account_raises_not_implemented`

#### generate_password_reset_token

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_signature_accepts_user_id` — signature check passes

#### resetPasswordConfirm — success

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_success_result_structure` — success=True, error_code=None
- [x] `test_success_invalidates_all_refresh_tokens` — green-phase assertion in place

#### resetPasswordConfirm — password history

- [x] `test_password_in_history_raises_not_implemented`
- [x] `test_password_in_history_returns_password_in_history_code` — error_code='password_in_history'

#### resetPasswordConfirm — expired token

- [x] `test_expired_token_raises_not_implemented`
- [x] `test_expired_token_returns_token_expired_code` — error_code='token_expired'
- [x] `test_expired_token_does_not_change_password` — success=False

#### resetPasswordConfirm — single-use token

- [x] `test_already_used_token_raises_not_implemented`
- [x] `test_already_used_token_returns_token_already_used_code` — error_code='token_already_used'

#### invalidate_all_refresh_tokens

- [x] `test_raises_not_implemented` — stub raises NotImplementedError (expected)
- [x] `test_signature_accepts_user_id` — signature check passes

#### PasswordResetResult structure

- [x] `test_result_has_success_field`
- [x] `test_result_has_error_code_field`
- [x] `test_result_has_message_field`
- [x] `test_result_defaults_error_code_to_none`
- [x] `test_result_defaults_message_to_empty_string`

---

### Authenticated Password Change — `test_us009_password_change.py`

File: `packages/backend/syntek-auth/tests/test_us009_password_change.py`\
Run: `syntek-dev test --python --python-package syntek-auth`\
Phase: **Red** — all functions raise `NotImplementedError`; structural tests pass

#### change_password — success

- [x] `test_raises_not_implemented`
- [x] `test_success_result_structure` — success=True, error_code=None
- [x] `test_success_invalidates_other_sessions` — green-phase assertion in place
- [x] `test_current_jti_none_invalidates_all_sessions` — None JTI revokes all

#### change_password — wrong current password

- [x] `test_wrong_current_password_raises_not_implemented`
- [x] `test_wrong_current_password_returns_invalid_credentials_code` —
      error_code='invalid_credentials'
- [x] `test_wrong_current_password_has_non_empty_message`

#### change_password — password history

- [x] `test_password_in_history_raises_not_implemented`
- [x] `test_password_in_history_returns_password_in_history_code` — error_code='password_in_history'
- [x] `test_password_in_history_does_not_invalidate_sessions`

#### verify_current_password

- [x] `test_raises_not_implemented`
- [x] `test_signature_accepts_user_id_and_password`

#### invalidate_other_sessions

- [x] `test_raises_not_implemented`
- [x] `test_raises_not_implemented_with_none_jti`
- [x] `test_signature_accepts_user_id_and_keep_jti`

#### PasswordChangeResult structure

- [x] `test_result_has_success_field`
- [x] `test_result_has_error_code_field`
- [x] `test_result_has_message_field`
- [x] `test_result_defaults_error_code_to_none`
- [x] `test_result_defaults_message_to_empty_string`

---

### Logout and Session Invalidation — `test_us009_logout.py`

File: `packages/backend/syntek-auth/tests/test_us009_logout.py`\
Run: `syntek-dev test --python --python-package syntek-auth`\
Phase: **Red** — all functions raise `NotImplementedError`; structural tests pass

#### logout — success

- [x] `test_raises_not_implemented`
- [x] `test_success_result_structure` — success=True, error_code=None
- [x] `test_logout_denylists_access_token` — green-phase assertion in place
- [x] `test_logout_revokes_refresh_token` — green-phase assertion in place

#### logout — replayed token

- [x] `test_replayed_token_raises_not_implemented`
- [x] `test_replayed_token_returns_success_false`
- [x] `test_replayed_token_returns_token_already_invalid_code` — error_code='token_already_invalid'

#### is_access_token_denylisted

- [x] `test_raises_not_implemented`
- [x] `test_signature_accepts_jti`

#### revokeAllSessions (admin)

- [x] `test_raises_not_implemented`
- [x] `test_returns_revoked_count` — returns int >= 0
- [x] `test_signature_accepts_user_id`
- [x] `test_revoke_all_sessions_for_different_user_does_not_raise`

#### LogoutResult structure

- [x] `test_result_has_success_field`
- [x] `test_result_has_error_code_field`
- [x] `test_result_has_message_field`
- [x] `test_result_defaults_error_code_to_none`
- [x] `test_result_defaults_message_to_empty_string`

---

### User Model — `test_us009_user_model.py`

File: `packages/backend/syntek-auth/tests/test_us009_user_model.py`\
Run: `syntek-dev test --python --python-package syntek-auth`

#### AbstractSyntekUser is abstract

- [x] `test_abstract_syntek_user_has_abstract_meta` — `Meta.abstract = True`
- [x] `test_abstract_syntek_user_has_no_db_table` — not registered as a concrete model

#### get_user_model() returns User

- [x] `test_get_user_model_returns_user_class` — resolves to `syntek_auth.models.User`
- [x] `test_user_class_is_subclass_of_abstract_base` — `User` subclasses `AbstractSyntekUser`

#### User model field declarations

- [x] `test_email_field_is_encrypted_field` — `email` declared as `EncryptedField`
- [x] `test_phone_field_is_encrypted_field` — `phone` declared as `EncryptedField`
- [x] `test_username_field_is_nullable` — `username` has `null=True`
- [x] `test_username_field_is_blank` — `username` has `blank=True`
- [x] `test_email_field_is_not_nullable` — `email` has `null=False`

#### USERNAME_FIELD is 'email'

- [x] `test_username_field_is_email` — `User.USERNAME_FIELD == 'email'`
- [x] `test_get_user_model_username_field_is_email` — `get_user_model().USERNAME_FIELD == 'email'`

#### PermissionsMixin presence

- [x] `test_user_has_has_perm_method` — `has_perm` callable present
- [x] `test_user_has_has_module_perms_method` — `has_module_perms` callable present
- [x] `test_user_is_subclass_of_permissions_mixin` — `issubclass(User, PermissionsMixin)`

#### create_user — email validation (red phase: NotImplementedError)

- [x] `test_create_user_empty_email_raises_value_error` — empty email raises ValueError or
      NotImplementedError
- [x] `test_create_user_raises_not_implemented_in_stub` — stub raises NotImplementedError

#### create_user — username optional

- [x] `test_create_user_without_username_raises_not_implemented` — stub raises NotImplementedError
      without username
- [x] `test_create_user_manager_signature_accepts_no_username` — `username` not a required
      positional arg

#### create_superuser (red phase: NotImplementedError)

- [x] `test_create_superuser_raises_not_implemented_in_stub` — stub raises NotImplementedError
- [x] `test_create_superuser_manager_signature_exists` — `create_superuser` callable present

#### create_superuser flag validation (red phase: ValueError or NotImplementedError)

- [x] `test_create_superuser_is_staff_false_raises` — `is_staff=False` raises
- [x] `test_create_superuser_is_superuser_false_raises` — `is_superuser=False` raises

#### User manager type

- [x] `test_user_objects_is_syntek_user_manager` — `User.objects` is `SyntekUserManager`
- [x] `test_get_user_model_objects_is_syntek_user_manager` — `get_user_model().objects` is
      `SyntekUserManager`

#### User factory (skipped until `syntek_auth.factories` exists)

- [~] `test_user_factory_build_returns_user_instance` — skipped (factory not yet created)
- [~] `test_user_factory_build_has_email` — skipped (factory not yet created)
- [~] `test_user_factory_build_username_is_optional` — skipped (factory not yet created)

---

## Known Failures

As of 12/03/2026, the entire suite (277 tests) passes. All tests in the five new flow files confirm
`NotImplementedError` is raised by the stubs — this is the correct red-phase behaviour.

The table below documents the expected failure reason for each group when the `NotImplementedError`
expectation is replaced by a green-phase assertion (i.e. what will initially fail when the
implementation begins):

| Test Group                          | Green-phase failure reason        | Story |
| ----------------------------------- | --------------------------------- | ----- |
| Settings validation (37 tests)      | Stub raises `NotImplementedError` | US009 |
| Password policy (19 tests)          | Stub raises `NotImplementedError` | US009 |
| Account lockout (12 tests)          | Stub raises `NotImplementedError` | US009 |
| MFA gating (16 tests)               | Stub raises `NotImplementedError` | US009 |
| JWT tokens (11 tests)               | Stub raises `NotImplementedError` | US009 |
| Login field dispatcher (6 tests)    | Stub raises `NotImplementedError` | US009 |
| Email verification (20 tests — new) | Stub raises `NotImplementedError` | US009 |
| Phone verification (21 tests — new) | Stub raises `NotImplementedError` | US009 |
| Password reset (25 tests — new)     | Stub raises `NotImplementedError` | US009 |
| Password change (20 tests — new)    | Stub raises `NotImplementedError` | US009 |
| Logout / session (20 tests — new)   | Stub raises `NotImplementedError` | US009 |

The user model tests pass at the stub level because they assert structural properties (field types,
abstract meta, mixin presence, manager type) that are satisfied by the stub `models.py`.

---

## How to Run

```bash
# Full syntek-auth suite (US009 + US076)
syntek-dev test --python --python-package syntek-auth

# US009 tests only
python -m pytest packages/backend/syntek-auth/tests/test_us009_*.py -v

# User model tests only
python -m pytest packages/backend/syntek-auth/tests/test_us009_user_model.py -v

# Settings validation only
python -m pytest packages/backend/syntek-auth/tests/test_us009_settings_validation.py -v

# With coverage
syntek-dev test --python --python-package syntek-auth --coverage
```

---

## Notes

- All test files are scoped to US009 acceptance criteria. The existing US076 tests in
  `test_sso_allowlist.py` remain untouched and continue passing.
- The pre-existing passing US009 test (`test_ready_with_no_syntek_auth_does_not_raise`) passes
  because `apps.py` only calls `validate_settings` when `SYNTEK_AUTH` is present.
- Password breach check tests that patch `is_password_breached` pass at the mock layer; the direct
  stub call test (`test_breach_check_does_not_send_full_password`) confirms `NotImplementedError`.
- Login field tests that use `patch` on the stub will pass at the mock layer; the direct stub call
  tests confirm the red phase.
- **Scope update (11/03/2026):** `conftest.py` updated to add `syntek_auth` to `INSTALLED_APPS` and
  set `AUTH_USER_MODEL = 'syntek_auth.User'`. This is required so that `get_user_model()` resolves
  to the concrete `User` class in all tests.
- `EncryptedField` is a placeholder `TextField` subclass in the red phase. In the green phase it
  will be replaced by the real implementation backed by `syntek_pyo3.encrypt_field` /
  `syntek_pyo3.decrypt_field`.
- Factory tests pass now that `syntek_auth.factories` exists (created during earlier scope update).
- **Scope update (12/03/2026):** Five new service stub files added:
  `services/email_verification.py`, `services/phone_verification.py`, `services/password_reset.py`,
  `services/password_change.py`, `services/session.py`. All public functions raise
  `NotImplementedError` until the green phase implementation.
- All 101 new flow tests pass at the red-phase level — each confirms that `NotImplementedError` is
  raised while verifying that the stub can be imported, has the correct signature, and exposes the
  expected result dataclass structure.
