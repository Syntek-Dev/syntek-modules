"""GraphQL types for phone verification operations.

This module defines input and output types for phone verification via SMS.
"""

from __future__ import annotations

import strawberry


@strawberry.input
class SendPhoneVerificationInput:
    """Input for sending phone verification SMS.

    Attributes:
        phone_number: E.164 format phone number (e.g., +44XXXXXXXXXX)
    """

    phone_number: str


@strawberry.input
class VerifyPhoneInput:
    """Input for verifying phone number with SMS code.

    Attributes:
        phone_number: E.164 format phone number
        code: 6-digit verification code from SMS
    """

    phone_number: str
    code: str


@strawberry.type
class PhoneVerificationType:
    """GraphQL type for phone verification token.

    Represents a phone verification attempt with status information.

    Attributes:
        id: Token UUID
        phone_number_masked: Masked phone number for display (e.g., +44****1234)
        created_at: Token creation timestamp
        expires_at: Token expiry timestamp
        is_expired: Whether token has expired
        is_used: Whether token has been used
        attempts_remaining: Number of verification attempts remaining (max 5)
    """

    id: strawberry.ID
    phone_number_masked: str
    created_at: str
    expires_at: str
    is_expired: bool
    is_used: bool
    attempts_remaining: int


@strawberry.type
class SendPhoneVerificationPayload:
    """Response payload for sending phone verification SMS.

    Attributes:
        success: Whether SMS was sent successfully
        message: User-friendly message
        verification_id: ID of verification token (for tracking)
        expires_at: When the code expires
    """

    success: bool
    message: str
    verification_id: strawberry.ID | None = None
    expires_at: str | None = None


@strawberry.type
class VerifyPhonePayload:
    """Response payload for phone verification.

    Attributes:
        success: Whether verification succeeded
        message: User-friendly message
        phone_verified: Whether user's phone is now verified
    """

    success: bool
    message: str
    phone_verified: bool
