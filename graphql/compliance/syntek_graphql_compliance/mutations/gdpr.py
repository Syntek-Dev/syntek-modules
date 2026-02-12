"""GraphQL mutations for GDPR compliance operations.

This module provides GraphQL mutations for GDPR-related operations
including requesting data exports, account deletion, managing
processing restrictions, and updating consent preferences.

All mutations require authentication and operate on the authenticated
user's data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.models import ConsentRecord  # type: ignore[import]
from apps.core.services.account_deletion_service import (  # type: ignore[import]
    AccountDeletionService,
)
from apps.core.services.data_export_service import DataExportService  # type: ignore[import]
from apps.core.services.processing_restriction_service import (  # type: ignore[import]
    ProcessingRestrictionService,
)
from apps.core.utils.encryption import IPEncryption  # type: ignore[import]

from syntek_graphql_compliance.types.gdpr import (  # type: ignore[import]
    AccountDeletionPayload,
    AccountDeletionRequestType,
    CancelAccountDeletionInput,
    ConfirmAccountDeletionInput,
    ConsentPayload,
    ConsentRecordType,
    ConsentType,
    DataExportPayload,
    DataExportRequestType,
    ProcessingRestrictionInput,
    ProcessingRestrictionPayload,
    ProcessingRestrictionType,
    RequestAccountDeletionInput,
    RequestDataExportInput,
    UpdateConsentInput,
)


def get_client_ip(request) -> str:
    """Extract client IP address from request.

    Args:
        request: Django HTTP request.

    Returns:
        Client IP address string.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent(request) -> str:
    """Extract user agent from request.

    Args:
        request: Django HTTP request.

    Returns:
        User agent string.
    """
    return request.META.get("HTTP_USER_AGENT", "")


