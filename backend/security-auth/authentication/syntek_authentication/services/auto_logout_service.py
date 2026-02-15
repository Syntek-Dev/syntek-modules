"""
Auto-logout service for session timeout management.

Handles idle timeouts, absolute timeouts, and "Remember Me" functionality.
"""

from datetime import timedelta
from typing import Optional

from django.contrib.sessions.models import Session
from django.utils import timezone

from ..models import SessionSecurity


class AutoLogoutService:
    """Service for managing automatic logout based on activity."""

    # Default timeouts (in seconds)
    DEFAULT_IDLE_TIMEOUT = 1800  # 30 minutes
    DEFAULT_ABSOLUTE_TIMEOUT = 43200  # 12 hours
    REMEMBER_ME_IDLE_TIMEOUT = 2592000  # 30 days

    # Warning time before auto-logout (in seconds)
    WARNING_TIME = 300  # 5 minutes

    @staticmethod
    def update_activity(session_key: str) -> bool:
        """
        Update last activity timestamp for a session.

        Args:
            session_key: Django session key

        Returns:
            bool: True if session was updated, False if not found
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
            session_security.activity_count += 1
            session_security.save(update_fields=["last_activity_at", "activity_count"])
            return True
        except SessionSecurity.DoesNotExist:
            return False

    @staticmethod
    def check_session_timeout(session_key: str) -> tuple[bool, Optional[str]]:
        """
        Check if session has timed out.

        Args:
            session_key: Django session key

        Returns:
            tuple: (is_expired, reason)
                - is_expired: True if session should be terminated
                - reason: Reason for expiry (idle_timeout, absolute_timeout, None)
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
        except SessionSecurity.DoesNotExist:
            return True, "session_not_found"

        now = timezone.now()

        # Check absolute timeout
        if session_security.absolute_timeout_at and now >= session_security.absolute_timeout_at:
            return True, "absolute_timeout"

        # Check idle timeout (if configured)
        if session_security.idle_timeout_seconds > 0:
            idle_timeout = timedelta(seconds=session_security.idle_timeout_seconds)
            idle_expiry = session_security.last_activity_at + idle_timeout

            if now >= idle_expiry:
                return True, "idle_timeout"

        return False, None

    @staticmethod
    def should_show_warning(session_key: str) -> bool:
        """
        Check if auto-logout warning should be shown to user.

        Warning is shown WARNING_TIME seconds before idle timeout.

        Args:
            session_key: Django session key

        Returns:
            bool: True if warning should be shown
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
        except SessionSecurity.DoesNotExist:
            return False

        # Don't show warning if already warned recently
        if session_security.auto_logout_warned_at:
            time_since_warning = timezone.now() - session_security.auto_logout_warned_at
            if time_since_warning.total_seconds() < AutoLogoutService.WARNING_TIME:
                return False

        # Calculate time until idle timeout
        if session_security.idle_timeout_seconds > 0:
            idle_timeout = timedelta(seconds=session_security.idle_timeout_seconds)
            idle_expiry = session_security.last_activity_at + idle_timeout
            time_until_expiry = (idle_expiry - timezone.now()).total_seconds()

            # Show warning if within WARNING_TIME seconds of expiry
            if 0 < time_until_expiry <= AutoLogoutService.WARNING_TIME:
                # Mark as warned
                session_security.auto_logout_warned_at = timezone.now()
                session_security.save(update_fields=["auto_logout_warned_at"])
                return True

        return False

    @staticmethod
    def get_time_until_timeout(session_key: str) -> Optional[int]:
        """
        Get seconds until session timeout.

        Args:
            session_key: Django session key

        Returns:
            int: Seconds until timeout, or None if no timeout configured
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
        except SessionSecurity.DoesNotExist:
            return 0

        now = timezone.now()
        time_until_expiry = None

        # Check absolute timeout
        if session_security.absolute_timeout_at:
            absolute_remaining = (session_security.absolute_timeout_at - now).total_seconds()
            time_until_expiry = absolute_remaining

        # Check idle timeout
        if session_security.idle_timeout_seconds > 0:
            idle_timeout = timedelta(seconds=session_security.idle_timeout_seconds)
            idle_expiry = session_security.last_activity_at + idle_timeout
            idle_remaining = (idle_expiry - now).total_seconds()

            # Use whichever timeout is sooner
            if time_until_expiry is None or idle_remaining < time_until_expiry:
                time_until_expiry = idle_remaining

        return max(0, int(time_until_expiry)) if time_until_expiry else None

    @staticmethod
    def enable_remember_me(session_key: str) -> bool:
        """
        Enable "Remember Me" for a session.

        Extends idle timeout to REMEMBER_ME_IDLE_TIMEOUT (30 days).

        Args:
            session_key: Django session key

        Returns:
            bool: True if successful, False if session not found
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
            session_security.remember_me = True
            session_security.idle_timeout_seconds = AutoLogoutService.REMEMBER_ME_IDLE_TIMEOUT
            session_security.save(update_fields=["remember_me", "idle_timeout_seconds"])
            return True
        except SessionSecurity.DoesNotExist:
            return False

    @staticmethod
    def disable_remember_me(session_key: str) -> bool:
        """
        Disable "Remember Me" for a session.

        Resets idle timeout to DEFAULT_IDLE_TIMEOUT (30 minutes).

        Args:
            session_key: Django session key

        Returns:
            bool: True if successful, False if session not found
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
            session_security.remember_me = False
            session_security.idle_timeout_seconds = AutoLogoutService.DEFAULT_IDLE_TIMEOUT
            session_security.save(update_fields=["remember_me", "idle_timeout_seconds"])
            return True
        except SessionSecurity.DoesNotExist:
            return False

    @staticmethod
    def set_custom_timeouts(
        session_key: str,
        idle_timeout_seconds: Optional[int] = None,
        absolute_timeout_at: Optional[timezone.datetime] = None,
    ) -> bool:
        """
        Set custom timeouts for a session.

        Args:
            session_key: Django session key
            idle_timeout_seconds: Custom idle timeout in seconds (None = no change)
            absolute_timeout_at: Custom absolute timeout timestamp (None = no change)

        Returns:
            bool: True if successful, False if session not found
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)

            if idle_timeout_seconds is not None:
                session_security.idle_timeout_seconds = idle_timeout_seconds

            if absolute_timeout_at is not None:
                session_security.absolute_timeout_at = absolute_timeout_at

            session_security.save()
            return True
        except SessionSecurity.DoesNotExist:
            return False

    @staticmethod
    def cleanup_expired_sessions():
        """
        Clean up expired sessions.

        Should be run periodically (e.g., via cron or Celery task).
        Deletes Django sessions and SessionSecurity records for expired sessions.
        """
        now = timezone.now()

        # Find expired sessions (idle timeout or absolute timeout)
        expired_sessions = []

        for session_security in SessionSecurity.objects.all():
            # Check absolute timeout
            if session_security.absolute_timeout_at and now >= session_security.absolute_timeout_at:
                expired_sessions.append(session_security.session_key)
                continue

            # Check idle timeout
            if session_security.idle_timeout_seconds > 0:
                idle_timeout = timedelta(seconds=session_security.idle_timeout_seconds)
                idle_expiry = session_security.last_activity_at + idle_timeout

                if now >= idle_expiry:
                    expired_sessions.append(session_security.session_key)

        # Delete expired sessions
        if expired_sessions:
            Session.objects.filter(session_key__in=expired_sessions).delete()
            SessionSecurity.objects.filter(session_key__in=expired_sessions).delete()

        return len(expired_sessions)

    @staticmethod
    def get_session_status(session_key: str) -> dict:
        """
        Get comprehensive session status.

        Args:
            session_key: Django session key

        Returns:
            dict: Session status information
        """
        try:
            session_security = SessionSecurity.objects.get(session_key=session_key)
        except SessionSecurity.DoesNotExist:
            return {"exists": False}

        is_expired, reason = AutoLogoutService.check_session_timeout(session_key)
        time_until_timeout = AutoLogoutService.get_time_until_timeout(session_key)
        should_warn = AutoLogoutService.should_show_warning(session_key)

        return {
            "exists": True,
            "is_expired": is_expired,
            "expiry_reason": reason,
            "time_until_timeout": time_until_timeout,
            "should_show_warning": should_warn,
            "remember_me": session_security.remember_me,
            "idle_timeout_seconds": session_security.idle_timeout_seconds,
            "absolute_timeout_at": session_security.absolute_timeout_at,
            "last_activity_at": session_security.last_activity_at,
            "activity_count": session_security.activity_count,
        }
