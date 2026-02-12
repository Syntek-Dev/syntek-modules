"""GraphQL mutations for two-factor authentication (2FA) operations.

This module defines all TOTP-related mutations for managing 2FA devices,
backup codes, and verification.

Implements requirements:
- C2: TOTP secret encryption using Fernet
- H13: Multiple TOTP devices with naming
- H14: Backup code hashing
- M3: Improved backup code format (XXXX-XXXX-XXXX)
- M6: TOTP time window tolerance (±1 period)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.models import TOTPDevice  # type: ignore[import]
from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.totp_service import TOTPService  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    NotFoundError,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.totp import (  # type: ignore[import]
    Confirm2FAInput,
    Confirm2FAPayload,
    Disable2FAPayload,
    Regenerate2FABackupCodesPayload,
    Remove2FADeviceInput,
    Remove2FADevicePayload,
    Setup2FAInput,
    Setup2FAPayload,
    TOTPDeviceType,
    TwoFactorStatusType,
)


def _device_to_graphql_type(device: TOTPDevice) -> TOTPDeviceType:
    """Convert TOTPDevice model to GraphQL type.

    Args:
        device: TOTPDevice model instance.

    Returns:
        TOTPDeviceType GraphQL object.
    """
    return TOTPDeviceType(
        id=strawberry.ID(str(device.id)),
        name=device.name,
        is_confirmed=device.is_confirmed,
        confirmed_at=device.confirmed_at.isoformat() if device.confirmed_at else None,
        last_used_at=device.last_used_at.isoformat() if device.last_used_at else None,
        created_at=device.created_at.isoformat(),
    )


@strawberry.type
class TOTPMutations:
    """GraphQL mutations for TOTP-based two-factor authentication."""

    @strawberry.mutation
    def setup_2fa(self, info: Info, input: Setup2FAInput) -> Setup2FAPayload:
        """Set up a new 2FA device for the authenticated user (H13).

        Creates a new TOTP device with encrypted secret (C2), generates
        QR code for authenticator app setup, and creates backup codes (H14, M3).

        Args:
            info: GraphQL execution info with authenticated user.
            input: Setup input containing device name.

        Returns:
            Setup2FAPayload with device details, secret, QR codes, and backup codes.

        Raises:
            AuthenticationError: If user not authenticated.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Create device with encrypted secret (C2, H13)
            device, plain_secret = TOTPService.create_device(
                user=user,
                device_name=input.device_name,
            )

            # Generate QR codes
            qr_code_svg = TOTPService.generate_qr_code_svg(device)
            qr_code_data_uri = TOTPService.generate_qr_code_data_uri(device)

            # Generate backup codes (H14, M3)
            backup_codes = TOTPService.generate_backup_codes(user)

            # Log 2FA setup initiated
            AuditService.log_event(
                action="2fa_setup_initiated",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
                metadata={"device_name": input.device_name, "device_id": str(device.id)},
            )

        return Setup2FAPayload(
            device=_device_to_graphql_type(device),
            secret=plain_secret,
            qr_code_svg=qr_code_svg,
            qr_code_data_uri=qr_code_data_uri,
            backup_codes=backup_codes,
        )

    @strawberry.mutation
    def confirm_2fa(self, info: Info, input: Confirm2FAInput) -> Confirm2FAPayload:
        """Confirm 2FA device setup by verifying initial token.

        User must provide a valid TOTP token from their authenticator app
        to prove they can generate codes before 2FA is enabled.

        Args:
            info: GraphQL execution info with authenticated user.
            input: Confirmation input with device ID and TOTP token.

        Returns:
            Confirm2FAPayload with success status and confirmed device.

        Raises:
            AuthenticationError: If user not authenticated.
            NotFoundError: If device not found or not owned by user.
            ValidationError: If token is invalid.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Find the device
        try:
            device = TOTPDevice.objects.get(id=input.device_id, user=user)
        except TOTPDevice.DoesNotExist as err:
            raise NotFoundError(
                ErrorCode.RESOURCE_NOT_FOUND,
                "TOTP device not found",
            ) from err

        # Check if already confirmed
        if device.is_confirmed:
            return Confirm2FAPayload(
                success=True,
                device=_device_to_graphql_type(device),
                message="Device is already confirmed",
            )

        # Verify the token (M6 - time window tolerance)
        # For confirmation, we verify against the unconfirmed device directly
        plain_secret = device.get_secret()
        import pyotp  # type: ignore[import]

        totp = pyotp.TOTP(plain_secret)
        is_valid = totp.verify(input.token, valid_window=TOTPService.TIME_WINDOW_TOLERANCE)

        if not is_valid:
            # Log failed confirmation attempt
            AuditService.log_event(
                action="2fa_confirmation_failed",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
                metadata={"device_id": str(device.id)},
            )
            raise ValidationError(
                ErrorCode.INVALID_TOTP_CODE,
                "Invalid TOTP code. Please check your authenticator app and try again.",
            )

        # Confirm the device
        if TOTPService.confirm_device(device, input.token):
            # Log successful confirmation
            AuditService.log_event(
                action="2fa_enabled",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
                metadata={"device_name": device.name, "device_id": str(device.id)},
            )

            return Confirm2FAPayload(
                success=True,
                device=_device_to_graphql_type(device),
                message="Two-factor authentication has been enabled successfully",
            )

        # This should not happen if token was valid, but handle it gracefully
        raise ValidationError(
            ErrorCode.INVALID_TOTP_CODE,
            "Failed to confirm device. Please try again.",
        )

    @strawberry.mutation
    def remove_2fa_device(self, info: Info, input: Remove2FADeviceInput) -> Remove2FADevicePayload:
        """Remove a TOTP device from the user's account (H13).

        Allows users to manage multiple devices by removing individual devices.
        If the last confirmed device is removed, 2FA is effectively disabled.

        Args:
            info: GraphQL execution info with authenticated user.
            input: Input with device ID to remove.

        Returns:
            Remove2FADevicePayload with success status and remaining device count.

        Raises:
            AuthenticationError: If user not authenticated.
            NotFoundError: If device not found or not owned by user.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Find the device
        try:
            device = TOTPDevice.objects.get(id=input.device_id, user=user)
        except TOTPDevice.DoesNotExist as err:
            raise NotFoundError(
                ErrorCode.RESOURCE_NOT_FOUND,
                "TOTP device not found",
            ) from err

        device_name = device.name
        was_confirmed = device.is_confirmed

        # Remove the device
        TOTPService.remove_device(device)

        # Count remaining devices
        remaining_devices = user.totp_devices.count()

        # Log device removal
        AuditService.log_event(
            action="2fa_device_removed",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
            metadata={
                "device_name": device_name,
                "was_confirmed": was_confirmed,
                "remaining_devices": remaining_devices,
            },
        )

        message = f"Device '{device_name}' has been removed"
        if remaining_devices == 0:
            message += ". Two-factor authentication is now disabled."

        return Remove2FADevicePayload(
            success=True,
            message=message,
            remaining_devices=remaining_devices,
        )

    @strawberry.mutation
    def regenerate_2fa_backup_codes(
        self, info: Info, password: str
    ) -> Regenerate2FABackupCodesPayload:
        """Regenerate backup codes for the authenticated user.

        Creates a new set of backup codes, invalidating all existing codes.
        Requires password confirmation for security.

        Args:
            info: GraphQL execution info with authenticated user.
            password: User's password for confirmation.

        Returns:
            Regenerate2FABackupCodesPayload with new backup codes.

        Raises:
            AuthenticationError: If user not authenticated or password invalid.
            ValidationError: If user doesn't have 2FA enabled.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Verify password
        if not user.check_password(password):
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        # Check if user has 2FA enabled
        if not TOTPService.has_confirmed_device(user):
            raise ValidationError(
                ErrorCode.INVALID_INPUT,
                "Two-factor authentication is not enabled",
            )

        ip_address = get_ip_address(info)

        # Generate new backup codes (H14, M3)
        backup_codes = TOTPService.generate_backup_codes(user)

        # Log backup code regeneration
        AuditService.log_event(
            action="2fa_backup_codes_regenerated",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
        )

        return Regenerate2FABackupCodesPayload(
            backup_codes=backup_codes,
            count=len(backup_codes),
        )

    @strawberry.mutation
    def disable_2fa(self, info: Info, password: str) -> Disable2FAPayload:
        """Disable two-factor authentication completely.

        Removes all TOTP devices and backup codes for the user.
        Requires password confirmation for security.

        Args:
            info: GraphQL execution info with authenticated user.
            password: User's password for confirmation.

        Returns:
            Disable2FAPayload with success status.

        Raises:
            AuthenticationError: If user not authenticated or password invalid.
            ValidationError: If 2FA is not enabled.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Verify password
        if not user.check_password(password):
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        # Check if user has 2FA enabled
        if not TOTPService.has_confirmed_device(user):
            raise ValidationError(
                ErrorCode.INVALID_INPUT,
                "Two-factor authentication is not enabled",
            )

        ip_address = get_ip_address(info)

        # Disable 2FA (removes all devices and backup codes)
        TOTPService.disable_2fa(user)

        # Log 2FA disabled
        AuditService.log_event(
            action="2fa_disabled",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
        )

        return Disable2FAPayload(
            success=True,
            message="Two-factor authentication has been disabled",
        )


