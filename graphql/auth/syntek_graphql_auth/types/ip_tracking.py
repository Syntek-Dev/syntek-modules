"""GraphQL types for IP tracking and management.

This module defines types for IP tracking, whitelist, and blacklist operations.
Implements encrypted PII handling and geolocation data.
"""

from __future__ import annotations

import strawberry


@strawberry.input
class AddIpWhitelistInput:
    """Input for adding IP to whitelist.

    Attributes:
        ip_address: IP address to whitelist
        reason: Reason for whitelisting
        expires_days: Optional expiry in days (null = permanent)
    """

    ip_address: str
    reason: str
    expires_days: int | None = None


@strawberry.input
class RemoveIpWhitelistInput:
    """Input for removing IP from whitelist.

    Attributes:
        whitelist_id: UUID of whitelist entry to remove
    """

    whitelist_id: strawberry.ID


@strawberry.input
class AddIpBlacklistInput:
    """Input for adding IP to blacklist.

    Attributes:
        ip_address: IP address to block
        reason: Reason for blacklisting
        permanent: Whether this is a permanent ban
        expires_days: Optional expiry in days (ignored if permanent=True)
    """

    ip_address: str
    reason: str
    permanent: bool = False
    expires_days: int | None = None


@strawberry.input
class RemoveIpBlacklistInput:
    """Input for removing IP from blacklist.

    Attributes:
        blacklist_id: UUID of blacklist entry to remove
    """

    blacklist_id: strawberry.ID


@strawberry.type
class IpTrackingEntryType:
    """GraphQL type for IP tracking entry.

    Represents a logged IP address with geolocation data.

    Attributes:
        id: Entry UUID
        ip_address_decrypted: Decrypted IP address (only for authorized users)
        location: Geolocation data (city, country, region)
        user_agent: Browser/device user agent
        created_at: Timestamp when IP was tracked
    """

    id: strawberry.ID
    ip_address_decrypted: str | None = None  # Null if user not authorized
    location: str | None = None  # e.g., "London, GB"
    user_agent: str
    created_at: str


@strawberry.type
class IpWhitelistEntryType:
    """GraphQL type for IP whitelist entry.

    Represents a whitelisted IP address.

    Attributes:
        id: Entry UUID
        ip_address_decrypted: Decrypted IP address
        reason: Reason for whitelisting
        created_at: When entry was created
        created_by: User who created entry (name)
        expires_at: When entry expires (null = permanent)
        is_expired: Whether entry has expired
    """

    id: strawberry.ID
    ip_address_decrypted: str
    reason: str
    created_at: str
    created_by: str | None = None
    expires_at: str | None = None
    is_expired: bool


@strawberry.type
class IpBlacklistEntryType:
    """GraphQL type for IP blacklist entry.

    Represents a blacklisted IP address.

    Attributes:
        id: Entry UUID
        reason: Reason for blacklisting
        permanent: Whether this is a permanent ban
        created_at: When entry was created
        expires_at: When entry expires (null if permanent)
        is_active: Whether entry is currently active
    """

    id: strawberry.ID
    reason: str
    permanent: bool
    created_at: str
    expires_at: str | None = None
    is_active: bool


@strawberry.type
class AddIpWhitelistPayload:
    """Response payload for adding IP to whitelist.

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
        entry: Created whitelist entry
    """

    success: bool
    message: str
    entry: IpWhitelistEntryType | None = None


@strawberry.type
class RemoveIpWhitelistPayload:
    """Response payload for removing IP from whitelist.

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
    """

    success: bool
    message: str


@strawberry.type
class AddIpBlacklistPayload:
    """Response payload for adding IP to blacklist.

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
        entry: Created blacklist entry
    """

    success: bool
    message: str
    entry: IpBlacklistEntryType | None = None


@strawberry.type
class RemoveIpBlacklistPayload:
    """Response payload for removing IP from blacklist.

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
    """

    success: bool
    message: str
