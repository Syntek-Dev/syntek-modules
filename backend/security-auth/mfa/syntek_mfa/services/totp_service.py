"""TOTP service for two-factor authentication management.

This module provides comprehensive 2FA functionality including device setup,
token verification, backup code management, and QR code generation.

Implements security requirements:
- C2: TOTP secret encryption using Rust encryption layer
- H13: Multiple named TOTP devices per user
- H14: Backup code hashing with Argon2
- M3: Improved backup code format (XXXX-XXXX-XXXX)
- M6: TOTP time window tolerance (±1 period)

Example:
    >>> device, secret = TOTPService.create_device(user, "iPhone 14")
    >>> qr_svg = TOTPService.generate_qr_code_svg(device)
    >>> is_valid = TOTPService.verify_token(device, "123456")
    >>> backup_codes = TOTPService.generate_backup_codes(user)
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

import pyotp  # type: ignore[import]
import qrcode
from qrcode.image.svg import SvgPathImage

from syntek_mfa.models import BackupCode, TOTPDevice  # type: ignore[import]

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

UserModel = get_user_model()


class TOTPService:
    """Service for managing TOTP-based two-factor authentication.

    Handles device enrollment, token verification, backup codes,
    and QR code generation with proper security measures.

    Attributes:
        DEFAULT_ISSUER: Default service name shown in authenticator apps.
        BACKUP_CODE_COUNT: Number of backup codes to generate per user.
        TIME_WINDOW_TOLERANCE: Number of time periods to check (±1 = 90s window).
    """

    DEFAULT_ISSUER = "Syntek App"
    BACKUP_CODE_COUNT = 10
    TIME_WINDOW_TOLERANCE = 1  # M6: ±1 period (90 second window)

    @classmethod
    def create_device(
        cls,
        user: AbstractUser,
        device_name: str = "Default",
        issuer_name: str | None = None,
    ) -> tuple[TOTPDevice, str]:
        """Create a new TOTP device for a user (H13).

        Generates a new TOTP secret, encrypts it via Rust layer (C2), and creates
        a device record. Supports multiple devices per user with unique names (H13).

        Args:
            user: User to create device for.
            device_name: Name for the device (e.g., "iPhone", "Backup Device").
            issuer_name: Service name shown in authenticator app.

        Returns:
            Tuple of (TOTPDevice instance, plain_secret for QR code display).

        Example:
            >>> device, secret = TOTPService.create_device(user, "iPhone 14")
            >>> device.is_confirmed
            False
            >>> len(secret)
            32
        """
        # Generate random TOTP secret (base32)
        plain_secret = pyotp.random_base32()

        # Create device with encrypted secret (C2)
        device = TOTPDevice(user=user, name=device_name, is_confirmed=False)
        device.set_secret(plain_secret)
        device.save()

        return device, plain_secret

    @classmethod
    def generate_qr_code_svg(cls, device: TOTPDevice, issuer_name: str | None = None) -> str:
        """Generate SVG QR code for device setup.

        Creates an SVG QR code that can be scanned by authenticator apps
        like Google Authenticator, Authy, or 1Password.

        Args:
            device: TOTP device to generate QR code for.
            issuer_name: Service name for display (defaults to DEFAULT_ISSUER).

        Returns:
            SVG string containing the QR code.

        Example:
            >>> device, _ = TOTPService.create_device(user)
            >>> svg = TOTPService.generate_qr_code_svg(device)
            >>> "<svg" in svg
            True
        """
        issuer = issuer_name or cls.DEFAULT_ISSUER
        uri = device.generate_qr_code_uri(issuer_name=issuer)

        # Generate QR code as SVG for scalability
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # type: ignore[attr-defined]
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Create SVG image
        img = qr.make_image(image_factory=SvgPathImage)

        # Convert to string
        buffer = io.BytesIO()
        img.save(buffer)
        return buffer.getvalue().decode()

    @classmethod
    def generate_qr_code_data_uri(cls, device: TOTPDevice, issuer_name: str | None = None) -> str:
        """Generate base64 data URI for QR code.

        Creates a data URI that can be used directly in HTML img tags.

        Args:
            device: TOTP device to generate QR code for.
            issuer_name: Service name for display.

        Returns:
            Data URI string (data:image/svg+xml;base64,...).

        Example:
            >>> device, _ = TOTPService.create_device(user)
            >>> uri = TOTPService.generate_qr_code_data_uri(device)
            >>> uri.startswith("data:image/svg+xml;base64,")
            True
        """
        import base64

        svg = cls.generate_qr_code_svg(device, issuer_name)
        b64_svg = base64.b64encode(svg.encode()).decode()
        return f"data:image/svg+xml;base64,{b64_svg}"

    @classmethod
    def verify_token(cls, device: TOTPDevice, token: str, valid_window: int | None = None) -> bool:
        """Verify a TOTP token with time tolerance (M6).

        Verifies the 6-digit TOTP token using the device's encrypted secret.
        Includes time window tolerance to handle clock skew (M6).

        Args:
            device: TOTP device to verify against.
            token: 6-digit TOTP token from authenticator app.
            valid_window: Number of time steps to check (default: 1).
                         1 = 90 second window (-30s, current, +30s).

        Returns:
            True if token is valid, False otherwise.

        Example:
            >>> device, secret = TOTPService.create_device(user)
            >>> totp = pyotp.TOTP(secret)
            >>> token = totp.now()
            >>> TOTPService.verify_token(device, token)
            False  # Not confirmed yet
        """
        window = valid_window if valid_window is not None else cls.TIME_WINDOW_TOLERANCE
        return device.verify_token(token, valid_window=window)

    @classmethod
    def confirm_device(cls, device: TOTPDevice, token: str) -> bool:
        """Confirm device setup by verifying initial token.

        User must provide a valid token from their authenticator app
        to prove they can generate codes before enabling 2FA.

        Args:
            device: TOTP device to confirm.
            token: 6-digit TOTP token for verification.

        Returns:
            True if token verified and device confirmed, False otherwise.

        Example:
            >>> device, secret = TOTPService.create_device(user)
            >>> totp = pyotp.TOTP(secret)
            >>> token = totp.now()
            >>> TOTPService.confirm_device(device, token)
            True
            >>> device.is_confirmed
            True
        """
        if device.is_confirmed:
            return True

        # Verify token directly using pyotp (device.verify_token requires is_confirmed=True)
        # Use time tolerance (M6)
        try:
            plain_secret = device.get_secret()
            totp = pyotp.TOTP(plain_secret)
            is_valid = totp.verify(token, valid_window=cls.TIME_WINDOW_TOLERANCE)

            if is_valid:
                device.is_confirmed = True  # type: ignore[misc]
                device.confirmed_at = timezone.now()  # type: ignore[misc]
                device.save(update_fields=["is_confirmed", "confirmed_at"])
                return True
        except (ValueError, TypeError):
            pass

        return False

    @classmethod
    def remove_device(cls, device: TOTPDevice) -> None:
        """Remove a TOTP device from a user's account (H13).

        Allows users to manage multiple devices by removing individual devices.

        Args:
            device: TOTP device to remove.

        Example:
            >>> device, _ = TOTPService.create_device(user, "Old Phone")
            >>> TOTPService.remove_device(device)
        """
        device.delete()

    @classmethod
    def list_user_devices(cls, user: AbstractUser) -> list[TOTPDevice]:
        """List all TOTP devices for a user (H13).

        Returns all confirmed and unconfirmed devices ordered by creation date.

        Args:
            user: User to list devices for.

        Returns:
            List of TOTPDevice instances.

        Example:
            >>> devices = TOTPService.list_user_devices(user)
            >>> len(devices)
            2
        """
        return list(user.totp_devices.all().order_by("-created_at"))  # type: ignore[attr-defined]

    @classmethod
    def has_confirmed_device(cls, user: AbstractUser) -> bool:
        """Check if user has at least one confirmed TOTP device.

        Args:
            user: User to check.

        Returns:
            True if user has confirmed 2FA device, False otherwise.

        Example:
            >>> TOTPService.has_confirmed_device(user)
            False
        """
        return user.totp_devices.filter(is_confirmed=True).exists()  # type: ignore[attr-defined]

    @classmethod
    @transaction.atomic
    def generate_backup_codes(cls, user: AbstractUser) -> list[str]:
        """Generate new backup codes for a user (H14, M3).

        Creates a new set of backup codes, invalidating any existing codes.
        Codes are hashed before storage (H14) and formatted for readability (M3).

        Args:
            user: User to generate backup codes for.

        Returns:
            List of plain text backup codes in XXXX-XXXX-XXXX format (M3).

        Example:
            >>> codes = TOTPService.generate_backup_codes(user)
            >>> len(codes)
            10
            >>> codes[0]
            'A1B2-C3D4-E5F6'
        """
        # Delete all existing backup codes
        BackupCode.objects.filter(user=user).delete()  # type: ignore[attr-defined]

        plain_codes = []

        for _ in range(cls.BACKUP_CODE_COUNT):
            # Generate raw 12-character code
            raw_code = BackupCode.generate_raw_code()

            # Format as XXXX-XXXX-XXXX (M3)
            formatted_code = BackupCode.format_code(raw_code)
            plain_codes.append(formatted_code)

            # Hash and store (H14)
            code_hash = BackupCode.hash_code(formatted_code)
            BackupCode.objects.create(user=user, code_hash=code_hash)  # type: ignore[attr-defined]

        return plain_codes

    @classmethod
    @transaction.atomic
    def verify_backup_code(cls, user: AbstractUser, code: str) -> bool:
        """Verify and consume a backup code (H14).

        Verifies a backup code against stored hashes and marks it as used
        if valid. Each code can only be used once.

        Args:
            user: User attempting to use backup code.
            code: Backup code in any format (hyphens optional).

        Returns:
            True if code is valid and unused, False otherwise.

        Example:
            >>> codes = TOTPService.generate_backup_codes(user)
            >>> TOTPService.verify_backup_code(user, codes[0])
            True
            >>> TOTPService.verify_backup_code(user, codes[0])
            False  # Already used
        """
        # Hash the provided code
        code_hash = BackupCode.hash_code(code)

        try:
            backup_code = BackupCode.objects.get(user=user, code_hash=code_hash, used=False)  # type: ignore[attr-defined]
            # Mark as used
            backup_code.mark_as_used()
            return True
        except BackupCode.DoesNotExist:  # type: ignore[attr-defined]
            return False

    @classmethod
    def count_remaining_backup_codes(cls, user: AbstractUser) -> int:
        """Count unused backup codes for a user.

        Args:
            user: User to count codes for.

        Returns:
            Number of unused backup codes.

        Example:
            >>> TOTPService.generate_backup_codes(user)
            >>> TOTPService.count_remaining_backup_codes(user)
            10
        """
        return BackupCode.objects.filter(user=user, used=False).count()  # type: ignore[attr-defined]

    @classmethod
    @transaction.atomic
    def disable_2fa(cls, user: AbstractUser) -> None:
        """Disable 2FA completely for a user.

        Removes all TOTP devices and backup codes for the user.

        Args:
            user: User to disable 2FA for.

        Example:
            >>> TOTPService.disable_2fa(user)
            >>> TOTPService.has_confirmed_device(user)
            False
        """
        user.totp_devices.all().delete()  # type: ignore[attr-defined]
        user.backup_codes.all().delete()  # type: ignore[attr-defined]
