"""MFA models.

Exports all MFA-related models for easy importing.
"""

from .backup_code import BackupCode
from .totp_device import TOTPDevice

__all__ = [
    "BackupCode",
    "TOTPDevice",
]
