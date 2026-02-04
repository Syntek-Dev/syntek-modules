"""PasswordHistory model for preventing password reuse (H11).

This module implements password history tracking to prevent users from
reusing recent passwords, as specified in the security review.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.hashers import check_password
from django.db import models


class PasswordHistory(models.Model):
    """Password history for preventing password reuse (H11).

    Stores historical password hashes to prevent users from reusing
    recent passwords. Implements security recommendation H11 from
    the authentication security review.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        password_hash: Hashed password (stored using same hasher as User)
        created_at: When this password was set
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="password_history",
    )
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_history"
        verbose_name = "Password History"
        verbose_name_plural = "Password Histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Return password history description.

        Returns:
            String representation with user email and timestamp.
        """
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"Password history for {user_email} at {self.created_at}"

    def check_password(self, password: str) -> bool:
        """Check if provided password matches this historical password.

        Uses Django's check_password to verify against the stored hash.

        Args:
            password: Plain text password to check.

        Returns:
            True if passwords match, False otherwise.
        """
        return check_password(password, self.password_hash)

    @classmethod
    def check_password_reuse(cls, user, password: str, history_count: int = 12) -> bool:
        """Check if password was used in recent history (H11).

        Checks the provided password against the user's most recent
        password history entries. Default is 12 historical passwords
        as recommended in security review.

        Args:
            user: The user to check history for.
            password: The plain text password to check.
            history_count: Number of historical passwords to check (default: 12).

        Returns:
            True if password was recently used, False otherwise.
        """
        recent_passwords = cls.objects.filter(user=user).order_by("-created_at")[:history_count]  # type: ignore[attr-defined]

        return any(history.check_password(password) for history in recent_passwords)

    @classmethod
    def record_password(cls, user, password_hash: str) -> PasswordHistory:
        """Record a password in history.

        Stores the hashed password in history and cleans up old entries
        beyond the retention limit (keeps last 24 entries).

        Args:
            user: The user whose password is being recorded.
            password_hash: The hashed password to store.

        Returns:
            The created PasswordHistory instance.
        """
        # Create new history entry
        history = cls.objects.create(  # type: ignore[attr-defined]
            user=user,
            password_hash=password_hash,
        )

        # Clean up old history (keep last 24 entries)
        old_passwords = cls.objects.filter(user=user).order_by("-created_at")[24:]  # type: ignore[attr-defined]
        for old_password in old_passwords:
            old_password.delete()

        return history
