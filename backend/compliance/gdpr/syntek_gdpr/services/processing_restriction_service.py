"""Processing restriction service for GDPR Article 18 compliance.

This module implements the Right to Restriction of Processing (Article 18)
by providing functionality for users to restrict how their data is processed.

GDPR Requirements (Article 18):
- Users can restrict processing when contesting data accuracy
- Users can restrict processing instead of erasure
- Users can restrict processing when processing is unlawful
- Users can restrict processing when data needed for legal claims

When processing is restricted:
- Data is stored but not processed (except storage)
- User can still authenticate (essential processing)
- Data not used for analytics or marketing
- Data not shared with third parties
- Security logging continues (legal obligation)

Example:
    >>> from syntek_gdpr.services.processing_restriction_service import ProcessingRestrictionService
    >>> ProcessingRestrictionService.restrict_processing(user, "Contesting accuracy")
    >>> is_restricted = ProcessingRestrictionService.is_restricted(user)
    >>> ProcessingRestrictionService.lift_restriction(user)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    pass

# Import services if available
try:
    from syntek_audit.services import AuditService
except ImportError:
    AuditService = None  # type: ignore[assignment, misc]


class ProcessingRestrictionService:
    """Service for processing restriction (GDPR Article 18).

    Handles the restriction and lifting of data processing for users.
    When restricted, user data should only be stored, not processed
    for purposes other than essential authentication.

    Processing Restrictions Applied:
    - No analytics or tracking
    - No marketing communications
    - No data sharing with third parties
    - No automated decision-making
    - Essential authentication still allowed
    - Security logging still allowed (legal obligation)

    Security Features:
    - All restriction changes are audit logged
    - Restriction reason is recorded
    - Timestamps track when restriction was applied/lifted

    Attributes:
        None - All methods are static
    """

    @staticmethod
    def restrict_processing(
        user,
        reason: str,
        ip_address: str = "",
        user_agent: str = "",
    ):
        """Restrict processing of user data.

        Sets the processing_restricted flag on the user account.
        All non-essential processing should check this flag.

        Args:
            user: User requesting restriction.
            reason: Reason for restriction (required).
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            Updated User instance.

        Raises:
            ValueError: If reason is not provided or already restricted.
        """
        if not reason or not reason.strip():
            raise ValueError("A reason for restriction is required.")

        if hasattr(user, "processing_restricted") and user.processing_restricted:
            raise ValueError("Processing is already restricted for this account.")

        user.processing_restricted = True
        user.restriction_reason = reason.strip()
        user.restricted_at = timezone.now()
        user.save(update_fields=["processing_restricted", "restriction_reason", "restricted_at"])

        # Audit log the restriction
        if AuditService:
            AuditService.log_event(
                action="processing_restricted",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "reason": reason.strip(),
                },
            )

        return user

    @staticmethod
    def lift_restriction(
        user,
        ip_address: str = "",
        user_agent: str = "",
    ):
        """Lift processing restriction from user data.

        Removes the processing_restricted flag, allowing normal
        data processing to resume.

        Args:
            user: User lifting restriction.
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            Updated User instance.

        Raises:
            ValueError: If processing is not currently restricted.
        """
        if not hasattr(user, "processing_restricted") or not user.processing_restricted:
            raise ValueError("Processing is not currently restricted for this account.")

        previous_reason = user.restriction_reason
        previous_restricted_at = user.restricted_at

        user.processing_restricted = False
        user.restriction_reason = ""
        user.restricted_at = None
        user.save(update_fields=["processing_restricted", "restriction_reason", "restricted_at"])

        # Audit log the lift
        if AuditService:
            AuditService.log_event(
                action="processing_restriction_lifted",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "previous_reason": previous_reason,
                    "was_restricted_at": (
                        previous_restricted_at.isoformat() if previous_restricted_at else None
                    ),
                },
            )

        return user

    @staticmethod
    def is_restricted(user) -> bool:
        """Check if processing is restricted for a user.

        Args:
            user: User to check.

        Returns:
            True if processing is restricted, False otherwise.
        """
        return getattr(user, "processing_restricted", False)

    @staticmethod
    def get_restriction_details(user) -> dict:
        """Get processing restriction details for a user.

        Args:
            user: User to get details for.

        Returns:
            Dictionary containing restriction status and details.
        """
        processing_restricted = getattr(user, "processing_restricted", False)

        return {
            "processing_restricted": processing_restricted,
            "restriction_reason": user.restriction_reason if processing_restricted else None,
            "restricted_at": (
                user.restricted_at.isoformat()
                if processing_restricted and hasattr(user, "restricted_at") and user.restricted_at
                else None
            ),
            "allowed_processing": [
                "Authentication (login/logout)",
                "Security logging",
                "Data storage",
                "Data export requests",
                "Account deletion requests",
            ]
            if processing_restricted
            else None,
            "restricted_processing": [
                "Analytics and tracking",
                "Marketing communications",
                "Data sharing with third parties",
                "Automated decision-making",
                "Profiling",
            ]
            if processing_restricted
            else None,
        }

    @staticmethod
    def check_can_process(user, processing_type: str) -> bool:
        """Check if a specific type of processing is allowed.

        Use this method before performing non-essential processing
        to ensure compliance with restriction status.

        Args:
            user: User to check.
            processing_type: Type of processing to check. Allowed values:
                - "essential": Authentication, security (always allowed)
                - "analytics": Analytics and tracking
                - "marketing": Marketing communications
                - "sharing": Third-party data sharing
                - "automated": Automated decision-making

        Returns:
            True if processing is allowed, False if restricted.
        """
        # Essential processing is always allowed
        if processing_type == "essential":
            return True

        # When restricted, only essential processing is allowed
        return not getattr(user, "processing_restricted", False)
