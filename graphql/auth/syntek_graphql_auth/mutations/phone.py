"""GraphQL mutations for phone verification operations.

This module defines mutations for phone verification with rate limiting
and security requirements from Phase 2.2.

SECURITY FEATURES:
- Per-IP rate limiting: 3/hour for sendPhoneVerification (prevent SMS cost attacks)
- Per-IP rate limiting: 5/15min for verifyPhone
- Global SMS budget enforcement: $500/day (configurable)
- CAPTCHA escalation after 100 SMS/hour globally
- Audit logging for all verification attempts
- Cost monitoring and alerting

Implements requirements:
- M-2: Global SMS cost attack prevention
- GDPR: Phone consent tracking
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.phone_verification_service import (
    PhoneVerificationService,  # type: ignore[import]
)
from syntek_graphql_core.decorators import rate_limit  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.phone import (  # type: ignore[import]
    SendPhoneVerificationInput,
    SendPhoneVerificationPayload,
    VerifyPhoneInput,
    VerifyPhonePayload,
)

logger = logging.getLogger(__name__)


@strawberry.type
class PhoneMutations:
    """GraphQL mutations for phone verification."""

    @strawberry.mutation
    @rate_limit("3/hour", scope="ip")  # Prevent SMS cost attacks (M-2)
    def send_phone_verification(
        self, info: Info, input: SendPhoneVerificationInput
    ) -> SendPhoneVerificationPayload:
        """Send SMS verification code to phone number.

        Sends a 6-digit verification code via SMS with rate limiting to prevent
        cost attacks. Implements global SMS budget enforcement and CAPTCHA escalation.

        Security Features:
        - Per-IP rate limiting: 3/hour (prevent SMS abuse)
        - Global rate limiting: 1000/hour across all IPs
        - Daily budget enforcement: $500/day (configurable)
        - CAPTCHA escalation after 100 SMS/hour globally
        - Cost monitoring and alerting
        - E.164 phone number validation

        GDPR Compliance:
        - Requires phone_consent: true
        - Logs consent in ConsentLog
        - Audit logs all verification attempts

        Args:
            info: GraphQL execution info with authenticated user
            input: Phone verification input (phone_number, phone_consent)

        Returns:
            SendPhoneVerificationPayload with success status and masked phone

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If phone format invalid or consent not provided
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Validate phone consent (GDPR requirement - GAP-03)
        if not input.phone_consent:
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Phone consent required for SMS verification",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Check global SMS budget (M-2)
            if not PhoneVerificationService.check_global_budget():
                # Log budget exceeded
                AuditService.log_event(
                    action="phone_verification_budget_exceeded",
                    user=user,
                    organisation=getattr(user, "organisation", None),
                    ip_address=ip_address,
                    metadata={"phone_number_masked": input.phone_number[-4:]},
                )

                raise ValidationError(
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    "SMS service temporarily unavailable. Please try again later.",
                )

            # Send verification code via SMS
            verification, masked_phone = PhoneVerificationService.send_verification(
                user=user,
                phone_number=input.phone_number,
                phone_consent=input.phone_consent,
                ip_address=ip_address,
            )

            # Log verification sent
            AuditService.log_event(
                action="phone_verification_sent",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "phone_number_masked": masked_phone,
                    "verification_id": str(verification.id),
                    "expires_at": verification.expires_at.isoformat(),
                },
            )

            return SendPhoneVerificationPayload(
                success=True,
                message=f"Verification code sent to {masked_phone}",
                phone_number_masked=masked_phone,
                expires_at=verification.expires_at.isoformat(),
            )

    @strawberry.mutation
    @rate_limit("5/15min", scope="ip")  # Prevent brute force
    def verify_phone(self, info: Info, input: VerifyPhoneInput) -> VerifyPhonePayload:
        """Verify phone number with SMS code.

        Validates the 6-digit code sent via SMS and marks phone as verified.
        Implements rate limiting to prevent brute force attacks.

        Security Features:
        - Per-IP rate limiting: 5/15min (prevent brute force)
        - Constant-time code comparison
        - Automatic code expiry (15 minutes)
        - Attempt tracking (max 5 attempts)
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Verification input (phone_number, code)

        Returns:
            VerifyPhonePayload with success status

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If code invalid or expired
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Verify code
            is_valid, message = PhoneVerificationService.verify_code(
                user=user,
                phone_number=input.phone_number,
                code=input.code,
            )

            # Log verification attempt
            AuditService.log_event(
                action="phone_verification_attempt",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "phone_number_masked": input.phone_number[-4:],
                    "success": is_valid,
                    "message": message,
                },
            )

            if not is_valid:
                raise ValidationError(ErrorCode.VALIDATION_ERROR, message)

            return VerifyPhonePayload(
                success=True,
                message="Phone number verified successfully",
                phone_verified=True,
            )
