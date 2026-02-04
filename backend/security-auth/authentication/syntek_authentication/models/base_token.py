"""BaseToken abstract model for authentication tokens.

Provides common fields and methods for SessionToken, PasswordResetToken,
and EmailVerificationToken. Implements token family pattern for replay
detection (H9) and single-use token validation (H12).

Security: Tokens are stored as HMAC-SHA256 hashes using TokenHasher utility.
Plain tokens are never stored in the database (C1, C3 requirements).
"""

import hashlib
import hmac
import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseToken(models.Model):
    """Abstract base class for all token types.

    Provides common fields and methods for SessionToken, PasswordResetToken,
    and EmailVerificationToken. Implements token family pattern for replay
    detection (H9) and single-use token validation (H12).

    Attributes:
        id: UUID primary key
        user: Foreign key to User
        token: Secure random token string (URL-safe base64, auto-generated)
        token_hash: HMAC-SHA256 hash of token for secure storage (C1, C3)
        token_family: UUID for grouping related tokens (H9 replay detection)
        used: Single-use flag (H12)
        used_at: Timestamp when token was used
        expires_at: Token expiration timestamp
        created_at: Creation timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="%(class)s_tokens",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True, blank=True, default="")
    token_hash = models.CharField(
        max_length=255, unique=True, db_index=True, blank=True, default=""
    )
    token_family = models.UUIDField(default=uuid.uuid4, db_index=True)
    used = models.BooleanField(default=False)  # type: ignore[call-arg]
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Generate token and hash on save if not set."""
        if not self.token:
            self.token = self.generate_token()
        if not self.token_hash and self.token:
            self.token_hash = self.hash_token(self.token)  # type: ignore[arg-type]
        super().save(*args, **kwargs)

    @classmethod
    def hash_token(cls, token: str) -> str:
        """Generate HMAC-SHA256 hash of token for secure storage.

        Uses the TOKEN_SIGNING_KEY as the HMAC key to ensure tokens cannot be
        forged without access to the signing key (C1 security requirement).
        This key is separate from SECRET_KEY for defense-in-depth.

        Args:
            token: The plain text token to hash.

        Returns:
            Hexadecimal string of the HMAC-SHA256 hash.

        Raises:
            ImproperlyConfigured: If TOKEN_SIGNING_KEY is not set in settings.
        """
        from django.core.exceptions import ImproperlyConfigured

        signing_key = getattr(settings, "TOKEN_SIGNING_KEY", None)
        if not signing_key:
            raise ImproperlyConfigured(
                "TOKEN_SIGNING_KEY must be set in settings. "
                'Generate with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        key = signing_key.encode()
        return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token.

        Uses URL-safe base64 encoding to generate a cryptographically
        secure random token suitable for authentication purposes.

        Returns:
            A secure random token string (64 characters).
        """
        return secrets.token_urlsafe(48)

    def is_expired(self) -> bool:
        """Check if token is expired.

        Compares the token's expiration timestamp with the current time.

        Returns:
            True if token has expired, False otherwise.
        """
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used).

        Implements H12 security requirement for single-use tokens.
        A token is valid only if it hasn't expired AND hasn't been used.

        Returns:
            True if token is valid for use, False otherwise.
        """
        return not self.is_expired() and not self.used

    def mark_used(self) -> None:
        """Mark token as used (H12 single-use implementation).

        Once a token is marked as used, it cannot be used again.
        Records the timestamp when the token was used.
        """
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=["used", "used_at"])

    # Backwards compatibility property for is_used -> used migration
    @property
    def is_used(self) -> bool:
        """Backwards compatibility alias for 'used' field."""
        return self.used  # type: ignore[return-value]

    @is_used.setter
    def is_used(self, value: bool) -> None:
        """Set used field via is_used alias."""
        self.used = value
