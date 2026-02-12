"""EmailVerificationToken model for email verification workflow.

Implements secure email verification tokens with expiration and single-use
validation as specified in security requirement H12.
"""

from django.db import models

from .base_token import BaseToken


class EmailVerificationToken(BaseToken):
    """Token for email verification workflow.

    Single-use token sent via email for verifying user email addresses.
    Inherits expiration and validation logic from BaseToken.
    Implements H12 security requirement for single-use tokens.

    Attributes:
        Inherits all attributes from BaseToken:
        - id: UUID primary key
        - user: Foreign key to User
        - token: Secure random token string
        - token_family: UUID for replay detection
        - is_used: Single-use flag (H12)
        - used_at: Timestamp when token was used
        - expires_at: Token expiration (typically 24 hours)
        - created_at: Creation timestamp
    """

    class Meta:
        db_table = "email_verification_tokens"
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        indexes = [
            # H2: Token expiry index for cleanup queries
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return email verification token description."""
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"Email verification for {user_email} (expires {self.expires_at})"
