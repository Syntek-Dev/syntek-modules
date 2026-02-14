"""GraphQL queries for security monitoring and login attempt tracking.

This module defines queries for login attempts and suspicious activity detection.
Users can query their own login history, admins can query all activity.

SECURITY FEATURES:
- Users can query their own login attempts
- Admins can query all login attempts
- Suspicious activity flagging with severity levels
- Pagination and filtering support
- Audit logging for sensitive queries

Implements requirements:
- Phase 2.3: Login attempt and suspicious activity queries
- Security monitoring and alerting
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import AuthenticationError, ErrorCode  # type: ignore[import]
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.login_attempt import (  # type: ignore[import]
    LoginAttemptEntryType,
    LoginAttemptsStatsType,
    SuspiciousActivityEntryType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class SecurityQueries:
    """GraphQL queries for security monitoring and login tracking."""

    @strawberry.field
    def login_attempts(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
        success: bool | None = None,
        days: int = 30,
    ) -> list[LoginAttemptEntryType]:
        """Get login attempts for authenticated user.

        Returns login attempt history with optional filtering by success status
        and date range. Users can only query their own attempts, admins can query all.

        Security Features:
        - Users can only query their own login attempts
        - Admins can query all login attempts
        - Decrypted IP addresses for authorized users
        - Pagination support
        - Success/failure filtering
        - Date range filtering
        - Audit logging

        Args:
            info: GraphQL execution info
            limit: Maximum entries to return (default: 50, max: 100)
            offset: Pagination offset
            success: Filter by success status (null = all attempts)
            days: Number of days to query (default: 30, max: 365)

        Returns:
            List of login attempt entries

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   loginAttempts(success: false, days: 7) {
            >>>     id
            >>>     email
            >>>     ipAddressDecrypted
            >>>     success
            >>>     failureReason
            >>>     createdAt
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Limit maximum page size and date range
        if limit > 100:
            limit = 100
        if days > 365:
            days = 365

        # Import service
        try:
            from apps.core.services.audit_service import AuditService  # type: ignore[import]
            from syntek_authentication.services.login_attempt_service import (  # type: ignore[import]
                LoginAttemptService,
            )
        except ImportError:
            logger.error("LoginAttemptService not available")
            return []

        # Get login attempts (service handles admin vs user filtering)
        is_admin = user.is_staff or user.is_superuser  # type: ignore[attr-defined]
        entries = LoginAttemptService.get_login_attempts(
            user=user,
            is_admin=is_admin,
            limit=limit,
            offset=offset,
            success=success,
            days=days,
        )

        # Log query
        AuditService.log_event(
            action="login_attempts_queried",
            user=user,
            organisation=getattr(user, "organisation", None),
            ip_address=ip_address,
            metadata={
                "limit": limit,
                "offset": offset,
                "success": success,
                "days": days,
                "count": len(entries),
                "is_admin": is_admin,
            },
        )

        return entries

    @strawberry.field
    def login_attempts_stats(self, info: Info, days: int = 30) -> LoginAttemptsStatsType:
        """Get login attempt statistics for authenticated user.

        Returns summary statistics for login attempts including total, successful,
        failed, and suspicious activity counts.

        Security Features:
        - Users can only query their own stats
        - Admins can query all stats
        - Date range filtering
        - Includes suspicious activity count

        Args:
            info: GraphQL execution info
            days: Number of days to query (default: 30, max: 365)

        Returns:
            Login attempt statistics

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Limit date range
        if days > 365:
            days = 365

        # Import service
        try:
            from syntek_authentication.services.login_attempt_service import (  # type: ignore[import]
                LoginAttemptService,
            )
        except ImportError:
            logger.error("LoginAttemptService not available")
            return LoginAttemptsStatsType(
                total_attempts=0,
                successful_attempts=0,
                failed_attempts=0,
                unique_ips=0,
                suspicious_count=0,
                most_recent_success=None,
                most_recent_failure=None,
            )

        # Get stats (service handles admin vs user filtering)
        is_admin = user.is_staff or user.is_superuser  # type: ignore[attr-defined]
        stats = LoginAttemptService.get_login_stats(user=user, is_admin=is_admin, days=days)

        return LoginAttemptsStatsType(
            total_attempts=stats["total_attempts"],
            successful_attempts=stats["successful_attempts"],
            failed_attempts=stats["failed_attempts"],
            unique_ips=stats["unique_ips"],
            suspicious_count=stats["suspicious_count"],
            most_recent_success=stats.get("most_recent_success"),
            most_recent_failure=stats.get("most_recent_failure"),
        )

    @strawberry.field
    def suspicious_activity(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
        severity: str | None = None,
        days: int = 30,
        resolved: bool | None = None,
    ) -> list[SuspiciousActivityEntryType]:
        """Get suspicious activity entries.

        Returns flagged login attempts that exhibit suspicious behavior such as
        rapid failed attempts, location changes, or unusual patterns.

        Security Features:
        - Users can only query their own suspicious activity
        - Admins can query all suspicious activity
        - Severity filtering (low, medium, high, critical)
        - Resolved status filtering
        - Pagination support
        - Audit logging

        Args:
            info: GraphQL execution info
            limit: Maximum entries to return (default: 50, max: 100)
            offset: Pagination offset
            severity: Filter by severity level (low/medium/high/critical, null = all)
            days: Number of days to query (default: 30, max: 365)
            resolved: Filter by resolved status (null = all)

        Returns:
            List of suspicious activity entries

        Raises:
            AuthenticationError: If user not authenticated

        Example:
            >>> query {
            >>>   suspiciousActivity(severity: "high", resolved: false) {
            >>>     id
            >>>     email
            >>>     ipAddressDecrypted
            >>>     reason
            >>>     severity
            >>>     createdAt
            >>>     resolved
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Limit maximum page size and date range
        if limit > 100:
            limit = 100
        if days > 365:
            days = 365

        # Import service
        try:
            from apps.core.services.audit_service import AuditService  # type: ignore[import]
            from syntek_authentication.services.suspicious_activity_service import (  # type: ignore[import]
                SuspiciousActivityService,
            )
        except ImportError:
            logger.error("SuspiciousActivityService not available")
            return []

        # Get suspicious activity (service handles admin vs user filtering)
        is_admin = user.is_staff or user.is_superuser  # type: ignore[attr-defined]
        entries = SuspiciousActivityService.get_suspicious_activity(
            user=user,
            is_admin=is_admin,
            limit=limit,
            offset=offset,
            severity=severity,
            days=days,
            resolved=resolved,
        )

        # Log query
        AuditService.log_event(
            action="suspicious_activity_queried",
            user=user,
            organisation=getattr(user, "organisation", None),
            ip_address=ip_address,
            metadata={
                "limit": limit,
                "offset": offset,
                "severity": severity,
                "days": days,
                "resolved": resolved,
                "count": len(entries),
                "is_admin": is_admin,
            },
        )

        return entries
