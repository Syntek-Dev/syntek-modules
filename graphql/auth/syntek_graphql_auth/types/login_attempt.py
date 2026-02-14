"""GraphQL types for login attempt tracking.

This module defines types for tracking and querying login attempts,
including failed attempts and suspicious activity detection.
"""

from __future__ import annotations

import strawberry


@strawberry.type
class LoginAttemptEntryType:
    """GraphQL type for login attempt tracking.

    Represents a single login attempt (successful or failed).

    Attributes:
        id: Entry UUID
        email: Email used for login attempt
        ip_address_decrypted: Decrypted IP address (only for authorized users)
        success: Whether login succeeded
        failure_reason: Reason code for failed attempts (null if successful)
        user_agent: Browser/device user agent
        created_at: Timestamp of login attempt
    """

    id: strawberry.ID
    email: str
    ip_address_decrypted: str | None = None  # Null if user not authorized
    success: bool
    failure_reason: str | None = None
    user_agent: str
    created_at: str


@strawberry.type
class SuspiciousActivityEntryType:
    """GraphQL type for suspicious login activity.

    Represents a flagged login attempt that exhibits suspicious behavior.

    Attributes:
        id: Entry UUID
        email: Email used for login attempt
        ip_address_decrypted: Decrypted IP address (only for authorized users)
        reason: Reason for flagging as suspicious
        severity: Severity level (low, medium, high, critical)
        user_agent: Browser/device user agent
        created_at: Timestamp when flagged
        resolved: Whether issue has been resolved/investigated
    """

    id: strawberry.ID
    email: str
    ip_address_decrypted: str | None = None
    reason: str
    severity: str  # "low", "medium", "high", "critical"
    user_agent: str
    created_at: str
    resolved: bool


@strawberry.type
class LoginAttemptsStatsType:
    """Statistics for login attempts.

    Provides summary statistics for a user's login attempts.

    Attributes:
        total_attempts: Total number of login attempts
        successful_attempts: Number of successful logins
        failed_attempts: Number of failed logins
        unique_ips: Number of unique IP addresses used
        suspicious_count: Number of flagged suspicious attempts
        most_recent_success: Timestamp of most recent successful login (null if none)
        most_recent_failure: Timestamp of most recent failed login (null if none)
    """

    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    unique_ips: int
    suspicious_count: int
    most_recent_success: str | None = None
    most_recent_failure: str | None = None
