"""GraphQL types for two-factor authentication (2FA).

This module defines input and output types for TOTP-based 2FA operations
including device management, verification, and backup codes.

Implements requirements:
- H13: Multiple TOTP devices with naming
- M3: Backup code format display
"""

import strawberry


@strawberry.input
class Setup2FAInput:
    """Input for 2FA setup mutation (H13).

    Attributes:
        device_name: User-friendly name for the device (e.g., "iPhone 14")
    """

    device_name: str = "Default"


@strawberry.input
class Confirm2FAInput:
    """Input for confirming 2FA setup.

    User must provide a valid token from their authenticator app
    to prove they can generate codes before enabling 2FA.

    Attributes:
        device_id: UUID of the device being confirmed
        token: 6-digit TOTP token from authenticator app
    """

    device_id: strawberry.ID
    token: str


@strawberry.input
class Verify2FAInput:
    """Input for verifying 2FA token during login.

    Attributes:
        token: 6-digit TOTP token from authenticator app
        use_backup_code: Whether the token is a backup code
    """

    token: str
    use_backup_code: bool = False


@strawberry.input
class Remove2FADeviceInput:
    """Input for removing a TOTP device (H13).

    Attributes:
        device_id: UUID of the device to remove
    """

    device_id: strawberry.ID


@strawberry.type
class TOTPDeviceType:
    """GraphQL type for TOTP device (H13).

    Represents a single 2FA device registered to a user.

    Attributes:
        id: Device UUID
        name: User-friendly device name
        is_confirmed: Whether setup is complete
        confirmed_at: When device was confirmed
        last_used_at: When device was last used for authentication
        created_at: When device was created
    """

    id: strawberry.ID
    name: str
    is_confirmed: bool
    confirmed_at: str | None = None
    last_used_at: str | None = None
    created_at: str


@strawberry.type
class Setup2FAPayload:
    """Response payload for 2FA setup mutation.

    Contains everything needed for the user to configure their authenticator app.

    Attributes:
        device: The created TOTP device
        secret: Plain text secret for manual entry (shown once)
        qr_code_svg: SVG QR code for scanning
        qr_code_data_uri: Base64 data URI for HTML img tag
        backup_codes: List of formatted backup codes (M3)
    """

    device: TOTPDeviceType
    secret: str
    qr_code_svg: str
    qr_code_data_uri: str
    backup_codes: list[str]


@strawberry.type
class Confirm2FAPayload:
    """Response payload for confirming 2FA setup.

    Attributes:
        success: Whether confirmation succeeded
        device: The confirmed device
        message: User-friendly message
    """

    success: bool
    device: TOTPDeviceType | None = None
    message: str


@strawberry.type
class Remove2FADevicePayload:
    """Response payload for removing a device (H13).

    Attributes:
        success: Whether removal succeeded
        message: User-friendly message
        remaining_devices: Number of devices still registered
    """

    success: bool
    message: str
    remaining_devices: int


@strawberry.type
class Regenerate2FABackupCodesPayload:
    """Response payload for regenerating backup codes.

    Attributes:
        backup_codes: New set of formatted backup codes (M3)
        count: Number of codes generated
    """

    backup_codes: list[str]
    count: int


@strawberry.type
class TwoFactorStatusType:
    """GraphQL type for user's 2FA status.

    Provides overview of user's 2FA configuration.

    Attributes:
        enabled: Whether user has confirmed 2FA device
        devices: List of registered devices (H13)
        backup_codes_remaining: Number of unused backup codes
    """

    enabled: bool
    devices: list[TOTPDeviceType]
    backup_codes_remaining: int


@strawberry.type
class Disable2FAPayload:
    """Response payload for disabling 2FA.

    Attributes:
        success: Whether 2FA was disabled
        message: User-friendly message
    """

    success: bool
    message: str
