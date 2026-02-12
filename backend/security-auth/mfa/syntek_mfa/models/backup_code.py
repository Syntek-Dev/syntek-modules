"""BackupCode model for two-factor authentication recovery.

This module implements backup codes for 2FA account recovery with proper
security measures including hashing (H14) and improved format (M3).
"""

import hashlib
import secrets
import uuid

from django.db import models
from django.utils import timezone


class BackupCode(models.Model):
    """One-time backup codes for 2FA account recovery.

    Backup codes provide emergency access when TOTP devices are unavailable.
    Codes are hashed before storage (H14) and use format XXXX-XXXX-XXXX (M3).

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        code_hash: SHA-256 hash of the backup code (H14)
        used: Whether the code has been consumed
        used_at: When the code was used
        created_at: When the code was created
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="backup_codes",
    )
    code_hash = models.CharField(max_length=64, db_index=True)
    used = models.BooleanField(default=False, db_index=True)  # type: ignore[call-arg]
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_backup_code"
        verbose_name = "Backup Code"
        verbose_name_plural = "Backup Codes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "used"]),
            models.Index(fields=["code_hash"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "code_hash"],
                name="unique_user_code_hash",
            ),
        ]

    def __str__(self) -> str:
        """Return backup code description.

        Returns:
            String representation with user email and status.
        """
        status = "used" if self.used else "unused"
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"Backup code for {user_email} ({status})"

    @staticmethod
    def hash_code(code: str) -> str:
        """Hash a backup code using SHA-256 (H14).

        Args:
            code: Plain text backup code (format: XXXX-XXXX-XXXX).

        Returns:
            Hexadecimal SHA-256 hash of the code.
        """
        # Remove hyphens and uppercase for consistent hashing
        normalized_code = code.replace("-", "").upper()
        return hashlib.sha256(normalized_code.encode()).hexdigest()

    @staticmethod
    def format_code(raw_code: str) -> str:
        """Format a raw code into XXXX-XXXX-XXXX format (M3).

        Args:
            raw_code: Raw 12-character alphanumeric code.

        Returns:
            Formatted code in XXXX-XXXX-XXXX format for readability.
        """
        # Ensure uppercase
        raw_code = raw_code.upper()

        # Split into groups of 4
        return f"{raw_code[0:4]}-{raw_code[4:8]}-{raw_code[8:12]}"

    @classmethod
    def generate_raw_code(cls) -> str:
        """Generate a random 12-character alphanumeric code.

        Returns:
            Raw 12-character code (no hyphens).
        """
        # Generate 12 random hex characters (0-9, A-F)
        return secrets.token_hex(6).upper()

    def mark_as_used(self) -> None:
        """Mark this backup code as used.

        Updates the used flag and records the timestamp.
        """
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=["used", "used_at"])
