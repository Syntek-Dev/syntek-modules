"""Suspicious activity detection and alerting service.

This module detects and alerts on suspicious security events:
- Login from new location (IP address)
- Password change events
- 2FA disable events
- Multiple failed login attempts
- Session anomalies

SECURITY NOTE (M10):
- Real-time detection of suspicious patterns
- Email and admin notifications
- Audit logging for all alerts
- User-facing security alerts

Example:
    >>> from syntek_monitoring.services.suspicious_activity_service import SuspiciousActivityService
    >>> SuspiciousActivityService.check_login_location(user, ip_address)
    >>> SuspiciousActivityService.alert_password_change(user)
    >>> SuspiciousActivityService.alert_2fa_disabled(user)
"""

import hashlib
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.http import HttpRequest

logger = logging.getLogger("security.suspicious_activity")


class SuspiciousActivityService:
    """Service for detecting and alerting on suspicious security events.

    Monitors user activity for anomalies and triggers alerts when
    suspicious patterns are detected.

    Detection Patterns:
    - New login location (IP address not seen in last 30 days)
    - Password change from new location
    - 2FA disable from new location
    - Rapid failed login attempts
    - Session from unusual device

    Attributes:
        KNOWN_IP_CACHE_PREFIX: Redis key prefix for known IPs.
        KNOWN_IP_RETENTION_DAYS: Days to remember known IPs.
    """

    KNOWN_IP_CACHE_PREFIX = "known_ip"
    KNOWN_IP_RETENTION_DAYS = 30

    @staticmethod
    def _get_known_ips_key(user: AbstractUser) -> str:
        """Generate cache key for user's known IP addresses.

        Args:
            user: User to generate key for.

        Returns:
            Cache key for known IPs.

        Example:
            >>> key = SuspiciousActivityService._get_known_ips_key(user)
            >>> key.startswith("known_ip:")
            True
        """
        return f"{SuspiciousActivityService.KNOWN_IP_CACHE_PREFIX}:{user.id}"  # type: ignore[attr-defined]

    @staticmethod
    def _hash_ip(ip_address: str) -> str:
        """Hash IP address for privacy in cache.

        Uses SHA-256 to hash IP addresses before storing in cache,
        preventing exposure of actual IP addresses in Redis.

        Args:
            ip_address: IP address to hash.

        Returns:
            SHA-256 hash of IP (first 16 chars for storage efficiency).

        Example:
            >>> hashed = SuspiciousActivityService._hash_ip("192.168.1.1")
            >>> len(hashed)
            16
        """
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

    @staticmethod
    def is_known_ip(user: AbstractUser, ip_address: str) -> bool:
        """Check if IP address is known for this user.

        Args:
            user: User to check.
            ip_address: IP address to verify.

        Returns:
            True if IP has been used in the last KNOWN_IP_RETENTION_DAYS.

        Example:
            >>> SuspiciousActivityService.is_known_ip(user, "192.168.1.1")
            False
        """
        cache_key = SuspiciousActivityService._get_known_ips_key(user)
        known_ips = cache.get(cache_key, set())

        ip_hash = SuspiciousActivityService._hash_ip(ip_address)
        return ip_hash in known_ips

    @staticmethod
    def mark_ip_as_known(user: AbstractUser, ip_address: str) -> None:
        """Mark an IP address as known for this user.

        Adds the IP hash to the user's known IPs cache with retention period.

        Args:
            user: User to mark IP for.
            ip_address: IP address to mark as known.

        Example:
            >>> SuspiciousActivityService.mark_ip_as_known(user, "192.168.1.1")
            >>> SuspiciousActivityService.is_known_ip(user, "192.168.1.1")
            True
        """
        cache_key = SuspiciousActivityService._get_known_ips_key(user)
        known_ips = cache.get(cache_key, set())

        ip_hash = SuspiciousActivityService._hash_ip(ip_address)
        known_ips.add(ip_hash)

        # Store with retention period (convert days to seconds)
        timeout = SuspiciousActivityService.KNOWN_IP_RETENTION_DAYS * 86400
        cache.set(cache_key, known_ips, timeout=timeout)

    @staticmethod
    def check_login_location(
        user: AbstractUser, ip_address: str, request: HttpRequest | None = None
    ) -> bool:
        """Check if login is from a new location.

        Triggers alert if IP is not in the known list.

        Args:
            user: User logging in.
            ip_address: IP address of login attempt.
            request: Optional HTTP request for additional context.

        Returns:
            True if this is a new location (alert sent), False if known.

        Example:
            >>> is_new = SuspiciousActivityService.check_login_location(
            ...     user, "192.168.1.1", request
            ... )
            >>> is_new
            True  # First time from this IP
        """
        if SuspiciousActivityService.is_known_ip(user, ip_address):
            # Known location, no alert needed
            SuspiciousActivityService.mark_ip_as_known(user, ip_address)
            return False

        # New location detected - send alert
        logger.warning(
            f"Login from new location detected for {user.email}",
            extra={
                "user_id": user.id,  # type: ignore[attr-defined]
                "user_email": user.email,
                "ip_address": ip_address,
                "user_agent": request.headers.get("user-agent", "") if request else "",  # type: ignore[attr-defined]
            },
        )

        # Log to audit trail (if audit module is installed)
        try:
            from syntek_audit.services.audit_service import AuditService  # type: ignore[import]

            AuditService.log_event(
                action="login_new_location",
                user=user,
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent", "") if request else "",  # type: ignore[attr-defined]
                metadata={
                    "alert_type": "new_location",
                    "severity": "medium",
                },
            )
        except ImportError:
            # Audit module not installed, skip audit logging
            pass

        # Send email notification
        SuspiciousActivityService._send_alert_email(
            user=user,
            subject="New login location detected",
            message=(
                f"A login to your account was detected from a new location.\n\n"
                f"If this was you, no action is needed. Your device will be remembered.\n\n"
                f"If this wasn't you, please change your password immediately and enable two-factor authentication.\n\n"
                f"Location details:\n"
                f"- Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"- IP Address: {ip_address}\n"
                f"- Device: {request.headers.get('user-agent', 'Unknown') if request else 'Unknown'}"  # type: ignore[attr-defined]
            ),
        )

        # Mark as known for future logins
        SuspiciousActivityService.mark_ip_as_known(user, ip_address)

        return True

    @staticmethod
    def alert_password_change(
        user: AbstractUser, ip_address: str = "", request: HttpRequest | None = None
    ) -> None:
        """Alert user that their password was changed.

        Args:
            user: User whose password was changed.
            ip_address: IP address where change occurred.
            request: Optional HTTP request for additional context.

        Example:
            >>> SuspiciousActivityService.alert_password_change(
            ...     user, "192.168.1.1", request
            ... )
        """
        logger.info(
            f"Password changed for {user.email}",
            extra={
                "user_id": user.id,  # type: ignore[attr-defined]
                "user_email": user.email,
                "ip_address": ip_address,
            },
        )

        # Log to audit trail (if audit module is installed)
        try:
            from syntek_audit.services.audit_service import AuditService  # type: ignore[import]

            AuditService.log_event(
                action="password_change",
                user=user,
                ip_address=ip_address,
                metadata={
                    "alert_type": "password_change",
                    "severity": "high",
                },
            )
        except ImportError:
            pass

        # Send email notification
        SuspiciousActivityService._send_alert_email(
            user=user,
            subject="Password changed",
            message=(
                f"Your account password was recently changed.\n\n"
                f"If you made this change, no action is needed.\n\n"
                f"If you did NOT change your password, your account may be compromised. "
                f"Please contact support immediately.\n\n"
                f"Change details:\n"
                f"- Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"- IP Address: {ip_address or 'Unknown'}\n"
                f"- Device: {request.headers.get('user-agent', 'Unknown') if request else 'Unknown'}"  # type: ignore[attr-defined]
            ),
        )

    @staticmethod
    def alert_2fa_disabled(
        user: AbstractUser, ip_address: str = "", request: HttpRequest | None = None
    ) -> None:
        """Alert user that 2FA was disabled.

        Args:
            user: User whose 2FA was disabled.
            ip_address: IP address where change occurred.
            request: Optional HTTP request for additional context.

        Example:
            >>> SuspiciousActivityService.alert_2fa_disabled(
            ...     user, "192.168.1.1", request
            ... )
        """
        logger.warning(
            f"Two-factor authentication disabled for {user.email}",
            extra={
                "user_id": user.id,  # type: ignore[attr-defined]
                "user_email": user.email,
                "ip_address": ip_address,
            },
        )

        # Log to audit trail (if audit module is installed)
        try:
            from syntek_audit.services.audit_service import AuditService  # type: ignore[import]

            AuditService.log_event(
                action="two_factor_disabled",
                user=user,
                ip_address=ip_address,
                metadata={
                    "alert_type": "2fa_disabled",
                    "severity": "high",
                },
            )
        except ImportError:
            pass

        # Send email notification
        SuspiciousActivityService._send_alert_email(
            user=user,
            subject="Two-factor authentication disabled",
            message=(
                f"Two-factor authentication (2FA) was disabled on your account.\n\n"
                f"If you made this change, please note that your account is now less secure. "
                f"We strongly recommend re-enabling 2FA.\n\n"
                f"If you did NOT disable 2FA, your account may be compromised. "
                f"Please enable 2FA immediately and change your password.\n\n"
                f"Change details:\n"
                f"- Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"- IP Address: {ip_address or 'Unknown'}\n"
                f"- Device: {request.headers.get('user-agent', 'Unknown') if request else 'Unknown'}"  # type: ignore[attr-defined]
            ),
        )

    @staticmethod
    def alert_2fa_enabled(user: AbstractUser, ip_address: str = "") -> None:
        """Alert user that 2FA was enabled.

        Args:
            user: User whose 2FA was enabled.
            ip_address: IP address where change occurred.

        Example:
            >>> SuspiciousActivityService.alert_2fa_enabled(user, "192.168.1.1")
        """
        logger.info(
            f"Two-factor authentication enabled for {user.email}",
            extra={
                "user_id": user.id,  # type: ignore[attr-defined]
                "user_email": user.email,
                "ip_address": ip_address,
            },
        )

        # Send email notification
        SuspiciousActivityService._send_alert_email(
            user=user,
            subject="Two-factor authentication enabled",
            message=(
                f"Two-factor authentication (2FA) has been enabled on your account.\n\n"
                f"Your account is now more secure. You'll be prompted for a verification code "
                f"when logging in from new devices.\n\n"
                f"If you did not enable 2FA, please contact support immediately.\n\n"
                f"Change details:\n"
                f"- Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"- IP Address: {ip_address or 'Unknown'}"
            ),
        )

    @staticmethod
    def alert_account_locked(user: AbstractUser, failure_count: int, lockout_minutes: int) -> None:
        """Alert user that their account was locked due to failed attempts.

        Args:
            user: User whose account was locked.
            failure_count: Number of failed attempts.
            lockout_minutes: Lockout duration in minutes.

        Example:
            >>> SuspiciousActivityService.alert_account_locked(user, 5, 15)
        """
        logger.warning(
            f"Account locked for {user.email} after {failure_count} failed attempts",
            extra={
                "user_id": user.id,  # type: ignore[attr-defined]
                "user_email": user.email,
                "failures": failure_count,
                "lockout_minutes": lockout_minutes,
            },
        )

        # Send email notification
        SuspiciousActivityService._send_alert_email(
            user=user,
            subject="Account temporarily locked",
            message=(
                f"Your account has been temporarily locked due to multiple failed login attempts.\n\n"
                f"Failed attempts: {failure_count}\n"
                f"Lockout duration: {lockout_minutes} minutes\n\n"
                f"If this was you, please wait {lockout_minutes} minutes before trying again.\n\n"
                f"If you did not attempt to log in, your account may be under attack. "
                f"Please ensure you have a strong password and enable two-factor authentication.\n\n"
                f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
            ),
        )

    @staticmethod
    def _send_alert_email(user: AbstractUser, subject: str, message: str) -> None:
        """Send security alert email to user.

        Attempts to use the email service if installed, otherwise logs the alert.

        Args:
            user: User to notify.
            subject: Email subject.
            message: Email body.

        Example:
            >>> SuspiciousActivityService._send_alert_email(
            ...     user, "Security Alert", "Your password was changed"
            ... )
        """
        try:
            # Try to use email service if available
            from django.core.mail import send_mail  # type: ignore[import]

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "SECURITY_EMAIL_FROM", settings.DEFAULT_FROM_EMAIL),
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(
                f"Failed to send security alert email to {user.email}",
                extra={
                    "user_id": user.id,  # type: ignore[attr-defined]
                    "user_email": user.email,
                    "error": str(e),
                },
            )
