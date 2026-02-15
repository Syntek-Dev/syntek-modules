"""GraphQL types for authentication configuration.

Provides safe, public-facing authentication configuration values
from Django SYNTEK_AUTH settings.
"""

import strawberry


@strawberry.type
class AuthConfigType:
    """Authentication configuration (safe to expose to clients).

    Contains public-safe configuration values from SYNTEK_AUTH settings.
    Does NOT expose secrets (JWT keys, encryption keys, etc.).
    """

    # Password validation
    password_min_length: int
    password_max_length: int
    special_chars_required: bool
    uppercase_required: bool
    lowercase_required: bool
    numbers_required: bool
    password_history_count: int
    common_password_check: bool

    # Login security
    max_login_attempts: int
    lockout_duration: int  # seconds
    lockout_increment: bool

    # Session configuration
    session_timeout: int  # seconds (without remember me)
    session_timeout_remember_me: int  # seconds (with remember me)
    session_absolute_timeout: int  # seconds
    allow_simultaneous_sessions: bool

    # MFA configuration
    totp_required: bool
    totp_issuer_name: str
    totp_window: int
    backup_code_count: int
    recovery_key_count: int

    # WebAuthn/Passkey
    webauthn_timeout: int  # milliseconds
    attestation_formats: list[str]

    # Session security
    fingerprint_levels: list[str]
    concurrent_session_limit: int

    # Social auth providers (enabled list)
    enabled_oauth_providers: list[str]

    # Notifications
    notify_failed_logins: bool
    notify_new_device_login: bool
    log_login_attempts: bool

    # Auto-logout
    auto_logout_warning_time: int  # seconds
    session_activity_check_interval: int  # milliseconds
