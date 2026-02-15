"""IP tracking service for security monitoring and access control.

This module provides IP address tracking functionality including:
- IP address logging with encryption
- IP whitelisting and blacklisting
- Redis caching for performance
- Geolocation tracking (optional)

SECURITY NOTE:
- Encrypted IP storage (AES-256-GCM)
- HMAC-based lookups (constant-time)
- Redis caching for whitelist/blacklist
- Automatic cleanup (90-day retention)

Example:
    >>> IPTrackingService.track_ip(user, request)
    >>> is_blocked = IPTrackingService.is_ip_blacklisted(ip_address)
    >>> IPTrackingService.add_to_whitelist(user, ip_address, "Home IP")
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone

try:
    from syntek_rust import (
        encrypt_ip_address_py,
        hash_ip_address_py,
    )
except ImportError:
    raise ImportError(
        "syntek_rust not found. Install with: cd rust/pyo3_bindings && maturin develop"
    )

if TYPE_CHECKING:
    from django.http import HttpRequest

    from syntek_authentication.models import IPBlacklist, IPTracking, IPWhitelist, User

logger = logging.getLogger(__name__)


class IPTrackingService:
    """Service for IP address tracking and access control.

    Handles IP tracking and access control:
    1. Log IP addresses with encryption
    2. Track geolocation (optional)
    3. Whitelist/blacklist management
    4. Redis caching for performance

    Features:
    - Encrypted IP storage
    - Constant-time lookups
    - Redis caching
    - Geolocation support
    - Automatic cleanup

    Attributes:
        CACHE_TTL: Redis cache time-to-live (seconds)
        RETENTION_DAYS: IP tracking retention period
        CACHE_KEY_WHITELIST: Redis key prefix for whitelist
        CACHE_KEY_BLACKLIST: Redis key prefix for blacklist
    """

    CACHE_TTL = 3600  # 1 hour
    RETENTION_DAYS = 90  # 90 days for global, 60 for EU
    CACHE_KEY_WHITELIST = "ip_whitelist:{ip_hash}"
    CACHE_KEY_BLACKLIST = "ip_blacklist:{ip_hash}"

    @staticmethod
    def _get_encryption_key() -> bytes:
        """Get encryption key from settings."""
        from django.conf import settings

        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _get_hmac_key() -> bytes:
        """Get HMAC key from settings."""
        from django.conf import settings

        key = getattr(settings, "HMAC_SECRET_KEY", None)
        if not key:
            raise ValueError("HMAC_SECRET_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _get_client_ip(request: "HttpRequest") -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    @staticmethod
    @transaction.atomic
    def track_ip(
        user: "User", request: "HttpRequest", location_data: dict | None = None
    ) -> "IPTracking":
        """Track IP address for user.

        Args:
            user: User whose IP to track.
            request: Django HTTP request.
            location_data: Optional geolocation data.

        Returns:
            IPTracking object.
        """
        from syntek_authentication.models import IPTracking

        encryption_key = IPTrackingService._get_encryption_key()
        hmac_key = IPTrackingService._get_hmac_key()

        # Get IP and user agent
        ip_address = IPTrackingService._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        # Encrypt IP address
        ip_encrypted = encrypt_ip_address_py(ip_address, encryption_key)
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Encrypt location data if provided
        location_encrypted = None
        if location_data:
            import json

            location_json = json.dumps(location_data)
            location_encrypted = encrypt_ip_address_py(location_json, encryption_key)

        # Create tracking record
        ip_tracking = IPTracking.objects.create(
            user=user,
            ip_address_encrypted=ip_encrypted,
            ip_hash=ip_hash,
            location_data_encrypted=location_encrypted,
            user_agent=user_agent,
        )

        logger.info(f"IP tracked for user {user.id}: {ip_hash[:8]}...")

        return ip_tracking

    @staticmethod
    def is_ip_whitelisted(ip_address: str, user: "User | None" = None) -> bool:
        """Check if IP address is whitelisted.

        Checks both user-specific and global whitelists.

        Args:
            ip_address: IP address to check.
            user: Optional user for user-specific whitelist.

        Returns:
            True if whitelisted, False otherwise.
        """
        from syntek_authentication.models import IPWhitelist

        hmac_key = IPTrackingService._get_hmac_key()
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Check Redis cache first
        cache_key = IPTrackingService.CACHE_KEY_WHITELIST.format(ip_hash=ip_hash)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check database
        query = IPWhitelist.objects.filter(ip_hash=ip_hash, is_active=True)

        # Check expiry
        query = query.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )

        # Check user-specific or global
        if user:
            is_whitelisted = query.filter(
                models.Q(user=user) | models.Q(user__isnull=True)
            ).exists()
        else:
            is_whitelisted = query.filter(user__isnull=True).exists()

        # Cache result
        cache.set(cache_key, is_whitelisted, IPTrackingService.CACHE_TTL)

        return is_whitelisted

    @staticmethod
    def is_ip_blacklisted(ip_address: str) -> bool:
        """Check if IP address is blacklisted.

        Args:
            ip_address: IP address to check.

        Returns:
            True if blacklisted, False otherwise.
        """
        from syntek_authentication.models import IPBlacklist

        hmac_key = IPTrackingService._get_hmac_key()
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Check Redis cache first
        cache_key = IPTrackingService.CACHE_KEY_BLACKLIST.format(ip_hash=ip_hash)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check database
        query = IPBlacklist.objects.filter(ip_hash=ip_hash, is_active=True)

        # Check expiry
        query = query.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )

        is_blacklisted = query.exists()

        # Cache result
        cache.set(cache_key, is_blacklisted, IPTrackingService.CACHE_TTL)

        return is_blacklisted

    @staticmethod
    @transaction.atomic
    def add_to_whitelist(
        ip_address: str,
        user: "User | None" = None,
        reason: str = "",
        expires_at: timezone.datetime | None = None,
        admin_user: "User | None" = None,
    ) -> "IPWhitelist":
        """Add IP address to whitelist.

        Args:
            ip_address: IP address to whitelist.
            user: Optional user (user-specific whitelist).
            reason: Reason for whitelisting.
            expires_at: Optional expiry date.
            admin_user: Admin adding whitelist entry.

        Returns:
            IPWhitelist object.
        """
        from syntek_authentication.models import IPWhitelist

        encryption_key = IPTrackingService._get_encryption_key()
        hmac_key = IPTrackingService._get_hmac_key()

        # Encrypt IP address (for audit trail)
        ip_encrypted = encrypt_ip_address_py(ip_address, encryption_key)
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Create whitelist entry
        whitelist_entry = IPWhitelist.objects.create(
            user=user,
            ip_address_encrypted=ip_encrypted,
            ip_hash=ip_hash,
            reason=reason,
            expires_at=expires_at,
            created_by=admin_user,
        )

        # Invalidate cache
        cache_key = IPTrackingService.CACHE_KEY_WHITELIST.format(ip_hash=ip_hash)
        cache.delete(cache_key)

        logger.info(
            f"IP whitelisted: {ip_hash[:8]}... "
            f"(user={user.id if user else 'global'}, admin={admin_user.id if admin_user else 'system'})"
        )

        return whitelist_entry

    @staticmethod
    @transaction.atomic
    def add_to_blacklist(
        ip_address: str,
        reason: str = "",
        expires_at: timezone.datetime | None = None,
        admin_user: "User | None" = None,
    ) -> "IPBlacklist":
        """Add IP address to blacklist.

        Args:
            ip_address: IP address to blacklist.
            reason: Reason for blacklisting.
            expires_at: Optional expiry date.
            admin_user: Admin adding blacklist entry.

        Returns:
            IPBlacklist object.
        """
        from syntek_authentication.models import IPBlacklist

        hmac_key = IPTrackingService._get_hmac_key()
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Create blacklist entry (no IP storage for security)
        blacklist_entry = IPBlacklist.objects.create(
            ip_hash=ip_hash,
            reason=reason,
            expires_at=expires_at,
            created_by=admin_user,
        )

        # Invalidate cache
        cache_key = IPTrackingService.CACHE_KEY_BLACKLIST.format(ip_hash=ip_hash)
        cache.delete(cache_key)

        logger.warning(
            f"IP blacklisted: {ip_hash[:8]}... (admin={admin_user.id if admin_user else 'system'})"
        )

        return blacklist_entry

    @staticmethod
    def cleanup_old_tracking_records(retention_days: int | None = None) -> int:
        """Clean up old IP tracking records.

        Args:
            retention_days: Retention period (default: RETENTION_DAYS).

        Returns:
            Number of records deleted.
        """
        from syntek_authentication.models import IPTracking

        if retention_days is None:
            retention_days = IPTrackingService.RETENTION_DAYS

        cutoff_date = timezone.now() - timedelta(days=retention_days)

        deleted_count, _ = IPTracking.objects.filter(created_at__lt=cutoff_date).delete()

        logger.info(
            f"Cleaned up {deleted_count} old IP tracking records (retention={retention_days} days)"
        )

        return deleted_count
