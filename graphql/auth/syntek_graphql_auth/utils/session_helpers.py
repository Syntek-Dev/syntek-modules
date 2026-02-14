"""Session management helpers for authentication mutations.

Provides utilities for tracking active sessions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone as tz

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def get_active_session_count(user: User) -> int:
    """Get count of active sessions for user.

    Args:
        user: User to get session count for

    Returns:
        int: Number of active (non-revoked, non-expired) sessions
    """
    from apps.core.models import SessionToken  # type: ignore[import]

    return SessionToken.objects.filter(
        user=user,
        is_revoked=False,
        expires_at__gt=tz.now(),
    ).count()
