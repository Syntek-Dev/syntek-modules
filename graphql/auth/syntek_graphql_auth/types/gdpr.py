"""GraphQL types for GDPR compliance operations.

This module defines types for data subject rights including data access,
rectification, erasure, and consent management (GDPR Articles 15-21).
"""

from __future__ import annotations

import strawberry


@strawberry.input
class UpdateEmailInput:
    """Input for updating user email (GDPR Right to Rectification - Art. 16).

    Attributes:
        password: Current password for verification
        new_email: New email address
    """

    password: str
    new_email: str


@strawberry.input
class UpdatePhoneNumberInput:
    """Input for updating user phone number (GDPR Right to Rectification - Art. 16).

    Attributes:
        password: Current password for verification
        new_phone_number: New phone number (E.164 format)
    """

    password: str
    new_phone_number: str


@strawberry.input
class UpdateUsernameInput:
    """Input for updating username (GDPR Right to Rectification - Art. 16).

    Attributes:
        password: Current password for verification
        new_username: New username (must be unique)
    """

    password: str
    new_username: str


@strawberry.input
class DeleteAccountInput:
    """Input for deleting user account (GDPR Right to Erasure - Art. 17).

    Attributes:
        password: Current password for confirmation
        confirmation_text: User must type "DELETE MY ACCOUNT" to confirm
    """

    password: str
    confirmation_text: str


@strawberry.input
class ExportMyDataInput:
    """Input for DSAR - Data Subject Access Request (GDPR Art. 15).

    Attributes:
        format: Export format ("json" or "csv")
        include_audit_logs: Whether to include audit logs
        include_ip_tracking: Whether to include IP tracking data
        include_login_history: Whether to include login attempt history
    """

    format: str = "json"  # "json" or "csv"
    include_audit_logs: bool = True
    include_ip_tracking: bool = True
    include_login_history: bool = True


@strawberry.type
class UpdateEmailPayload:
    """Response payload for updating email.

    Attributes:
        success: Whether update succeeded
        message: User-friendly message
        verification_email_sent: Whether verification email was sent to new address
    """

    success: bool
    message: str
    verification_email_sent: bool


@strawberry.type
class UpdatePhoneNumberPayload:
    """Response payload for updating phone number.

    Attributes:
        success: Whether update succeeded
        message: User-friendly message
        verification_sms_sent: Whether verification SMS was sent to new number
    """

    success: bool
    message: str
    verification_sms_sent: bool


@strawberry.type
class UpdateUsernamePayload:
    """Response payload for updating username.

    Attributes:
        success: Whether update succeeded
        message: User-friendly message
        new_username: Updated username
    """

    success: bool
    message: str
    new_username: str | None = None


@strawberry.type
class DeleteAccountPayload:
    """Response payload for deleting account.

    Attributes:
        success: Whether deletion was initiated
        message: User-friendly message
        deletion_scheduled_for: Timestamp when account will be permanently deleted
        grace_period_days: Number of days until permanent deletion
    """

    success: bool
    message: str
    deletion_scheduled_for: str | None = None
    grace_period_days: int


@strawberry.type
class WithdrawPhoneConsentPayload:
    """Response payload for withdrawing phone consent (GDPR Art. 7(3)).

    Attributes:
        success: Whether consent withdrawal succeeded
        message: User-friendly message
        phone_removed: Whether phone number was removed
    """

    success: bool
    message: str
    phone_removed: bool


@strawberry.type
class OptOutOfIPTrackingPayload:
    """Response payload for opting out of IP tracking (GDPR Art. 21).

    Attributes:
        success: Whether opt-out succeeded
        message: User-friendly message
        records_deleted: Number of IP tracking records deleted
    """

    success: bool
    message: str
    records_deleted: int


@strawberry.type
class ExportMyDataPayload:
    """Response payload for DSAR - Data Subject Access Request.

    Attributes:
        success: Whether export succeeded
        message: User-friendly message
        download_url: URL to download exported data
        format: Export format (json or csv)
        expires_at: When download link expires
        file_size_bytes: Size of export file in bytes
    """

    success: bool
    message: str
    download_url: str | None = None
    format: str
    expires_at: str | None = None
    file_size_bytes: int | None = None
