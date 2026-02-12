"""Failed login tracking and account lockout service.

This module implements progressive account lockout based on failed login attempts.
Tracks failures by both IP address and user account for comprehensive security.

SECURITY NOTE (M9):
- Track by IP address and by user account
- Progressive lockout with exponential backoff
- Automatic unlock after lockout period
- Audit logging for all lockout events

Example:
    >>> FailedLoginService.record_failure(user, ip_address)
    >>> is_locked, remaining = FailedLoginService.check_lockout(user)
    >>> FailedLoginService.clear_failed_attempts(user)
"""

import hashlib
import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.core.cache import cache
from django.utils import timezone

if TYPE_CHECKING:
    from syntek_authentication.models import User

logger = logging.getLogger(__name__)


class FailedLoginService:
    """Service for tracking failed login attempts and account lockout.

    Implements progressive lockout with exponential backoff:
    - 3-5 failures: 5 minute lockout
    - 6-10 failures: 15 minute lockout
    - 11-20 failures: 1 hour lockout
    - 21+ failures: 24 hour lockout

    Tracks failures by:
    - User account (email)
    - IP address

    Attributes:
        LOCKOUT_THRESHOLDS: Tuple of (max_attempts, lockout_minutes) for each tier
        IP_CACHE_PREFIX: Redis key prefix for IP-based tracking
        USER_CACHE_PREFIX: Redis key prefix for user-based tracking
    """

    # Progressive lockout tiers: (max_attempts, lockout_minutes)
    LOCKOUT_THRESHOLDS = [
        (3, 5),  # 3-5 failures = 5 min lockout
        (6, 15),  # 6-10 failures = 15 min lockout
        (11, 60),  # 11-20 failures = 1 hour lockout
        (21, 1440),  # 21+ failures = 24 hour lockout
    ]

    IP_CACHE_PREFIX = "failed_login:ip"
    USER_CACHE_PREFIX = "failed_login:user"
    LOCKOUT_CACHE_PREFIX = "account_locked"

    @staticmethod
    def _get_lockout_duration(failure_count: int) -> int:
        """Calculate lockout duration based on failure count.

        Args:
            failure_count: Number of consecutive failed attempts.

        Returns:
            Lockout duration in minutes.
        """
        for max_attempts, lockout_minutes in FailedLoginService.LOCKOUT_THRESHOLDS:
            if failure_count <= max_attempts:
                return lockout_minutes

        # If more than highest threshold, use the maximum lockout
        return FailedLoginService.LOCKOUT_THRESHOLDS[-1][1]

    @staticmethod
    def _get_cache_key(identifier: str, prefix: str) -> str:
        """Generate cache key for failure tracking.

        Args:
            identifier: Email or IP address.
            prefix: Cache key prefix.

        Returns:
            Hashed cache key.
        """
        # Hash the identifier for privacy (especially for IPs)
        identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"{prefix}:{identifier_hash}"

    @staticmethod
    def record_failure(
        user: "User | None",
        ip_address: str,
        email: str | None = None,
    ) -> dict:
        """Record a failed login attempt.

        Increments failure count for both user and IP address.
        Triggers lockout if threshold is exceeded.

        Args:
            user: User account (None if user doesn't exist).
            ip_address: IP address of the failed attempt.
            email: Email address used in the attempt (for non-existent users).

        Returns:
            Dictionary with lockout information:
                {
                    'failures': int,
                    'is_locked': bool,
                    'lockout_until': datetime | None,
                    'lockout_minutes': int | None,
                }
        """
        identifier = user.email if user else (email or ip_address)

        # Increment failure count for user/email
        user_key = FailedLoginService._get_cache_key(
            identifier,  # type: ignore[arg-type]
            FailedLoginService.USER_CACHE_PREFIX,
        )
        user_failures = cache.get(user_key, 0) + 1
        cache.set(user_key, user_failures, timeout=86400)  # 24 hour expiry

        # Increment failure count for IP
        ip_key = FailedLoginService._get_cache_key(
            ip_address,
            FailedLoginService.IP_CACHE_PREFIX,
        )
        ip_failures = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_failures, timeout=86400)  # 24 hour expiry

        # Use the higher of the two failure counts
        failure_count = max(user_failures, ip_failures)

        # Check if lockout threshold exceeded
        min_threshold = FailedLoginService.LOCKOUT_THRESHOLDS[0][0]
        if failure_count >= min_threshold:
            lockout_minutes = FailedLoginService._get_lockout_duration(failure_count)
            lockout_until = timezone.now() + timedelta(minutes=lockout_minutes)

            # Set lockout flag
            lockout_key = FailedLoginService._get_cache_key(
                identifier,  # type: ignore[arg-type]
                FailedLoginService.LOCKOUT_CACHE_PREFIX,
            )
            cache.set(lockout_key, lockout_until.timestamp(), timeout=lockout_minutes * 60)

            # Log the lockout event
            logger.warning(
                f"Account locked: {identifier} after {failure_count} failed attempts",
                extra={
                    "email": identifier,
                    "ip_address": ip_address,
                    "failures": failure_count,
                    "lockout_minutes": lockout_minutes,
                    "lockout_until": lockout_until.isoformat(),
                },
            )

            # Create audit log if user exists
            # NOTE: AuditService dependency commented out - will be available after audit module extraction
            # if user:
            #     from syntek_audit.services import AuditService
            #
            #     AuditService.log_event(
            #         action="account_locked",
            #         user=user,
            #         ip_address=ip_address,
            #         metadata={
            #             "failures": failure_count,
            #             "lockout_minutes": lockout_minutes,
            #         },
            #     )

            return {
                "failures": failure_count,
                "is_locked": True,
                "lockout_until": lockout_until,
                "lockout_minutes": lockout_minutes,
            }

        return {
            "failures": failure_count,
            "is_locked": False,
            "lockout_until": None,
            "lockout_minutes": None,
        }

    @staticmethod
    def check_lockout(user: "User | None", email: str | None = None) -> tuple[bool, int]:
        """Check if account is currently locked out.

        Args:
            user: User account to check.
            email: Email address to check (if user doesn't exist).

        Returns:
            Tuple of (is_locked, remaining_seconds).
        """
        identifier = user.email if user else email
        if not identifier:
            return False, 0

        lockout_key = FailedLoginService._get_cache_key(
            identifier,  # type: ignore[arg-type]
            FailedLoginService.LOCKOUT_CACHE_PREFIX,
        )
        lockout_timestamp = cache.get(lockout_key)

        if not lockout_timestamp:
            return False, 0

        lockout_until = timezone.datetime.fromtimestamp(
            lockout_timestamp,
            tz=timezone.get_current_timezone(),
        )

        if timezone.now() >= lockout_until:
            # Lockout expired
            cache.delete(lockout_key)
            return False, 0

        remaining_seconds = int((lockout_until - timezone.now()).total_seconds())
        return True, remaining_seconds

    @staticmethod
    def clear_failed_attempts(user: "User | None", email: str | None = None) -> None:
        """Clear failed login attempts for a user.

        Called after successful login to reset the failure counter.

        Args:
            user: User account to clear.
            email: Email address to clear (if user doesn't exist).
        """
        identifier = user.email if user else email
        if not identifier:
            return

        # Clear user failure count
        user_key = FailedLoginService._get_cache_key(
            identifier,  # type: ignore[arg-type]
            FailedLoginService.USER_CACHE_PREFIX,
        )
        cache.delete(user_key)

        # Clear lockout flag
        lockout_key = FailedLoginService._get_cache_key(
            identifier,  # type: ignore[arg-type]
            FailedLoginService.LOCKOUT_CACHE_PREFIX,
        )
        cache.delete(lockout_key)

    @staticmethod
    def get_failure_count(user: "User | None", email: str | None = None) -> int:
        """Get current failure count for a user.

        Args:
            user: User account.
            email: Email address (if user doesn't exist).

        Returns:
            Number of failed attempts.
        """
        identifier = user.email if user else email
        if not identifier:
            return 0

        user_key = FailedLoginService._get_cache_key(
            identifier,  # type: ignore[arg-type]
            FailedLoginService.USER_CACHE_PREFIX,
        )
        return cache.get(user_key, 0)

    @staticmethod
    def clear_ip_failures(ip_address: str) -> None:
        """Clear failed attempts for an IP address.

        Args:
            ip_address: IP address to clear.
        """
        ip_key = FailedLoginService._get_cache_key(
            ip_address,
            FailedLoginService.IP_CACHE_PREFIX,
        )
        cache.delete(ip_key)
