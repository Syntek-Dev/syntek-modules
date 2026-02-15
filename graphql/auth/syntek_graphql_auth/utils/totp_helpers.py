"""Two-factor authentication helpers for login mutations.

Provides TOTP and backup code verification logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.totp_service import TOTPService  # type: ignore[import]


def verify_two_factor_code(
    user: User,
    totp_code: str,
    ip_address: str,
) -> bool:
    """Verify TOTP code or backup code for user.

    Tries TOTP token first, then falls back to backup codes.
    Logs backup code usage for audit trail.

    Args:
        user: User to verify 2FA for
        totp_code: TOTP code or backup code to verify
        ip_address: Client IP address for audit logging

    Returns:
        bool: True if verification successful, False otherwise
    """
    # Try TOTP token first
    verified = False

    # Get user's confirmed devices
    devices = list(user.totp_devices.filter(is_confirmed=True))

    # Try each device until one verifies
    for device in devices:
        if TOTPService.verify_token(device, totp_code):
            verified = True
            break

    # If TOTP failed, try backup code
    if not verified:
        verified = TOTPService.verify_backup_code(user, totp_code)  # type: ignore[arg-type]

        if verified:
            # Log backup code usage
            AuditService.log_event(
                action="2fa_backup_code_used",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
            )

    return verified
