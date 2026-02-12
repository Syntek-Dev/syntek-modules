"""Concurrent session management service.

This module provides functionality to manage concurrent user sessions,
enforce session limits, and handle session termination.

SECURITY NOTE (M7):
- Configurable max sessions per user
- Auto-terminate oldest session when limit exceeded
- Device fingerprinting for session tracking
- Real-time session activity monitoring

Example:
    >>> SessionManagementService.enforce_session_limit(user)
    >>> active_sessions = SessionManagementService.get_active_sessions(user)
    >>> SessionManagementService.revoke_session(session_id)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from syntek_authentication.models import User  # type: ignore[import]
    from syntek_sessions.models import SessionToken  # type: ignore[import]

logger = logging.getLogger(__name__)


class SessionManagementService:
    """Service for managing concurrent user sessions.

    Implements session limit enforcement, activity tracking, and
    session termination for security and compliance.

    Security Features:
    - Configurable max sessions per user
    - Automatic oldest-session termination
    - Device-based session tracking
    - Activity-based session cleanup

    Attributes:
        DEFAULT_MAX_SESSIONS: Default maximum sessions per user
        SESSION_IDLE_TIMEOUT_HOURS: Hours before idle session expires
    """

    DEFAULT_MAX_SESSIONS = 5
    SESSION_IDLE_TIMEOUT_HOURS = 24

    @staticmethod
    def get_max_sessions_per_user() -> int:
        """Get configured maximum sessions per user.

        Returns:
            Maximum number of concurrent sessions allowed per user.
        """
        return getattr(
            settings,
            "MAX_CONCURRENT_SESSIONS_PER_USER",
            SessionManagementService.DEFAULT_MAX_SESSIONS,
        )

    @staticmethod
    def get_active_sessions(user: "User") -> list["SessionToken"]:
        """Get all active sessions for a user.

        Active sessions are those that are:
        - Not expired
        - Not revoked
        - Not marked as used

        Args:
            user: User to get sessions for.

        Returns:
            List of active SessionToken instances, ordered by last activity.
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        return list(
            SessionToken.objects.filter(
                user=user,
                expires_at__gt=timezone.now(),
                is_revoked=False,
                used=False,
            )
            .order_by("-last_activity_at")
            .select_related("user")
        )

    @staticmethod
    def get_session_count(user: "User") -> int:
        """Get count of active sessions for a user.

        Args:
            user: User to count sessions for.

        Returns:
            Number of active sessions.
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        return SessionToken.objects.filter(
            user=user,
            expires_at__gt=timezone.now(),
            is_revoked=False,
            used=False,
        ).count()

    @staticmethod
    @transaction.atomic
    def enforce_session_limit(user: "User") -> dict:
        """Enforce concurrent session limit for a user.

        If user has more active sessions than allowed, revokes the
        oldest sessions (by last_activity_at) until the limit is met.

        Args:
            user: User to enforce session limit for.

        Returns:
            Dictionary with enforcement statistics:
                {
                    'active_sessions': int,
                    'sessions_revoked': int,
                    'revoked_session_ids': list[str],
                }
        """
        max_sessions = SessionManagementService.get_max_sessions_per_user()
        active_sessions = SessionManagementService.get_active_sessions(user)
        active_count = len(active_sessions)

        if active_count <= max_sessions:
            return {
                "active_sessions": active_count,
                "sessions_revoked": 0,
                "revoked_session_ids": [],
            }

        # Calculate how many sessions to revoke
        sessions_to_revoke = active_count - max_sessions

        # Get oldest sessions (by last_activity_at)
        sessions_to_terminate = active_sessions[-sessions_to_revoke:]

        # Revoke the oldest sessions
        revoked_ids = []
        for session in sessions_to_terminate:
            session.revoke()
            revoked_ids.append(str(session.id))

        logger.info(
            f"Enforced session limit for user {user.email}: "
            f"revoked {len(revoked_ids)} oldest sessions",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "sessions_revoked": len(revoked_ids),
                "max_sessions": max_sessions,
            },
        )

        return {
            "active_sessions": max_sessions,
            "sessions_revoked": len(revoked_ids),
            "revoked_session_ids": revoked_ids,
        }

    @staticmethod
    def revoke_session(session_id: str, user: "User | None" = None) -> bool:
        """Revoke a specific session.

        Args:
            session_id: UUID of the session to revoke.
            user: Optional user for permission check (only revoke own sessions).

        Returns:
            True if session was revoked, False if not found or unauthorized.
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        try:
            filters = {"id": session_id, "is_revoked": False}
            if user:
                filters["user"] = user

            session = SessionToken.objects.get(**filters)
            session.revoke()

            logger.info(
                f"Session {session_id} revoked",
                extra={
                    "session_id": session_id,
                    "user_id": session.user.id if session.user else None,
                },
            )

            return True
        except SessionToken.DoesNotExist:
            logger.warning(
                f"Attempt to revoke non-existent or unauthorized session {session_id}",
                extra={"session_id": session_id, "user_id": user.id if user else None},
            )
            return False

    @staticmethod
    def revoke_all_user_sessions(user: "User", except_session_id: str | None = None) -> int:
        """Revoke all sessions for a user.

        Useful for:
        - Password change (security requirement H8)
        - Account compromise response
        - User-initiated "log out all devices"

        Args:
            user: User whose sessions should be revoked.
            except_session_id: Optional session ID to keep active (current session).

        Returns:
            Number of sessions revoked.
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        filters = {"user": user, "is_revoked": False}
        if except_session_id:
            sessions = SessionToken.objects.filter(**filters).exclude(id=except_session_id)
        else:
            sessions = SessionToken.objects.filter(**filters)

        count = sessions.count()

        # Revoke all sessions
        sessions.update(is_revoked=True, revoked_at=timezone.now())

        logger.info(
            f"Revoked all sessions for user {user.email}",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "sessions_revoked": count,
                "except_session_id": except_session_id,
            },
        )

        return count

    @staticmethod
    def cleanup_idle_sessions() -> int:
        """Clean up idle sessions that haven't been used recently.

        Revokes sessions that haven't had activity in SESSION_IDLE_TIMEOUT_HOURS.
        This is typically run as a periodic task (e.g., daily cron job).

        Returns:
            Number of idle sessions cleaned up.
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        timeout = timedelta(hours=SessionManagementService.SESSION_IDLE_TIMEOUT_HOURS)
        cutoff_time = timezone.now() - timeout

        idle_sessions = SessionToken.objects.filter(
            last_activity_at__lt=cutoff_time,
            is_revoked=False,
        )

        count = idle_sessions.count()
        idle_sessions.update(is_revoked=True, revoked_at=timezone.now())

        logger.info(
            f"Cleaned up {count} idle sessions",
            extra={
                "sessions_cleaned": count,
                "idle_timeout_hours": SessionManagementService.SESSION_IDLE_TIMEOUT_HOURS,
            },
        )

        return count

    @staticmethod
    def get_session_details(session_id: str, user: "User") -> dict | None:
        """Get detailed information about a session.

        Args:
            session_id: UUID of the session.
            user: User requesting the information (must own the session).

        Returns:
            Dictionary with session details or None if not found/unauthorized:
                {
                    'id': str,
                    'created_at': datetime,
                    'last_activity_at': datetime,
                    'expires_at': datetime,
                    'device_fingerprint': str,
                    'user_agent': str,
                    'is_current': bool,
                }
        """
        from syntek_sessions.models import SessionToken  # type: ignore[import]

        try:
            session = SessionToken.objects.get(
                id=session_id,
                user=user,
                is_revoked=False,
            )

            return {
                "id": str(session.id),
                "created_at": session.created_at,
                "last_activity_at": session.last_activity_at,
                "expires_at": session.expires_at,
                "device_fingerprint": session.device_fingerprint,
                "user_agent": session.user_agent,
                "is_current": False,  # This should be determined by the caller
            }
        except SessionToken.DoesNotExist:
            return None
