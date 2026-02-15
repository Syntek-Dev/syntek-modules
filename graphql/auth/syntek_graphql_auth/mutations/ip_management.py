"""GraphQL mutations for IP whitelist/blacklist management.

This module defines mutations for managing IP access control lists.
Admins can whitelist trusted IPs or blacklist malicious IPs.

SECURITY FEATURES:
- Admin-only access (requires staff or superuser)
- Encrypted IP storage using Rust
- CIDR notation support (/24, /32)
- Expiry dates for temporary blocks/allows
- Reason tracking for audit trails
- Automatic IP validation

Implements requirements:
- IP whitelist management
- IP blacklist management
- Bloom filter optimization for blacklist checks
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.ip_management_service import IPManagementService  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    PermissionDeniedError,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.ip_tracking import (  # type: ignore[import]
    AddIpBlacklistInput,
    AddIpBlacklistPayload,
    AddIpWhitelistInput,
    AddIpWhitelistPayload,
    IpBlacklistEntryType,
    IpWhitelistEntryType,
    RemoveIpBlacklistInput,
    RemoveIpBlacklistPayload,
    RemoveIpWhitelistInput,
    RemoveIpWhitelistPayload,
)

logger = logging.getLogger(__name__)


@strawberry.type
class IPManagementMutations:
    """GraphQL mutations for IP whitelist/blacklist management."""

    @strawberry.mutation
    def add_ip_whitelist(
        self, info: Info, input: AddIpWhitelistInput
    ) -> AddIpWhitelistPayload:
        """Add IP address to whitelist (admin only).

        Whitelisted IPs bypass rate limiting and are always allowed access.
        Useful for trusted services, internal networks, or VIP users.

        Security Features:
        - Admin-only access
        - Encrypted IP storage (Rust)
        - CIDR notation support
        - Expiry dates for temporary whitelisting
        - Reason tracking
        - IP format validation

        Args:
            info: GraphQL execution info with authenticated admin user
            input: Whitelist input (ip_address, reason, expires_at)

        Returns:
            AddIpWhitelistPayload with created entry

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
            ValidationError: If IP format invalid
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(
                ErrorCode.PERMISSION_DENIED,
                "Admin access required",
            )

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Add to whitelist
            entry = IPManagementService.add_to_whitelist(
                ip_address=input.ip_address,
                reason=input.reason,
                expires_at=input.expires_at,
                added_by=user,
            )

            # Log whitelist addition
            AuditService.log_event(
                action="ip_whitelist_added",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "whitelisted_ip": input.ip_address,
                    "reason": input.reason,
                    "expires_at": input.expires_at,
                },
            )

            return AddIpWhitelistPayload(
                success=True,
                message=f"IP {input.ip_address} added to whitelist",
                entry=IpWhitelistEntryType(
                    id=strawberry.ID(str(entry.id)),
                    ip_address=input.ip_address,
                    reason=input.reason,
                    added_by_email=user.email,  # type: ignore[attr-defined]
                    expires_at=entry.expires_at.isoformat() if entry.expires_at else None,
                    is_expired=entry.is_expired(),
                    created_at=entry.created_at.isoformat(),
                ),
            )

    @strawberry.mutation
    def remove_ip_whitelist(
        self, info: Info, input: RemoveIpWhitelistInput
    ) -> RemoveIpWhitelistPayload:
        """Remove IP address from whitelist (admin only).

        Removes IP from whitelist, restoring normal rate limiting and access rules.

        Args:
            info: GraphQL execution info with authenticated admin user
            input: Remove input (ip_address)

        Returns:
            RemoveIpWhitelistPayload with success status

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
            ValidationError: If IP not whitelisted
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(
                ErrorCode.PERMISSION_DENIED,
                "Admin access required",
            )

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Remove from whitelist
            removed = IPManagementService.remove_from_whitelist(
                ip_address=input.ip_address,
            )

            if not removed:
                raise ValidationError(
                    ErrorCode.VALIDATION_ERROR,
                    f"IP {input.ip_address} not found in whitelist",
                )

            # Log whitelist removal
            AuditService.log_event(
                action="ip_whitelist_removed",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"removed_ip": input.ip_address},
            )

            return RemoveIpWhitelistPayload(
                success=True,
                message=f"IP {input.ip_address} removed from whitelist",
            )

    @strawberry.mutation
    def add_ip_blacklist(
        self, info: Info, input: AddIpBlacklistInput
    ) -> AddIpBlacklistPayload:
        """Add IP address to blacklist (admin only).

        Blacklisted IPs are completely blocked from accessing the system.
        Useful for blocking malicious IPs, attackers, or banned users.

        Security Features:
        - Admin-only access
        - Encrypted IP storage (Rust)
        - CIDR notation support (block entire subnets)
        - Expiry dates for temporary bans
        - Reason tracking (e.g., "brute force", "spam")
        - Bloom filter optimization for fast checks
        - IP format validation

        Args:
            info: GraphQL execution info with authenticated admin user
            input: Blacklist input (ip_address, reason, expires_at)

        Returns:
            AddIpBlacklistPayload with created entry

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
            ValidationError: If IP format invalid
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(
                ErrorCode.PERMISSION_DENIED,
                "Admin access required",
            )

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Add to blacklist
            entry = IPManagementService.add_to_blacklist(
                ip_address=input.ip_address,
                reason=input.reason,
                expires_at=input.expires_at,
                added_by=user,
            )

            # Log blacklist addition
            AuditService.log_event(
                action="ip_blacklist_added",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "blacklisted_ip": input.ip_address,
                    "reason": input.reason,
                    "expires_at": input.expires_at,
                },
            )

            return AddIpBlacklistPayload(
                success=True,
                message=f"IP {input.ip_address} added to blacklist",
                entry=IpBlacklistEntryType(
                    id=strawberry.ID(str(entry.id)),
                    ip_address=input.ip_address,
                    reason=input.reason,
                    added_by_email=user.email,  # type: ignore[attr-defined]
                    expires_at=entry.expires_at.isoformat() if entry.expires_at else None,
                    is_expired=entry.is_expired(),
                    created_at=entry.created_at.isoformat(),
                ),
            )

    @strawberry.mutation
    def remove_ip_blacklist(
        self, info: Info, input: RemoveIpBlacklistInput
    ) -> RemoveIpBlacklistPayload:
        """Remove IP address from blacklist (admin only).

        Removes IP from blacklist, allowing access again. Use when ban period
        has ended or IP was incorrectly blacklisted.

        Args:
            info: GraphQL execution info with authenticated admin user
            input: Remove input (ip_address)

        Returns:
            RemoveIpBlacklistPayload with success status

        Raises:
            AuthenticationError: If user not authenticated
            PermissionDeniedError: If user not admin
            ValidationError: If IP not blacklisted
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Check admin permissions
        if not (user.is_staff or user.is_superuser):  # type: ignore[attr-defined]
            raise PermissionDeniedError(
                ErrorCode.PERMISSION_DENIED,
                "Admin access required",
            )

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Remove from blacklist
            removed = IPManagementService.remove_from_blacklist(
                ip_address=input.ip_address,
            )

            if not removed:
                raise ValidationError(
                    ErrorCode.VALIDATION_ERROR,
                    f"IP {input.ip_address} not found in blacklist",
                )

            # Log blacklist removal
            AuditService.log_event(
                action="ip_blacklist_removed",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"removed_ip": input.ip_address},
            )

            return RemoveIpBlacklistPayload(
                success=True,
                message=f"IP {input.ip_address} removed from blacklist",
            )
