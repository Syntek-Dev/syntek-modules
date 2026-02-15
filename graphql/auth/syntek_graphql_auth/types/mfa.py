"""GraphQL types for enhanced MFA status with expiry warnings.

This module defines types for comprehensive MFA status reporting,
including backup codes and recovery keys with expiry tracking.
"""

from __future__ import annotations

import strawberry

from syntek_graphql_auth.types.recovery import RecoveryKeyType  # type: ignore[import]
from syntek_graphql_auth.types.totp import TOTPDeviceType  # type: ignore[import]


@strawberry.type
class BackupCodeStatusType:
    """Status information for backup codes.

    Provides detailed information about backup codes including expiry and usage.

    Attributes:
        total_codes: Total number of backup codes generated
        remaining_codes: Number of unused backup codes
        used_codes: Number of used backup codes
        generated_at: When backup codes were last generated (ISO timestamp)
        expires_at: When backup codes expire (null if no expiry)
        days_until_expiry: Days remaining until expiry (null if no expiry)
        low_code_warning: Whether to warn user about low code count (< 3 remaining)
        expiry_warning: Whether to warn user about approaching expiry (< 30 days)
    """

    total_codes: int
    remaining_codes: int
    used_codes: int
    generated_at: str
    expires_at: str | None = None
    days_until_expiry: int | None = None
    low_code_warning: bool
    expiry_warning: bool


@strawberry.type
class MFAStatusType:
    """Enhanced MFA status with expiry warnings and detailed information.

    Provides comprehensive overview of user's MFA configuration including
    TOTP devices, backup codes, and recovery keys with expiry tracking.

    Attributes:
        enabled: Whether MFA is enabled (has confirmed TOTP device)
        totp_devices: List of registered TOTP devices
        totp_enabled: Whether TOTP is enabled (alias for enabled)
        backup_codes: Backup code status information
        recovery_keys: List of active recovery keys with expiry info
        total_recovery_keys: Total number of recovery keys
        active_recovery_keys: Number of active (unexpired, unused) recovery keys
        expired_recovery_keys: Number of expired recovery keys
        used_recovery_keys: Number of used recovery keys
        recovery_keys_expiring_soon: Whether any recovery keys expire in < 30 days
        oldest_recovery_key_expiry: Earliest expiry date among active recovery keys
        requires_attention: Whether user should take action (low codes, expiring keys, etc.)
        attention_reasons: List of reasons requiring attention
    """

    enabled: bool
    totp_devices: list[TOTPDeviceType]
    totp_enabled: bool  # Alias for enabled
    backup_codes: BackupCodeStatusType | None = None
    recovery_keys: list[RecoveryKeyType]
    total_recovery_keys: int
    active_recovery_keys: int
    expired_recovery_keys: int
    used_recovery_keys: int
    recovery_keys_expiring_soon: bool
    oldest_recovery_key_expiry: str | None = None
    requires_attention: bool
    attention_reasons: list[str]
