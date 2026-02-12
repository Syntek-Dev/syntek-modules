"""PasswordResetToken model for password reset workflow.

Implements secure password reset tokens with expiration and single-use
validation as specified in security requirement H12.
"""

from django.db import models

from .base_token import BaseToken


class PasswordResetToken(BaseToken):
    """Token for password reset workflow.

    Single-use token sent via email for secure password reset.
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
        - expires_at: Token expiration (typically 1 hour)
        - created_at: Creation timestamp
    """

    class Meta:
        db_table = "password_reset_tokens"
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        indexes = [
            # H2: Token expiry index for cleanup queries
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return password reset token description."""
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"Password reset for {user_email} (expires {self.expires_at})"
