"""TOTPDevice model for two-factor authentication.

This module implements TOTP (Time-based One-Time Password) device management
with Fernet encryption for secrets (C2 security requirement).
"""

import uuid

import pyotp  # type: ignore[import]
from cryptography.fernet import Fernet, InvalidToken  # type: ignore[import]
from django.conf import settings
from django.db import models
from django.utils import timezone


class TOTPDevice(models.Model):
    """TOTP device for two-factor authentication.

    Stores encrypted TOTP secrets for user authentication devices.
    Supports multiple devices per user (H13) with device naming.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        name: Device name for identification (H13)
        secret: Encrypted TOTP secret (Fernet encryption)
        is_confirmed: Whether device setup is complete
        confirmed_at: When device was confirmed
        last_used_at: When device was last used for authentication
        created_at: When device was created
        updated_at: When device was last modified
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="totp_devices",
    )
    name = models.CharField(max_length=64, default="Default")
    secret = models.BinaryField()
    is_confirmed = models.BooleanField(default=False)  # type: ignore[call-arg]
    confirmed_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_totp_device"
        verbose_name = "TOTP Device"
        verbose_name_plural = "TOTP Devices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_confirmed"]),
        ]

    def __str__(self) -> str:
        """Return TOTP device description.

        Returns:
            String representation with device name and user email.
        """
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"TOTP device '{self.name}' for {user_email}"

    @staticmethod
    def _get_cipher() -> Fernet:
        """Get Fernet cipher for encryption/decryption.

        Returns:
            Fernet cipher instance using TOTP_ENCRYPTION_KEY from settings.

        Raises:
            ImproperlyConfigured: If TOTP_ENCRYPTION_KEY not set in settings.
        """
        encryption_key = getattr(settings, "TOTP_ENCRYPTION_KEY", None)
        if not encryption_key:
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured(
                "TOTP_ENCRYPTION_KEY must be set in Django settings. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            )
        return Fernet(
            encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        )

    def set_secret(self, plain_secret: str) -> None:
        """Set and encrypt the TOTP secret using Fernet (C2).

        Encrypts the TOTP secret before storing in the database to protect
        against secret compromise if database is accessed.

        Args:
            plain_secret: Plain text base32 TOTP secret.
        """
        cipher = self._get_cipher()
        self.secret = cipher.encrypt(plain_secret.encode())

    def get_secret(self) -> str:
        """Get the decrypted TOTP secret.

        Decrypts the stored encrypted secret using Fernet cipher.

        Returns:
            Plain text base32 TOTP secret.

        Raises:
            cryptography.fernet.InvalidToken: If secret cannot be decrypted.
        """
        if not self.secret:
            return ""
        cipher = self._get_cipher()
        return cipher.decrypt(self.secret).decode()

    def verify_token(self, token: str, valid_window: int = 1) -> bool:
        """Verify a TOTP token against this device.

        Verifies the provided 6-digit token using the device's encrypted secret.
        Includes time tolerance window to account for clock skew.

        Args:
            token: The 6-digit TOTP token to verify.
            valid_window: Number of time steps to allow before/after current time.
                         Default is 1 (90 second window: -30s, current, +30s).

        Returns:
            True if token is valid, False otherwise.
        """
        if not self.is_confirmed:
            return False

        try:
            plain_secret = self.get_secret()
            totp = pyotp.TOTP(plain_secret)
            is_valid = totp.verify(token, valid_window=valid_window)

            if is_valid:
                self.last_used_at = timezone.now()
                self.save(update_fields=["last_used_at"])

            return is_valid
        except (ValueError, TypeError, InvalidToken):
            return False

    def generate_qr_code_uri(self, issuer_name: str = "Syntek App") -> str:
        """Generate provisioning URI for QR code display.

        Generates a URI that can be encoded into a QR code for easy device setup
        in authenticator apps like Google Authenticator or Authy.

        Args:
            issuer_name: Name of the application/service for display in auth app.

        Returns:
            Provisioning URI string for QR code generation.
        """
        plain_secret = self.get_secret()
        totp = pyotp.TOTP(plain_secret)
        user_email = (
            getattr(self.user, "email", "unknown@example.com")
            if self.user
            else "unknown@example.com"
        )
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer_name,
        )
