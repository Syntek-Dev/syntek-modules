"""Public service exports for ``syntek-auth``.

Re-exports all public service functions and data classes from the services
subpackage so that internal callers can use a single stable import path.
"""

from __future__ import annotations

from syntek_auth.services.email_verification import (
    EmailVerificationResult,
    generate_email_verification_token,
    is_email_verified,
    resend_verification_email,
    verify_email_token,
)
from syntek_auth.services.lockout import (
    LockoutState,
    compute_lockout_duration,
    should_lock_account,
)
from syntek_auth.services.lookup_tokens import (
    make_email_token,
    make_phone_token,
    make_totp_secret_token,
    make_username_token,
)
from syntek_auth.services.mfa import (
    MfaSessionState,
    enabled_mfa_methods,
    oidc_amr_satisfies_mfa,
    resolve_session_state,
)
from syntek_auth.services.oauth_mfa import (
    OAuthMfaCompleteResult,
    OAuthMfaPendingResult,
    complete_oauth_mfa,
    issue_oauth_pending_session,
)
from syntek_auth.services.oidc import (
    OidcProviderConfig,
    OidcTokenClaims,
    build_auth_url,
    discover_provider,
    exchange_code,
    generate_nonce,
    generate_state,
    get_provider_config,
    validate_id_token,
)
from syntek_auth.services.password import (
    PasswordPolicyResult,
    PolicyViolation,
    check_password_history,
    is_password_breached,
    is_password_expired,
    validate_password_policy,
)
from syntek_auth.services.password_change import (
    PasswordChangeResult,
    change_password,
    invalidate_other_sessions,
    verify_current_password,
)
from syntek_auth.services.password_reset import (
    PasswordResetResult,
    confirm_password_reset,
    generate_password_reset_token,
    invalidate_all_refresh_tokens,
    request_password_reset,
)
from syntek_auth.services.phone_verification import (
    PhoneVerificationResult,
    generate_phone_otp,
    is_phone_verified,
    resend_phone_otp,
    verify_phone_otp,
)
from syntek_auth.services.session import (
    LogoutResult,
    is_access_token_denylisted,
    logout,
    revoke_all_sessions,
)
from syntek_auth.services.tokens import (
    TokenPair,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
    validate_access_token,
)
from syntek_auth.services.totp import (
    TotpSetupData,
    build_provisioning_uri,
    consume_backup_code,
    enable_totp_for_user,
    generate_backup_codes,
    generate_totp_secret,
    store_backup_codes,
    verify_totp_code,
)

__all__ = [
    "EmailVerificationResult",
    "LockoutState",
    "LogoutResult",
    "MfaSessionState",
    "OAuthMfaCompleteResult",
    "OAuthMfaPendingResult",
    "OidcProviderConfig",
    "OidcTokenClaims",
    "PasswordChangeResult",
    "PasswordPolicyResult",
    "PasswordResetResult",
    "PhoneVerificationResult",
    "PolicyViolation",
    "TokenPair",
    "TotpSetupData",
    "build_auth_url",
    "build_provisioning_uri",
    "change_password",
    "check_password_history",
    "complete_oauth_mfa",
    "compute_lockout_duration",
    "confirm_password_reset",
    "consume_backup_code",
    "discover_provider",
    "enable_totp_for_user",
    "enabled_mfa_methods",
    "exchange_code",
    "generate_backup_codes",
    "generate_email_verification_token",
    "generate_nonce",
    "generate_password_reset_token",
    "generate_phone_otp",
    "generate_state",
    "generate_totp_secret",
    "get_provider_config",
    "invalidate_all_refresh_tokens",
    "invalidate_other_sessions",
    "is_access_token_denylisted",
    "is_email_verified",
    "is_password_breached",
    "is_password_expired",
    "is_phone_verified",
    "issue_oauth_pending_session",
    "issue_token_pair",
    "logout",
    "make_email_token",
    "make_phone_token",
    "make_totp_secret_token",
    "make_username_token",
    "oidc_amr_satisfies_mfa",
    "request_password_reset",
    "resend_phone_otp",
    "resend_verification_email",
    "resolve_session_state",
    "revoke_all_sessions",
    "revoke_refresh_token",
    "rotate_refresh_token",
    "should_lock_account",
    "store_backup_codes",
    "validate_access_token",
    "validate_id_token",
    "validate_password_policy",
    "verify_current_password",
    "verify_email_token",
    "verify_phone_otp",
    "verify_totp_code",
]
