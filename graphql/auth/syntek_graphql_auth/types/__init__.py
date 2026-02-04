"""GraphQL types for authentication operations."""

from syntek_graphql_auth.types.auth import (
    AuthPayload,
    EnableTwoFactorInput,
    LoginInput,
    PasswordChangeInput,
    PasswordResetInput,
    PasswordResetRequestInput,
    RegisterInput,
    TwoFactorSetupPayload,
)
from syntek_graphql_auth.types.totp import (
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
from syntek_graphql_auth.types.user import (
    OrganisationType,
    UserProfileType,
    UserType,
)

__all__ = [
    # Auth types
    "AuthPayload",
    "EnableTwoFactorInput",
    "LoginInput",
    "PasswordChangeInput",
    "PasswordResetInput",
    "PasswordResetRequestInput",
    "RegisterInput",
    "TwoFactorSetupPayload",
    # TOTP types
    "Confirm2FAInput",
    "Confirm2FAPayload",
    "Disable2FAPayload",
    "Regenerate2FABackupCodesPayload",
    "Remove2FADeviceInput",
    "Remove2FADevicePayload",
    "Setup2FAInput",
    "Setup2FAPayload",
    "TOTPDeviceType",
    "TwoFactorStatusType",
    # User types
    "OrganisationType",
    "UserProfileType",
    "UserType",
]
