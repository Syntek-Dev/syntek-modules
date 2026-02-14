"""GraphQL mutations for session security operations.

This module defines mutations for session security monitoring, including:
- Session fingerprinting and device tracking
- Suspicious activity detection
- Session termination
- Auto-logout and remember-me features
- Backup code regeneration

SECURITY FEATURES:
- Device fingerprint tracking (browser, OS, screen resolution)
- Suspicious pattern detection (location changes, device changes)
- Risk scoring for sessions
- Automatic session termination for high-risk sessions
- Idle timeout enforcement
- Absolute timeout enforcement

Implements requirements:
- NEW: Session security monitoring
- NEW: Device fingerprinting
- NEW: Suspicious activity detection
- IMPROVEMENT: Backup code regeneration with expiry
- Phase 2.9: Auto-logout features
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.session_security_service import (
    SessionSecurityService,  # type: ignore[import]
)
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import (  # type: ignore[import]
    get_ip_address,
    get_request,
    get_user_agent,
)
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.mfa import BackupCodeStatusType  # type: ignore[import]
from syntek_graphql_auth.types.session_security import (  # type: ignore[import]
    DisableRememberMePayload,
    EnableRememberMePayload,
    SessionSecurityType,
    TerminateSuspiciousSessionsPayload,
    UpdateSessionActivityInput,
    UpdateSessionActivityPayload,
)

logger = logging.getLogger(__name__)


@strawberry.type
class SessionSecurityMutations:
    """GraphQL mutations for session security management."""

    @strawberry.mutation
    def get_session_security(self, info: Info) -> SessionSecurityType:
        """Get current session security information.

        Returns detailed security information about the current session including
        device fingerprint, risk score, and suspicious patterns.

        Security Features:
        - Device fingerprint (browser, OS, resolution)
        - IP address tracking
        - User agent analysis
        - Last activity timestamp
        - Suspicious pattern detection
        - Risk score (0-100)
        - Device change detection

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            SessionSecurityType with session security details

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)
        user_agent = get_user_agent(info)

        # Get session security info
        session_info = SessionSecurityService.get_session_security(
            request=request,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return SessionSecurityType(
            id=strawberry.ID(str(session_info["id"])),
            session_key=session_info["session_key"],
            device_fingerprint=session_info["device_fingerprint"],
            ip_address_decrypted=session_info["ip_address_decrypted"],
            user_agent=session_info["user_agent"],
            last_activity_at=session_info["last_activity_at"],
            created_at=session_info["created_at"],
            suspicious_patterns=session_info["suspicious_patterns"],
            risk_score=session_info["risk_score"],
            device_changes=session_info["device_changes"],
            idle_timeout_seconds=session_info["idle_timeout_seconds"],
            absolute_timeout_at=session_info["absolute_timeout_at"],
            remember_me=session_info["remember_me"],
            is_current=True,
        )

    @strawberry.mutation
    def terminate_suspicious_sessions(self, info: Info) -> TerminateSuspiciousSessionsPayload:
        """Terminate all suspicious sessions for current user.

        Terminates sessions flagged as suspicious (high risk score, device changes,
        location changes) while preserving the current session.

        Security Features:
        - Risk-based termination (risk score > 70)
        - Device change detection
        - Location change detection
        - Preserves current session
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            TerminateSuspiciousSessionsPayload with termination count

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Terminate suspicious sessions
            terminated_count = SessionSecurityService.terminate_suspicious_sessions(
                user=user,
                current_session_key=request.session.session_key,  # type: ignore[attr-defined]
            )

            # Log termination
            AuditService.log_event(
                action="suspicious_sessions_terminated",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"terminated_count": terminated_count},
            )

            return TerminateSuspiciousSessionsPayload(
                success=True,
                message=f"Terminated {terminated_count} suspicious sessions",
                terminated_count=terminated_count,
            )

    @strawberry.mutation
    def regenerate_backup_codes(self, info: Info) -> BackupCodeStatusType:
        """Regenerate backup codes for 2FA.

        Generates new backup codes and revokes old ones. Backup codes expire
        after 90 days by default.

        Security Features:
        - Cryptographically secure generation
        - Argon2id hashing
        - Expiry tracking (90 days)
        - Low-code warning (< 3 remaining)
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            BackupCodeStatusType with new backup code status

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If 2FA not enabled
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Check if 2FA is enabled
        if not getattr(user, "two_factor_enabled", False):
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "2FA must be enabled to generate backup codes",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Regenerate backup codes
            backup_code_status = SessionSecurityService.regenerate_backup_codes(
                user=user,
            )

            # Log backup code regeneration
            AuditService.log_event(
                action="backup_codes_regenerated",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "total_codes": backup_code_status["total_codes"],
                    "expires_at": backup_code_status["expires_at"],
                },
            )

            return BackupCodeStatusType(
                total_codes=backup_code_status["total_codes"],
                remaining_codes=backup_code_status["remaining_codes"],
                used_codes=backup_code_status["used_codes"],
                generated_at=backup_code_status["generated_at"],
                expires_at=backup_code_status["expires_at"],
                days_until_expiry=backup_code_status["days_until_expiry"],
                low_code_warning=backup_code_status["low_code_warning"],
                expiry_warning=backup_code_status["expiry_warning"],
            )

    @strawberry.mutation
    def update_session_activity(
        self, info: Info, input: UpdateSessionActivityInput
    ) -> UpdateSessionActivityPayload:
        """Update session activity timestamp (Phase 2.9 - Auto-logout).

        Updates the last activity timestamp for the current session. This is
        called by the frontend to prevent idle timeout during active use.

        Security Features:
        - Idle timeout tracking
        - Absolute timeout enforcement
        - Activity logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Activity input (optional session_key)

        Returns:
            UpdateSessionActivityPayload with timeout status

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If session not found
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Get session key from input or current session
        session_key = input.session_key if input.session_key else request.session.session_key  # type: ignore[attr-defined]

        if not session_key:
            raise ValidationError(ErrorCode.VALIDATION_ERROR, "Session key not found")

        try:
            # Import syntek service
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService as SyntekSessionSecurityService,
            )

            # Update session activity
            session_security = SyntekSessionSecurityService.update_session_activity(
                session_key=session_key,
                user=user,
            )

            return UpdateSessionActivityPayload(
                success=True,
                message="Session activity updated",
                last_activity_at=session_security.last_activity_at.isoformat(),
                idle_timeout_seconds=session_security.idle_timeout_seconds,
                absolute_timeout_at=(
                    session_security.absolute_timeout_at.isoformat()
                    if session_security.absolute_timeout_at
                    else None
                ),
            )

        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            raise ValidationError(ErrorCode.VALIDATION_ERROR, f"Session update failed: {str(e)}")

    @strawberry.mutation
    def enable_remember_me(self, info: Info) -> EnableRememberMePayload:
        """Enable "Keep me logged in" feature (Phase 2.9 - Auto-logout).

        Enables remember-me functionality, extending session lifetime from
        30 minutes (default) to 30 days.

        Security Features:
        - Extended session lifetime (30 days)
        - Device fingerprint validation
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            EnableRememberMePayload with success status

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If session not found
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)
        session_key = request.session.session_key  # type: ignore[attr-defined]

        if not session_key:
            raise ValidationError(ErrorCode.VALIDATION_ERROR, "Session key not found")

        try:
            # Import syntek service
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService as SyntekSessionSecurityService,
            )

            # Enable remember-me
            session_security = SyntekSessionSecurityService.enable_remember_me(
                session_key=session_key,
                user=user,
            )

            # Log remember-me enabled
            AuditService.log_event(
                action="remember_me_enabled",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "session_expires_at": (
                        session_security.absolute_timeout_at.isoformat()
                        if session_security.absolute_timeout_at
                        else None
                    )
                },
            )

            return EnableRememberMePayload(
                success=True,
                message="Remember-me enabled. Session will last 30 days.",
                session_expires_at=(
                    session_security.absolute_timeout_at.isoformat()
                    if session_security.absolute_timeout_at
                    else None
                ),
            )

        except Exception as e:
            logger.error(f"Failed to enable remember-me: {e}")
            raise ValidationError(ErrorCode.VALIDATION_ERROR, f"Enable remember-me failed: {str(e)}")

    @strawberry.mutation
    def disable_remember_me(self, info: Info) -> DisableRememberMePayload:
        """Disable "Keep me logged in" feature (Phase 2.9 - Auto-logout).

        Disables remember-me functionality, reverting to default 30-minute
        idle timeout.

        Security Features:
        - Revert to default timeout (30 minutes)
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            DisableRememberMePayload with success status

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If session not found
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)
        session_key = request.session.session_key  # type: ignore[attr-defined]

        if not session_key:
            raise ValidationError(ErrorCode.VALIDATION_ERROR, "Session key not found")

        try:
            # Import syntek service
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService as SyntekSessionSecurityService,
            )

            # Disable remember-me
            session_security = SyntekSessionSecurityService.disable_remember_me(
                session_key=session_key,
                user=user,
            )

            # Log remember-me disabled
            AuditService.log_event(
                action="remember_me_disabled",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "session_expires_at": (
                        session_security.absolute_timeout_at.isoformat()
                        if session_security.absolute_timeout_at
                        else None
                    )
                },
            )

            return DisableRememberMePayload(
                success=True,
                message="Remember-me disabled. Session will expire after 30 minutes of inactivity.",
                session_expires_at=(
                    session_security.absolute_timeout_at.isoformat()
                    if session_security.absolute_timeout_at
                    else None
                ),
            )

        except Exception as e:
            logger.error(f"Failed to disable remember-me: {e}")
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR, f"Disable remember-me failed: {str(e)}"
            )
