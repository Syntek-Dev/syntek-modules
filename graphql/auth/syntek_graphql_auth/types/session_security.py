"""GraphQL types for session security and hijacking detection.

This module defines types for session fingerprinting, suspicious pattern detection,
and auto-logout management.
"""

from __future__ import annotations

import strawberry


@strawberry.input
class UpdateSessionActivityInput:
    """Input for updating session activity timestamp.

    Attributes:
        session_key: Django session key (optional, uses current session if not provided)
    """

    session_key: str | None = None


@strawberry.type
class SessionSecurityType:
    """GraphQL type for session security information.

    Represents security monitoring data for a user session.

    Attributes:
        id: Entry UUID
        session_key: Django session key (truncated for display)
        device_fingerprint: Device characteristics summary
        ip_address_decrypted: Decrypted IP address (only for authorized users)
        user_agent: Browser/device user agent
        last_activity_at: Timestamp of last activity
        created_at: Session creation timestamp
        suspicious_patterns: List of detected suspicious patterns
        risk_score: Calculated risk score (0-100, higher = more suspicious)
        device_changes: List of detected device/location changes
        idle_timeout_seconds: Idle timeout in seconds
        absolute_timeout_at: Absolute timeout timestamp (null if no limit)
        remember_me: Whether "Remember Me" is enabled
        is_current: Whether this is the current session
    """

    id: strawberry.ID
    session_key: str  # Truncated to first 8 chars
    device_fingerprint: str  # JSON string or summary
    ip_address_decrypted: str | None = None
    user_agent: str
    last_activity_at: str
    created_at: str
    suspicious_patterns: list[str]
    risk_score: int  # 0-100
    device_changes: list[str]
    idle_timeout_seconds: int
    absolute_timeout_at: str | None = None
    remember_me: bool
    is_current: bool


@strawberry.type
class SessionStatusType:
    """Status information for current session.

    Provides information about session timeout and activity.

    Attributes:
        is_active: Whether session is active
        last_activity_at: Timestamp of last activity
        idle_timeout_seconds: Idle timeout in seconds
        absolute_timeout_at: Absolute timeout timestamp (null if no limit)
        seconds_until_idle_timeout: Seconds until idle timeout (null if no limit)
        seconds_until_absolute_timeout: Seconds until absolute timeout (null if no limit)
        remember_me: Whether "Remember Me" is enabled
        should_warn: Whether to show auto-logout warning to user
    """

    is_active: bool
    last_activity_at: str
    idle_timeout_seconds: int
    absolute_timeout_at: str | None = None
    seconds_until_idle_timeout: int | None = None
    seconds_until_absolute_timeout: int | None = None
    remember_me: bool
    should_warn: bool


@strawberry.type
class UpdateSessionActivityPayload:
    """Response payload for updating session activity.

    Attributes:
        success: Whether update succeeded
        message: User-friendly message
        last_activity_at: Updated activity timestamp
        idle_timeout_seconds: Idle timeout in seconds
        absolute_timeout_at: Absolute timeout timestamp (null if no limit)
    """

    success: bool
    message: str
    last_activity_at: str | None = None
    idle_timeout_seconds: int | None = None
    absolute_timeout_at: str | None = None


@strawberry.type
class EnableRememberMePayload:
    """Response payload for enabling "Remember Me".

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
        session_expires_at: When the session will expire (ISO format)
    """

    success: bool
    message: str
    session_expires_at: str | None = None


@strawberry.type
class DisableRememberMePayload:
    """Response payload for disabling "Remember Me".

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
        session_expires_at: When the session will expire (ISO format)
    """

    success: bool
    message: str
    session_expires_at: str | None = None


@strawberry.type
class TerminateSuspiciousSessionsPayload:
    """Response payload for terminating suspicious sessions.

    Attributes:
        success: Whether operation succeeded
        message: User-friendly message
        sessions_terminated: Number of sessions terminated
    """

    success: bool
    message: str
    sessions_terminated: int
