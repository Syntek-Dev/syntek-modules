"""GraphQL queries for authentication configuration.

Provides public-safe configuration values from Django SYNTEK_AUTH settings.
Configuration is cached to reduce database queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from django.conf import settings

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_auth.types.config import AuthConfigType


@strawberry.type
class AuthConfigQueries:
    """Queries for authentication configuration."""

    @strawberry.field
    def auth_config(self, info: Info) -> AuthConfigType:
        """Get authentication configuration.

        Returns public-safe configuration values from SYNTEK_AUTH settings.
        Does NOT expose secrets (JWT keys, encryption keys, etc.).

        This query can be called without authentication and is safe to cache
        on the client for 5-10 minutes.

        Returns:
            Authentication configuration object with all safe settings
        """
        config = getattr(settings, 'SYNTEK_AUTH', {})

        return AuthConfigType(
            # Password validation
            password_min_length=config.get('PASSWORD_LENGTH', 12),
            password_max_length=128,  # Standard maximum
            special_chars_required=config.get('SPECIAL_CHARS_REQUIRED', True),
            uppercase_required=config.get('UPPERCASE_REQUIRED', True),
            lowercase_required=config.get('LOWERCASE_REQUIRED', True),
            numbers_required=config.get('NUMBERS_REQUIRED', True),
            password_history_count=config.get('PASSWORD_HISTORY_COUNT', 5),
            common_password_check=config.get('COMMON_PASSWORD_CHECK', True),

            # Login security
            max_login_attempts=config.get('MAX_LOGIN_ATTEMPTS', 5),
            lockout_duration=config.get('LOCKOUT_DURATION', 300),
            lockout_increment=config.get('LOCKOUT_INCREMENT', True),

            # Session configuration
            session_timeout=config.get('SESSION_TIMEOUT', 1800),  # 30 minutes
            session_timeout_remember_me=config.get('SESSION_TIMEOUT_REMEMBER_ME', 2592000),  # 30 days
            session_absolute_timeout=config.get('SESSION_ABSOLUTE_TIMEOUT', 43200),  # 12 hours
            allow_simultaneous_sessions=config.get('ALLOW_SIMULTANEOUS_SESSIONS', False),

            # MFA configuration
            totp_required=config.get('TOTP_REQUIRED', False),
            totp_issuer_name=config.get('TOTP_ISSUER_NAME', 'Syntek Platform'),
            totp_window=1,  # Standard TOTP window (30 seconds before/after)
            backup_code_count=10,  # Standard backup code count
            recovery_key_count=1,  # One recovery key per user

            # WebAuthn/Passkey
            webauthn_timeout=60000,  # 60 seconds in milliseconds
            attestation_formats=['packed', 'fido-u2f', 'android-key', 'android-safetynet', 'tpm', 'apple', 'none'],

            # Session security
            fingerprint_levels=['minimal', 'balanced', 'aggressive'],
            concurrent_session_limit=3,  # Maximum 3 concurrent sessions

            # Social auth providers
            enabled_oauth_providers=config.get('ENABLED_OAUTH_PROVIDERS', [
                'google',
                'github',
                'microsoft',
            ]),

            # Notifications
            notify_failed_logins=config.get('NOTIFY_FAILED_LOGINS', True),
            notify_new_device_login=config.get('NOTIFY_NEW_DEVICE_LOGIN', True),
            log_login_attempts=config.get('LOG_LOGIN_ATTEMPTS', True),

            # Auto-logout
            auto_logout_warning_time=120,  # 2 minutes before expiry
            session_activity_check_interval=60000,  # 1 minute in milliseconds
        )
