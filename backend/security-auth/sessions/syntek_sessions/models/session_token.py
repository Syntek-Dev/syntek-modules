"""SessionToken model for authenticated users.

Stores JWT access and refresh token hashes for session management.
Implements security recommendations H8 (device fingerprinting),
H9 (token family for replay detection), and M8 (session activity tracking).
"""

from django.db import models
from django.utils import timezone

from syntek_authentication.models import BaseToken  # type: ignore[import]


class SessionToken(BaseToken):
    """Session token for user authentication.

    Stores hashed JWT tokens in database for revocation and tracking.
    Supports refresh token rotation with replay detection.

    Attributes:
        user: Foreign key to User (inherited from BaseToken)
        token: Secure random token (inherited from BaseToken)
        token_family: UUID for token family replay detection (inherited from BaseToken)
        used: Single-use flag (inherited from BaseToken)
        expires_at: Token expiration (inherited from BaseToken)
        created_at: Creation timestamp (inherited from BaseToken)
        token_hash: Hashed JWT access token
        refresh_token_hash: Hashed JWT refresh token
        ip_address: Encrypted IP address (BinaryField for Fernet encryption)
        user_agent: Browser user agent string
        device_fingerprint: Device identifier for tracking (H8)
        is_refresh_token_used: Flag for refresh token rotation (H9)
        last_activity_at: Last activity timestamp (M8)
        is_revoked: Manual revocation flag
        revoked_at: Revocation timestamp
    """

    # Override token_hash from BaseToken - SessionToken uses its own hashes
    token_hash = models.CharField(
        max_length=255, unique=True, db_index=True, blank=True, default=""
    )
    refresh_token_hash = models.CharField(
        max_length=255, unique=True, db_index=True, blank=True, default=""
    )

    # Security tracking
    ip_address = models.BinaryField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    device_fingerprint = models.CharField(max_length=64, blank=True, default="")

    # H9: Refresh token rotation and replay detection
    is_refresh_token_used = models.BooleanField(default=False)  # type: ignore[call-arg]

    # M8: Session activity tracking
    last_activity_at = models.DateTimeField(auto_now=True)

    # Manual revocation
    is_revoked = models.BooleanField(default=False)  # type: ignore[call-arg]
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "session_tokens"
        verbose_name = "Session Token"
        verbose_name_plural = "Session Tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["token_hash"]),
            models.Index(fields=["refresh_token_hash"]),
            models.Index(fields=["token_family"]),
            models.Index(fields=["device_fingerprint"]),
            models.Index(fields=["last_activity_at"]),
            # H1: Composite index for filtering active sessions per user
            models.Index(fields=["user", "is_revoked"]),
            # H2: Token expiry index for cleanup queries
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_revoked", "expires_at"]),
        ]

    def __str__(self) -> str:
        """Return session token description.

        Returns:
            String representation with user email and creation time.
        """
        return f"Session for {self.user.email} (created {self.created_at})"

    def revoke(self) -> None:
        """Revoke the session token.

        Marks the token as revoked and records the revocation timestamp.
        Revoked tokens cannot be used for authentication.
        """
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_revoked", "revoked_at"])

    def is_valid(self) -> bool:
        """Check if token is valid for authentication.

        Overrides BaseToken.is_valid() to include revocation check.
        Combines checks for expiration, usage, and revocation status.

        Returns:
            True if token can be used for authentication, False otherwise.
        """
        return not self.is_expired() and not self.used and not self.is_revoked

    def mark_refresh_token_used(self) -> None:
        """Mark refresh token as used for rotation (H9).

        Implements refresh token rotation security pattern.
        Once a refresh token is used, it should be invalidated to prevent reuse.
        """
        self.is_refresh_token_used = True
        self.save(update_fields=["is_refresh_token_used"])