@strawberry.type
class TOTPQueries:
    """GraphQL queries for TOTP-based two-factor authentication."""

    @strawberry.field
    def two_factor_status(self, info: Info) -> TwoFactorStatusType:
        """Get the current user's 2FA status.

        Returns an overview of the user's 2FA configuration including
        enabled status, registered devices (H13), and remaining backup codes.

        Args:
            info: GraphQL execution info with authenticated user.

        Returns:
            TwoFactorStatusType with 2FA status information.

        Raises:
            AuthenticationError: If user not authenticated.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Get all devices
        devices = TOTPService.list_user_devices(user)
        device_types = [_device_to_graphql_type(device) for device in devices]

        # Check if 2FA is enabled (has confirmed device)
        enabled = TOTPService.has_confirmed_device(user)

        # Count remaining backup codes
        backup_codes_remaining = TOTPService.count_remaining_backup_codes(user)

        return TwoFactorStatusType(
            enabled=enabled,
            devices=device_types,
            backup_codes_remaining=backup_codes_remaining,
        )

    @strawberry.field
    def two_factor_devices(self, info: Info) -> list[TOTPDeviceType]:
        """List all TOTP devices for the authenticated user (H13).

        Returns:
            List of TOTPDeviceType objects.

        Raises:
            AuthenticationError: If user not authenticated.
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        devices = TOTPService.list_user_devices(user)
        return [_device_to_graphql_type(device) for device in devices]
