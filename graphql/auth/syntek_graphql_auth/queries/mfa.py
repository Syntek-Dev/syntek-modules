"""GraphQL queries for MFA status information.

This module defines queries for retrieving MFA configuration status,
including TOTP devices, backup codes, and recovery keys with expiry tracking.

SECURITY FEATURES:
- User can only query their own MFA status
- Authentication required
- Expiry warnings for backup codes and recovery keys
- Comprehensive status tracking

Implements requirements:
- Phase 2.3: MFA status query with expiry information
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import AuthenticationError, ErrorCode  # type: ignore[import]
from syntek_graphql_core.utils.context import get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.mfa import MFAStatusType  # type: ignore[import]

logger = logging.getLogger(__name__)


@strawberry.type
class MFAQueries:
    """GraphQL queries for MFA status information."""

    @strawberry.field
    def mfa_status(self, info: Info) -> MFAStatusType:
        """Get comprehensive MFA status for authenticated user.

        Returns detailed information about the user's MFA configuration including
        TOTP devices, backup codes, and recovery keys with expiry tracking.

        Security Features:
        - Authentication required
        - User can only query their own MFA status
        - Expiry warnings for backup codes (< 30 days until expiry)
        - Low code warning for backup codes (< 3 remaining)
        - Expiry warnings for recovery keys (< 30 days until expiry)
        - Comprehensive attention flags for user action required

        Returns:
            MFAStatusType with complete MFA configuration status

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   mfaStatus {
            >>>     enabled
            >>>     totpEnabled
            >>>     backupCodes {
            >>>       totalCodes
            >>>       remainingCodes
            >>>       expiresAt
            >>>       lowCodeWarning
            >>>       expiryWarning
            >>>     }
            >>>     recoveryKeys {
            >>>       id
            >>>       expiresAt
            >>>       used
            >>>     }
            >>>     requiresAttention
            >>>     attentionReasons
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Import MFA service
        try:
            from syntek_authentication.services.mfa_service import (
                MFAService,  # type: ignore[import]
            )
        except ImportError:
            logger.error("MFAService not available, install syntek-authentication package")
            # Return basic MFA status with no features enabled

            return MFAStatusType(
                enabled=False,
                totp_devices=[],
                totp_enabled=False,
                backup_codes=None,
                recovery_keys=[],
                total_recovery_keys=0,
                active_recovery_keys=0,
                expired_recovery_keys=0,
                used_recovery_keys=0,
                recovery_keys_expiring_soon=False,
                oldest_recovery_key_expiry=None,
                requires_attention=False,
                attention_reasons=[],
            )

        # Get comprehensive MFA status
        mfa_status = MFAService.get_mfa_status(user)

        return MFAStatusType(
            enabled=mfa_status["enabled"],
            totp_devices=mfa_status["totp_devices"],
            totp_enabled=mfa_status["totp_enabled"],
            backup_codes=mfa_status.get("backup_codes"),
            recovery_keys=mfa_status["recovery_keys"],
            total_recovery_keys=mfa_status["total_recovery_keys"],
            active_recovery_keys=mfa_status["active_recovery_keys"],
            expired_recovery_keys=mfa_status["expired_recovery_keys"],
            used_recovery_keys=mfa_status["used_recovery_keys"],
            recovery_keys_expiring_soon=mfa_status["recovery_keys_expiring_soon"],
            oldest_recovery_key_expiry=mfa_status.get("oldest_recovery_key_expiry"),
            requires_attention=mfa_status["requires_attention"],
            attention_reasons=mfa_status["attention_reasons"],
        )
