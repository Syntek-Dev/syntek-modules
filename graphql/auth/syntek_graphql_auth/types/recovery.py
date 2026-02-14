"""GraphQL types for recovery key operations.

This module defines input and output types for account recovery keys.
Implements algorithm versioning and expiry management.
"""

from __future__ import annotations

import strawberry


@strawberry.input
class GenerateRecoveryKeysInput:
    """Input for generating recovery keys.

    Attributes:
        password: User's password for confirmation
        count: Number of keys to generate (default: 5, max: 10)
        format: Key format (default: "base32")
    """

    password: str
    count: int = 5
    format: str = "base32"


@strawberry.input
class LoginWithRecoveryKeyInput:
    """Input for logging in with recovery key.

    Attributes:
        email: User's email address
        recovery_key: Recovery key (one-time use)
    """

    email: str
    recovery_key: str


@strawberry.type
class RecoveryKeyType:
    """GraphQL type for recovery key (enhanced with versioning and expiry).

    Represents a single recovery key with metadata.

    Attributes:
        id: Key UUID
        algorithm_version: Algorithm version (e.g., "hmac-sha256-v1")
        created_at: Key creation timestamp
        expires_at: Key expiry timestamp
        is_expired: Whether key has expired
        is_used: Whether key has been used (one-time use)
        days_until_expiry: Days remaining until expiry (null if expired/used)
    """

    id: strawberry.ID
    algorithm_version: str
    created_at: str
    expires_at: str
    is_expired: bool
    is_used: bool
    days_until_expiry: int | None = None


@strawberry.type
class GenerateRecoveryKeysPayload:
    """Response payload for generating recovery keys.

    Attributes:
        recovery_keys: List of plain text recovery keys (shown once)
        count: Number of keys generated
        expires_at: When keys expire (ISO timestamp)
        message: User-friendly message
    """

    recovery_keys: list[str]
    count: int
    expires_at: str
    message: str


@strawberry.type
class RecoveryKeyStatusType:
    """Status information for user's recovery keys.

    Attributes:
        active_keys: List of active (unexpired, unused) recovery keys
        total_keys: Total number of recovery keys
        expired_keys: Number of expired keys
        used_keys: Number of used keys
        oldest_expiry: Earliest expiry date among active keys (null if no active keys)
    """

    active_keys: list[RecoveryKeyType]
    total_keys: int
    expired_keys: int
    used_keys: int
    oldest_expiry: str | None = None
