"""GraphQL queries for IP tracking and management.

This module defines queries for IP whitelist, blacklist, and tracking history.
Admin-only access for whitelist/blacklist, user access for their own IP history.

SECURITY FEATURES:
- Admin-only access for whitelist/blacklist queries
- Users can query their own IP tracking history
- Encrypted IP storage with Rust decryption
- Pagination support for large result sets
- Audit logging for sensitive queries

Implements requirements:
- Phase 2.3: IP management queries
- GDPR: IP tracking with decryption for authorized users
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    PermissionDeniedError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.ip_tracking import (  # type: ignore[import]
    IpBlacklistEntryType,
    IpTrackingEntryType,
    IpWhitelistEntryType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class IPManagementQueries:
    """GraphQL queries for IP tracking and management."""

    @strawberry.field
    def ip_whitelist(
        self, info: Info, limit: int = 50, offset: int = 0
    ) -> list[IpWhitelistEntryType]:
        """Get IP whitelist entries (admin only).

        Lists all whitelisted IP addresses with pagination support.

        Security Features:
        - Admin-only access (is_staff or is_superuser)
        - Decrypted IP addresses in response
        - Pagination support
        - Audit logging

        Args:
            info: GraphQL execution info
            limit: Maximum entries to return (default: 50, max: 100)
            offset: Pagination offset

        Returns:
            List of IP whitelist entries

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(ErrorCode.PERMISSION_DENIED, "Admin access required")

        ip_address = get_ip_address(info)

        # Limit maximum page size
        if limit > 100:
            limit = 100

        # Import service
        try:
            from apps.core.services.audit_service import AuditService  # type: ignore[import]
            from syntek_authentication.services.ip_management_service import (  # type: ignore[import]
                IPManagementService,
            )
        except ImportError:
            logger.error("IPManagementService not available")
            return []

        # Get whitelist entries
        entries = IPManagementService.get_whitelist(limit=limit, offset=offset)

        # Log admin query
        AuditService.log_event(
            action="ip_whitelist_queried",
            user=user,
            organisation=getattr(user, "organisation", None),
            ip_address=ip_address,
            metadata={"limit": limit, "offset": offset, "count": len(entries)},
        )

        return entries

    @strawberry.field
    def ip_blacklist(
        self, info: Info, limit: int = 50, offset: int = 0
    ) -> list[IpBlacklistEntryType]:
        """Get IP blacklist entries (admin only).

        Lists all blacklisted IP addresses with pagination support.

        Security Features:
        - Admin-only access (is_staff or is_superuser)
        - Includes active and expired entries
        - Pagination support
        - Audit logging

        Args:
            info: GraphQL execution info
            limit: Maximum entries to return (default: 50, max: 100)
            offset: Pagination offset

        Returns:
            List of IP blacklist entries

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(ErrorCode.PERMISSION_DENIED, "Admin access required")

        ip_address = get_ip_address(info)

        # Limit maximum page size
        if limit > 100:
            limit = 100

        # Import service
        try:
            from apps.core.services.audit_service import AuditService  # type: ignore[import]
            from syntek_authentication.services.ip_management_service import (  # type: ignore[import]
                IPManagementService,
            )
        except ImportError:
            logger.error("IPManagementService not available")
            return []

        # Get blacklist entries
        entries = IPManagementService.get_blacklist(limit=limit, offset=offset)

        # Log admin query
        AuditService.log_event(
            action="ip_blacklist_queried",
            user=user,
            organisation=getattr(user, "organisation", None),
            ip_address=ip_address,
            metadata={"limit": limit, "offset": offset, "count": len(entries)},
        )

        return entries

    @strawberry.field
    def ip_tracking_history(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
        days: int = 30,
    ) -> list[IpTrackingEntryType]:
        """Get IP tracking history for authenticated user.

        Returns user's IP tracking history with decrypted IP addresses,
        geolocation data, and user agent information.

        Security Features:
        - User can only query their own IP history
        - IP addresses decrypted for authorized users
        - Pagination support
        - Date range filtering
        - Audit logging

        Args:
            info: GraphQL execution info
            limit: Maximum entries to return (default: 50, max: 100)
            offset: Pagination offset
            days: Number of days to query (default: 30, max: 365)

        Returns:
            List of IP tracking entries

        Raises:
            AuthenticationError: If user not authenticated
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
            from syntek_authentication.services.ip_tracking_service import (  # type: ignore[import]
                IPTrackingService,
            )
        except ImportError:
            logger.error("IPTrackingService not available")
            return []

        # Get IP tracking history
        entries = IPTrackingService.get_user_history(
            user=user, limit=limit, offset=offset, days=days
        )

        # Log query (GDPR audit requirement)
        AuditService.log_event(
            action="ip_tracking_history_queried",
            user=user,
            organisation=getattr(user, "organisation", None),
            ip_address=ip_address,
            metadata={"limit": limit, "offset": offset, "days": days, "count": len(entries)},
        )

        return entries