@strawberry.type
class GDPRMutations:
    """GraphQL mutations for GDPR compliance.

    Provides mutations for data export, account deletion, processing
    restriction, and consent management.
    """

    @strawberry.mutation
    def request_data_export(
        self,
        info: Info,
        input: RequestDataExportInput,
    ) -> DataExportPayload:
        """Request export of user's personal data (GDPR Article 15).

        Creates a data export request that will be processed asynchronously.
        The export file will be available for download for 24 hours after
        completion.

        Rate limited to one export per 24 hours.

        Args:
            info: GraphQL resolver info containing request context.
            input: Export request input with format preference.

        Returns:
            DataExportPayload with export request details.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return DataExportPayload(
                success=False,
                message="Authentication required.",
                export_request=None,
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            export_request = DataExportService.request_export(
                user=user,
                export_format=input.format.value,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Trigger async processing (Celery task)
            from apps.core.tasks import process_data_export_task  # type: ignore[import]

            process_data_export_task.delay(str(export_request.id))  # type: ignore[misc]

            return DataExportPayload(
                success=True,
                message="Data export request submitted. You will be notified when ready.",
                export_request=DataExportRequestType.from_model(export_request),
            )

        except ValueError as e:
            return DataExportPayload(
                success=False,
                message=str(e),
                export_request=None,
            )

    @strawberry.mutation
    def request_account_deletion(
        self,
        info: Info,
        input: RequestAccountDeletionInput,
    ) -> AccountDeletionPayload:
        """Request account deletion (GDPR Article 17).

        Creates a pending account deletion request. A confirmation email
        will be sent to the user's email address. The user must confirm
        the deletion within 24 hours.

        Args:
            info: GraphQL resolver info containing request context.
            input: Deletion request input with optional reason.

        Returns:
            AccountDeletionPayload with deletion request details.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return AccountDeletionPayload(
                success=False,
                message="Authentication required.",
                deletion_request=None,
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            deletion_request = AccountDeletionService.request_deletion(
                user=user,
                reason=input.reason or "",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return AccountDeletionPayload(
                success=True,
                message="Deletion request submitted. Please check your email to confirm.",
                deletion_request=AccountDeletionRequestType.from_model(deletion_request),
            )

        except ValueError as e:
            return AccountDeletionPayload(
                success=False,
                message=str(e),
                deletion_request=None,
            )

    @strawberry.mutation
    def confirm_account_deletion(
        self,
        info: Info,
        input: ConfirmAccountDeletionInput,
    ) -> AccountDeletionPayload:
        """Confirm and execute account deletion.

        Verifies the confirmation token and password, then permanently
        deletes the user account and associated data. This action is
        irreversible.

        Args:
            info: GraphQL resolver info containing request context.
            input: Confirmation input with token and password.

        Returns:
            AccountDeletionPayload with deletion result.
        """
        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            deletion_request = AccountDeletionService.confirm_deletion(
                token=input.token,
                password=input.password,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return AccountDeletionPayload(
                success=True,
                message="Account deletion completed. Your data has been removed.",
                deletion_request=AccountDeletionRequestType.from_model(deletion_request),
            )

        except ValueError as e:
            return AccountDeletionPayload(
                success=False,
                message=str(e),
                deletion_request=None,
            )

    @strawberry.mutation
    def cancel_account_deletion(
        self,
        info: Info,
        input: CancelAccountDeletionInput,
    ) -> AccountDeletionPayload:
        """Cancel a pending account deletion request.

        Cancels the specified deletion request if it is still pending
        and belongs to the authenticated user.

        Args:
            info: GraphQL resolver info containing request context.
            input: Cancellation input with request ID.

        Returns:
            AccountDeletionPayload with cancellation result.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return AccountDeletionPayload(
                success=False,
                message="Authentication required.",
                deletion_request=None,
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            deletion_request = AccountDeletionService.cancel_deletion(
                request_id=UUID(str(input.request_id)),
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return AccountDeletionPayload(
                success=True,
                message="Deletion request cancelled.",
                deletion_request=AccountDeletionRequestType.from_model(deletion_request),
            )

        except ValueError as e:
            return AccountDeletionPayload(
                success=False,
                message=str(e),
                deletion_request=None,
            )

    @strawberry.mutation
    def update_processing_restriction(
        self,
        info: Info,
        input: ProcessingRestrictionInput,
    ) -> ProcessingRestrictionPayload:
        """Update processing restriction status (GDPR Article 18).

        Restricts or lifts restriction on processing of user's personal data.
        When restricted, data will only be stored and not processed for
        non-essential purposes.

        Args:
            info: GraphQL resolver info containing request context.
            input: Restriction input with restrict flag and optional reason.

        Returns:
            ProcessingRestrictionPayload with updated restriction status.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return ProcessingRestrictionPayload(
                success=False,
                message="Authentication required.",
                restriction=None,
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            if input.restrict:
                if not input.reason:
                    return ProcessingRestrictionPayload(
                        success=False,
                        message="A reason is required when restricting processing.",
                        restriction=None,
                    )

                ProcessingRestrictionService.restrict_processing(
                    user=user,
                    reason=input.reason,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                message = "Processing restriction applied."
            else:
                ProcessingRestrictionService.lift_restriction(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                message = "Processing restriction lifted."

            # Refresh user from database
            user.refresh_from_db()

            details = ProcessingRestrictionService.get_restriction_details(user)

            return ProcessingRestrictionPayload(
                success=True,
                message=message,
                restriction=ProcessingRestrictionType(
                    processing_restricted=details["processing_restricted"],
                    restriction_reason=details["restriction_reason"],
                    restricted_at=user.restricted_at if user.processing_restricted else None,
                    allowed_processing=details["allowed_processing"],
                    restricted_processing=details["restricted_processing"],
                ),
            )

        except ValueError as e:
            return ProcessingRestrictionPayload(
                success=False,
                message=str(e),
                restriction=None,
            )

    @strawberry.mutation
    def update_consent(
        self,
        info: Info,
        input: UpdateConsentInput,
    ) -> ConsentPayload:
        """Update consent for a specific processing type.

        Records the user's consent decision for a specific type of
        data processing (e.g., analytics, marketing).

        Args:
            info: GraphQL resolver info containing request context.
            input: Consent input with type and granted flag.

        Returns:
            ConsentPayload with updated consent record.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return ConsentPayload(
                success=False,
                message="Authentication required.",
                consent=None,
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Essential consent cannot be withdrawn
        if input.consent_type == ConsentType.ESSENTIAL and not input.granted:
            return ConsentPayload(
                success=False,
                message="Essential processing consent cannot be withdrawn.",
                consent=None,
            )

        # Encrypt IP address
        encrypted_ip = IPEncryption.encrypt_ip(ip_address) if ip_address else None

        # Withdraw any existing active consent of this type
        if not input.granted:
            from django.utils import timezone

            ConsentRecord.objects.filter(
                user=user,
                consent_type=input.consent_type.value,
                granted=True,
                withdrawn_at__isnull=True,
            ).update(withdrawn_at=timezone.now())

        # Create new consent record
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type=input.consent_type.value,
            granted=input.granted,
            ip_address=encrypted_ip,
            user_agent=user_agent,
        )

        action = "granted" if input.granted else "withdrawn"
        return ConsentPayload(
            success=True,
            message=f"Consent for {input.consent_type.value} processing {action}.",
            consent=ConsentRecordType.from_model(consent),
        )
