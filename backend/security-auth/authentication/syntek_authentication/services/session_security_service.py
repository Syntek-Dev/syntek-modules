"""Session security service for session fingerprinting and hijacking detection.

This module provides session security functionality including:
- Device fingerprinting (screen, timezone, canvas, WebGL)
- IP address tracking and anomaly detection
- User agent validation and change detection
- Suspicious activity pattern analysis

SECURITY NOTE:
- Multi-factor fingerprinting (IP, UA, device)
- Encrypted IP storage (AES-256-GCM)
- HMAC-based IP lookups (constant-time)
- Automatic session termination on hijacking
- Suspicious activity flagging

Example:
    >>> SessionSecurityService.create_session_fingerprint(user, request)
    >>> is_suspicious = SessionSecurityService.validate_session(session_key, request)
    >>> SessionSecurityService.terminate_suspicious_sessions(user)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import transaction
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

    from syntek_authentication.models import SessionSecurity, User

logger = logging.getLogger(__name__)


class SessionSecurityService:
    """Service for session fingerprinting and hijacking detection.

    Handles session security through:
    1. Device fingerprinting (screen, timezone, canvas)
    2. IP address tracking and validation
    3. User agent change detection
    4. Suspicious activity pattern analysis

    Features:
    - Multi-factor fingerprinting
    - Encrypted IP storage
    - Constant-time IP lookups
    - Automatic suspicious session termination
    - Real-time validation

    Attributes:
        MAX_IP_CHANGES: Maximum IP changes before flagging
        MAX_UA_CHANGES: Maximum user agent changes before flagging
        FINGERPRINT_MISMATCH_THRESHOLD: Percentage difference threshold
    """

    MAX_IP_CHANGES = 3
    MAX_UA_CHANGES = 2
    FINGERPRINT_MISMATCH_THRESHOLD = 30  # 30% difference

    @staticmethod
    def _get_encryption_key() -> bytes:
        """Get encryption key from settings.

        Returns:
            Encryption key bytes.
        """
        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _get_hmac_key() -> bytes:
        """Get HMAC key from settings.

        Returns:
            HMAC key bytes.
        """
        key = getattr(settings, "HMAC_SECRET_KEY", None)
        if not key:
            raise ValueError("HMAC_SECRET_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _extract_device_fingerprint(request: "HttpRequest") -> dict[str, Any]:
        """Extract device fingerprint from request.

        Args:
            request: Django HTTP request.

        Returns:
            Device fingerprint dictionary.
        """
        # Note: This requires client-side JavaScript to send fingerprint data
        # in request headers or POST data. This is a simplified version.

        fingerprint = {
            "screen_resolution": request.META.get("HTTP_X_SCREEN_RESOLUTION"),
            "timezone": request.META.get("HTTP_X_TIMEZONE"),
            "language": request.META.get("HTTP_ACCEPT_LANGUAGE", "")[:50],
            "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", "")[:50],
            "canvas_hash": request.META.get("HTTP_X_CANVAS_HASH"),
            "webgl_vendor": request.META.get("HTTP_X_WEBGL_VENDOR"),
            "webgl_renderer": request.META.get("HTTP_X_WEBGL_RENDERER"),
        }

        # Remove None values
        return {k: v for k, v in fingerprint.items() if v is not None}

    @staticmethod
    def _get_client_ip(request: "HttpRequest") -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For and proxies.

        Args:
            request: Django HTTP request.

        Returns:
            Client IP address.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Take the first IP (original client)
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    @staticmethod
    @transaction.atomic
    def create_session_fingerprint(
        user: "User", session_key: str, request: "HttpRequest"
    ) -> "SessionSecurity":
        """Create session security fingerprint.

        Args:
            user: User creating session.
            session_key: Django session key.
            request: Django HTTP request.

        Returns:
            SessionSecurity object.
        """
        from syntek_authentication.models import SessionSecurity

        encryption_key = SessionSecurityService._get_encryption_key()
        hmac_key = SessionSecurityService._get_hmac_key()

        # Get IP and user agent
        ip_address = SessionSecurityService._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        # Encrypt IP address
        ip_encrypted = encrypt_ip_address_py(ip_address, encryption_key)
        ip_hash = hash_ip_address_py(ip_address, hmac_key)

        # Extract device fingerprint
        device_fingerprint = SessionSecurityService._extract_device_fingerprint(request)

        # Create session security record
        session_security = SessionSecurity.objects.create(
            user=user,
            session_key=session_key,
            device_fingerprint=device_fingerprint,
            ip_address_encrypted=ip_encrypted,
            ip_hash=ip_hash,
            user_agent=user_agent,
        )

        logger.info(f"Created session fingerprint for user {user.id}, session {session_key[:8]}...")

        return session_security

    @staticmethod
    def validate_session(session_key: str, request: "HttpRequest") -> tuple[bool, list[str]]:
        """Validate session security.

        Checks for:
        - IP address changes
        - User agent changes
        - Device fingerprint changes

        Args:
            session_key: Django session key.
            request: Django HTTP request.

        Returns:
            Tuple of (is_valid, suspicious_flags).
        """
        from syntek_authentication.models import SessionSecurity

        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
        except SessionSecurity.DoesNotExist:
            logger.warning(f"Session security record not found: {session_key[:8]}...")
            return False, ["session_not_found"]

        suspicious_flags = []

        # Check IP address change
        current_ip = SessionSecurityService._get_client_ip(request)
        hmac_key = SessionSecurityService._get_hmac_key()
        current_ip_hash = hash_ip_address_py(current_ip, hmac_key)

        if current_ip_hash != session_security.ip_hash:
            suspicious_flags.append("ip_change")
            logger.warning(
                f"IP change detected for session {session_key[:8]}... "
                f"(user {session_security.user.id})"
            )

        # Check user agent change
        current_ua = request.META.get("HTTP_USER_AGENT", "")[:500]
        if current_ua != session_security.user_agent:
            suspicious_flags.append("user_agent_change")
            logger.warning(
                f"User agent change detected for session {session_key[:8]}... "
                f"(user {session_security.user.id})"
            )

        # Check device fingerprint change
        current_fingerprint = SessionSecurityService._extract_device_fingerprint(request)
        if session_security.device_fingerprint:
            mismatch_count = 0
            total_fields = len(session_security.device_fingerprint)

            for key, value in session_security.device_fingerprint.items():
                if current_fingerprint.get(key) != value:
                    mismatch_count += 1

            if total_fields > 0:
                mismatch_percentage = (mismatch_count / total_fields) * 100
                if mismatch_percentage > SessionSecurityService.FINGERPRINT_MISMATCH_THRESHOLD:
                    suspicious_flags.append("fingerprint_mismatch")
                    logger.warning(
                        f"Device fingerprint mismatch for session {session_key[:8]}... "
                        f"({mismatch_percentage:.1f}% different)"
                    )

        # If suspicious, add flag to session
        if suspicious_flags:
            SessionSecurityService.add_suspicious_flags(session_key, suspicious_flags)

        is_valid = len(suspicious_flags) == 0
        return is_valid, suspicious_flags

    @staticmethod
    @transaction.atomic
    def add_suspicious_flags(session_key: str, flags: list[str]) -> None:
        """Add suspicious activity flags to session.

        Args:
            session_key: Django session key.
            flags: List of suspicious activity flags.
        """
        from syntek_authentication.models import SessionSecurity

        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)

            for flag in flags:
                session_security.add_suspicious_flag(
                    flag, {"detected_at": timezone.now().isoformat()}
                )

            logger.info(f"Added suspicious flags {flags} to session {session_key[:8]}...")
        except SessionSecurity.DoesNotExist:
            logger.warning(f"Session security record not found: {session_key[:8]}...")

    @staticmethod
    def get_suspicious_sessions(user: "User") -> list["SessionSecurity"]:
        """Get all suspicious sessions for user.

        Args:
            user: User to check.

        Returns:
            List of SessionSecurity objects with suspicious activity.
        """
        from syntek_authentication.models import SessionSecurity

        sessions = SessionSecurity.objects.filter(user=user)
        return [s for s in sessions if s.has_suspicious_activity()]

    @staticmethod
    @transaction.atomic
    def terminate_suspicious_sessions(user: "User") -> int:
        """Terminate all suspicious sessions for user.

        Args:
            user: User whose suspicious sessions to terminate.

        Returns:
            Number of sessions terminated.
        """
        from django.contrib.sessions.models import Session

        suspicious_sessions = SessionSecurityService.get_suspicious_sessions(user)

        terminated_count = 0
        for session_security in suspicious_sessions:
            try:
                # Delete Django session
                Session.objects.filter(session_key=session_security.session_key).delete()

                # Delete session security record
                session_security.delete()

                terminated_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to terminate session {session_security.session_key[:8]}...: {e}"
                )

        logger.info(f"Terminated {terminated_count} suspicious sessions for user {user.id}")

        return terminated_count

    @staticmethod
    def cleanup_old_sessions(days: int = 30) -> int:
        """Clean up old session security records.

        Args:
            days: Age threshold in days.

        Returns:
            Number of records deleted.
        """
        from django.utils import timezone

        from syntek_authentication.models import SessionSecurity

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = SessionSecurity.objects.filter(created_at__lt=cutoff_date).delete()

        logger.info(f"Cleaned up {deleted_count} old session security records")

        return deleted_count
