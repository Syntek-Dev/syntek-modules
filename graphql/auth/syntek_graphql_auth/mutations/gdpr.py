"""GraphQL mutations for GDPR compliance operations.

This module defines mutations for data subject rights including:
- Right to Rectification (Art. 16): Update email, phone, username
- Right to Erasure (Art. 17): Delete account
- Right to Object (Art. 21): Opt out of IP tracking
- Consent Management (Art. 7): Withdraw phone consent

SECURITY FEATURES:
- Password verification required for all rectification operations
- Soft delete with 30-day grace period for erasure
- Immediate session invalidation on deletion
- Audit logging for all GDPR operations
- Verification emails/SMS for contact updates

SOCIAL AUTHENTICATION INTEGRATION:
- Social account data included in DSAR exports (see gdpr_social_extensions.py)
- OAuth tokens revoked on account deletion (see gdpr_social_extensions.py)
- Social login history included in exports
- Helper functions: get_social_account_export_data(), revoke_all_oauth_tokens()

Implements requirements:
- GAP-04: Email and phone rectification
- GAP-05: Username rectification
- GAP-07: Account deletion with grace period
- GAP-13: Phone consent withdrawal
- GAP-16: IP tracking opt-out
- Phase 2.8: Social authentication GDPR compliance
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.contrib.auth import authenticate
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.gdpr_service import GDPRService  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.gdpr import (  # type: ignore[import]
    DeleteAccountInput,
    DeleteAccountPayload,
    OptOutOfIPTrackingPayload,
    UpdateEmailInput,
    UpdateEmailPayload,
    UpdatePhoneNumberInput,
    UpdatePhoneNumberPayload,
    UpdateUsernameInput,
    UpdateUsernamePayload,
    WithdrawPhoneConsentPayload,
)

logger = logging.getLogger(__name__)


@strawberry.type
class GDPRMutations:
    """GraphQL mutations for GDPR data subject rights."""

    @strawberry.mutation
    def update_email(self, info: Info, input: UpdateEmailInput) -> UpdateEmailPayload:
        """Update user email address (GDPR Right to Rectification - Art. 16).

        Updates email with password verification and sends verification email
        to new address. Email change is atomic after verification.

        Security Features:
        - Password verification required
        - Verification email sent to new address
        - Atomic email change after verification
        - Old email notified of change
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Update input (password, new_email)

        Returns:
            UpdateEmailPayload with success status

        Raises:
            AuthenticationError: If user not authenticated or password invalid
            ValidationError: If email already exists or invalid format
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Verify password
        auth_user = authenticate(
            request=request,
            email=user.email,  # type: ignore[attr-defined]
            password=input.password,
        )

        if not auth_user:
            # Log failed password verification
            AuditService.log_event(
                action="update_email_failed_password",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"new_email_masked": input.new_email[:3] + "***"},
            )

            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Update email with verification
            verification_sent = GDPRService.update_email(
                user=user,
                new_email=input.new_email,
                ip_address=ip_address,
            )

            # Log email update request
            AuditService.log_event(
                action="email_update_requested",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "old_email_masked": user.email[:3] + "***",  # type: ignore[attr-defined]
                    "new_email_masked": input.new_email[:3] + "***",
                },
            )

            return UpdateEmailPayload(
                success=True,
                message=f"Verification email sent to {input.new_email}. Please verify to complete change.",
                verification_email_sent=verification_sent,
            )

    @strawberry.mutation
    def update_phone_number(
        self, info: Info, input: UpdatePhoneNumberInput
    ) -> UpdatePhoneNumberPayload:
        """Update user phone number (GDPR Right to Rectification - Art. 16).

        Updates phone with password verification and sends verification SMS
        to new number. Phone change is atomic after verification.

        Security Features:
        - Password verification required
        - Verification SMS sent to new number
        - Atomic phone change after verification
        - E.164 format validation
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Update input (password, new_phone_number)

        Returns:
            UpdatePhoneNumberPayload with success status

        Raises:
            AuthenticationError: If user not authenticated or password invalid
            ValidationError: If phone format invalid
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Verify password
        auth_user = authenticate(
            request=request,
            email=user.email,  # type: ignore[attr-defined]
            password=input.password,
        )

        if not auth_user:
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Update phone with verification
            verification, masked_phone = GDPRService.update_phone_number(
                user=user,
                new_phone_number=input.new_phone_number,
                ip_address=ip_address,
            )

            # Log phone update request
            AuditService.log_event(
                action="phone_update_requested",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"new_phone_masked": masked_phone},
            )

            return UpdatePhoneNumberPayload(
                success=True,
                message=f"Verification SMS sent to {masked_phone}. Please verify to complete change.",
                verification_sms_sent=True,
            )

    @strawberry.mutation
    def update_username(self, info: Info, input: UpdateUsernameInput) -> UpdateUsernamePayload:
        """Update username (GDPR Right to Rectification - Art. 16).

        Updates username with password verification and uniqueness check.

        Security Features:
        - Password verification required
        - Username uniqueness validation
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Update input (password, new_username)

        Returns:
            UpdateUsernamePayload with success status

        Raises:
            AuthenticationError: If user not authenticated or password invalid
            ValidationError: If username already exists
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Verify password
        auth_user = authenticate(
            request=request,
            email=user.email,  # type: ignore[attr-defined]
            password=input.password,
        )

        if not auth_user:
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Update username
            new_username = GDPRService.update_username(
                user=user,
                new_username=input.new_username,
            )

            # Log username update
            AuditService.log_event(
                action="username_updated",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "old_username": getattr(user, "username", None),
                    "new_username": new_username,
                },
            )

            return UpdateUsernamePayload(
                success=True,
                message="Username updated successfully",
                new_username=new_username,
            )

    @strawberry.mutation
    def delete_account(self, info: Info, input: DeleteAccountInput) -> DeleteAccountPayload:
        """Delete user account (GDPR Right to Erasure - Art. 17).

        Soft deletes account with 30-day grace period. User can cancel deletion
        within grace period. After 30 days, account is permanently deleted.

        Security Features:
        - Password verification required
        - Confirmation text required ("DELETE MY ACCOUNT")
        - Soft delete with 30-day grace period
        - Immediate session invalidation
        - Schedule hard delete job
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user
            input: Delete input (password, confirmation_text)

        Returns:
            DeleteAccountPayload with deletion schedule

        Raises:
            AuthenticationError: If user not authenticated or password invalid
            ValidationError: If confirmation text incorrect
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Verify password
        auth_user = authenticate(
            request=request,
            email=user.email,  # type: ignore[attr-defined]
            password=input.password,
        )

        if not auth_user:
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid password",
            )

        # Verify confirmation text
        if input.confirmation_text != "DELETE MY ACCOUNT":
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                'Please type "DELETE MY ACCOUNT" to confirm deletion',
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Soft delete account with 30-day grace period
            deletion_scheduled_for = GDPRService.delete_account(
                user=user,
                ip_address=ip_address,
            )

            # Log account deletion request
            AuditService.log_event(
                action="account_deletion_requested",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "deletion_scheduled_for": deletion_scheduled_for.isoformat(),
                    "grace_period_days": 30,
                },
            )

            return DeleteAccountPayload(
                success=True,
                message="Account deletion scheduled. You have 30 days to cancel.",
                deletion_scheduled_for=deletion_scheduled_for.isoformat(),
                grace_period_days=30,
            )

    @strawberry.mutation
    def withdraw_phone_consent(self, info: Info) -> WithdrawPhoneConsentPayload:
        """Withdraw phone consent (GDPR Consent Withdrawal - Art. 7(3)).

        Removes phone number from account and withdraws consent for SMS communications.

        Security Features:
        - Removes phone number from database
        - Logs consent withdrawal in ConsentLog
        - Disables SMS-based features
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            WithdrawPhoneConsentPayload with success status

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Withdraw phone consent
            phone_removed = GDPRService.withdraw_phone_consent(
                user=user,
                ip_address=ip_address,
            )

            # Log consent withdrawal
            AuditService.log_event(
                action="phone_consent_withdrawn",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"phone_removed": phone_removed},
            )

            return WithdrawPhoneConsentPayload(
                success=True,
                message="Phone consent withdrawn and phone number removed",
                phone_removed=phone_removed,
            )

    @strawberry.mutation
    def opt_out_of_ip_tracking(self, info: Info) -> OptOutOfIPTrackingPayload:
        """Opt out of IP address tracking (GDPR Right to Object - Art. 21).

        Stops collecting IP addresses for user and deletes existing IP tracking data.

        Security Features:
        - Stop collecting IP addresses
        - Delete existing IP tracking records
        - Log opt-out decision in ConsentLog
        - Audit logging

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            OptOutOfIPTrackingPayload with deletion count

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Opt out of IP tracking
            records_deleted = GDPRService.opt_out_of_ip_tracking(
                user=user,
                ip_address=ip_address,
            )

            # Log opt-out
            AuditService.log_event(
                action="ip_tracking_opt_out",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"records_deleted": records_deleted},
            )

            return OptOutOfIPTrackingPayload(
                success=True,
                message=f"IP tracking disabled. Deleted {records_deleted} existing records.",
                records_deleted=records_deleted,
            )
