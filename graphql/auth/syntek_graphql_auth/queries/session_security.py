"""GraphQL queries for session security and monitoring.

This module defines queries for session fingerprinting, device tracking,
and active session management.

SECURITY FEATURES:
- Session fingerprint tracking
- Device change detection
- Risk scoring for sessions
- Suspicious pattern detection
- Active session enumeration
- Audit logging

Implements requirements:
- Phase 2.3: Session security queries
- Session hijacking detection
- Auto-logout status monitoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import AuthenticationError, ErrorCode  # type: ignore[import]
from syntek_graphql_core.utils.context import (  # type: ignore[import]
    get_ip_address,
    get_request,
    get_user_agent,
)
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.session_security import (  # type: ignore[import]
    SessionSecurityType,
    SessionStatusType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class SessionSecurityQueries:
    """GraphQL queries for session security monitoring."""

    @strawberry.field
    def session_security(self, info: Info) -> SessionSecurityType:
        """Get security information for current session.

        Returns detailed security information about the current session including
        device fingerprint, risk score, suspicious patterns, and timeout settings.

        Security Features:
        - Device fingerprint (browser, OS, screen resolution)
        - IP address tracking
        - User agent analysis
        - Suspicious pattern detection
        - Risk score (0-100)
        - Device change detection
        - Idle timeout tracking
        - Absolute timeout tracking

        Returns:
            SessionSecurityType with current session security details

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   sessionSecurity {
            >>>     sessionKey
            >>>     deviceFingerprint
            >>>     ipAddressDecrypted
            >>>     riskScore
            >>>     suspiciousPatterns
            >>>     deviceChanges
            >>>     idleTimeoutSeconds
            >>>     rememberMe
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)
        user_agent = get_user_agent(info)

        # Import service
        try:
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService,
            )
        except ImportError:
            logger.error("SessionSecurityService not available")
            # Return minimal session info
            return SessionSecurityType(
                id=strawberry.ID("unknown"),
                session_key="unknown",
                device_fingerprint="unknown",
                ip_address_decrypted=ip_address,
                user_agent=user_agent,
                last_activity_at="",
                created_at="",
                suspicious_patterns=[],
                risk_score=0,
                device_changes=[],
                idle_timeout_seconds=900,  # 15 minutes default
                absolute_timeout_at=None,
                remember_me=False,
                is_current=True,
            )

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

    @strawberry.field
    def active_sessions(self, info: Info, limit: int = 50) -> list[SessionSecurityType]:
        """Get all active sessions for authenticated user.

        Returns list of all active sessions with device information, location data,
        and security metrics. Useful for "where you're logged in" pages.

        Security Features:
        - Device info (browser, OS, screen resolution)
        - IP addresses (decrypted)
        - Location data from IP geolocation
        - Last activity timestamp
        - Session creation time
        - Risk scores and suspicious patterns
        - Remember-me status
        - Current session flagged

        Args:
            info: GraphQL execution info
            limit: Maximum sessions to return (default: 50, max: 100)

        Returns:
            List of active session security entries

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   activeSessions {
            >>>     id
            >>>     sessionKey
            >>>     deviceFingerprint
            >>>     ipAddressDecrypted
            >>>     lastActivityAt
            >>>     createdAt
            >>>     riskScore
            >>>     isCurrent
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Limit maximum page size
        if limit > 100:
            limit = 100

        # Import service
        try:
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService,
            )
        except ImportError:
            logger.error("SessionSecurityService not available")
            return []

        # Get all active sessions for user
        sessions = SessionSecurityService.get_active_sessions(user=user, limit=limit)

        # Convert to GraphQL types
        current_session_key = request.session.session_key if hasattr(request, "session") else None  # type: ignore[attr-defined]

        return [
            SessionSecurityType(
                id=strawberry.ID(str(session["id"])),
                session_key=session["session_key"],
                device_fingerprint=session["device_fingerprint"],
                ip_address_decrypted=session["ip_address_decrypted"],
                user_agent=session["user_agent"],
                last_activity_at=session["last_activity_at"],
                created_at=session["created_at"],
                suspicious_patterns=session["suspicious_patterns"],
                risk_score=session["risk_score"],
                device_changes=session["device_changes"],
                idle_timeout_seconds=session["idle_timeout_seconds"],
                absolute_timeout_at=session["absolute_timeout_at"],
                remember_me=session["remember_me"],
                is_current=session["session_key"] == current_session_key,
            )
            for session in sessions
        ]

    @strawberry.field
    def session_status(self, info: Info) -> SessionStatusType:
        """Get timeout status for current session (Phase 2.9 - Auto-logout).

        Returns information about session activity and timeout settings,
        useful for frontend to display auto-logout warnings.

        Security Features:
        - Idle timeout tracking
        - Absolute timeout tracking
        - Activity timestamp
        - Warning flags for approaching timeout
        - Remember-me status

        Returns:
            SessionStatusType with timeout status

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   sessionStatus {
            >>>     isActive
            >>>     lastActivityAt
            >>>     idleTimeoutSeconds
            >>>     secondsUntilIdleTimeout
            >>>     rememberMe
            >>>     shouldWarn
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        session_key = request.session.session_key  # type: ignore[attr-defined]

        if not session_key:
            # Return minimal status if no session key
            return SessionStatusType(
                is_active=True,
                last_activity_at="",
                idle_timeout_seconds=1800,  # 30 minutes default
                absolute_timeout_at=None,
                seconds_until_idle_timeout=None,
                seconds_until_absolute_timeout=None,
                remember_me=False,
                should_warn=False,
            )

        # Import service
        try:
            from syntek_authentication.services.session_security_service import (  # type: ignore[import]
                SessionSecurityService,
            )
        except ImportError:
            logger.error("SessionSecurityService not available")
            # Return minimal status
            return SessionStatusType(
                is_active=True,
                last_activity_at="",
                idle_timeout_seconds=1800,  # 30 minutes default
                absolute_timeout_at=None,
                seconds_until_idle_timeout=None,
                seconds_until_absolute_timeout=None,
                remember_me=False,
                should_warn=False,
            )

        try:
            # Get session status
            status = SessionSecurityService.get_session_status(
                session_key=session_key, user=user
            )

            return SessionStatusType(
                is_active=status["is_active"],
                last_activity_at=status["last_activity_at"],
                idle_timeout_seconds=status["idle_timeout_seconds"],
                absolute_timeout_at=status.get("absolute_timeout_at"),
                seconds_until_idle_timeout=status.get("seconds_until_idle_timeout"),
                seconds_until_absolute_timeout=status.get("seconds_until_absolute_timeout"),
                remember_me=status["remember_me"],
                should_warn=status["auto_logout_warning"],
            )

        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            # Return minimal status on error
            return SessionStatusType(
                is_active=True,
                last_activity_at="",
                idle_timeout_seconds=1800,  # 30 minutes default
                absolute_timeout_at=None,
                seconds_until_idle_timeout=None,
                seconds_until_absolute_timeout=None,
                remember_me=False,
                should_warn=False,
            )
