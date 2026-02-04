"""Consent service for GDPR consent management.

This module provides business logic for managing user consent records
in compliance with GDPR Articles 6 and 7 (lawful basis and consent requirements).

GDPR Requirements:
- Consent must be freely given, specific, informed, and unambiguous
- Users can withdraw consent at any time
- Consent versioning for policy changes
- Audit trail with IP address and user agent

Example:
    >>> from syntek_gdpr.services.consent_service import ConsentService
    >>> ConsentService.grant_consent(user, "marketing", "1.0.0", ip_address="192.168.1.1")
    >>> ConsentService.withdraw_consent(user, "marketing")
    >>> status = ConsentService.get_consent_status(user, "marketing")
"""

from django.db import transaction
from django.utils import timezone

from syntek_gdpr.models import ConsentRecord

# Import audit service if available
try:
    from syntek_audit.services import AuditService
except ImportError:
    AuditService = None  # type: ignore[assignment, misc]


class ConsentService:
    """Service for managing user consent records.

    Handles granting, withdrawing, and checking consent for different
    types of data processing activities.

    Consent Types:
    - essential: Required for service functionality (always granted)
    - functional: Preferences, language settings
    - analytics: Google Analytics, usage tracking
    - marketing: Email marketing, ad tracking

    Security Features:
    - All consent changes are audit logged
    - IP addresses are encrypted
    - Consent versioning tracks policy changes
    - Complete withdrawal history maintained

    Attributes:
        None - All methods are static
    """

    @staticmethod
    @transaction.atomic
    def grant_consent(
        user,
        consent_type: str,
        version: str = "1.0.0",
        ip_address: str | None = None,
        user_agent: str = "",
        metadata: dict | None = None,
    ) -> ConsentRecord:
        """Grant consent for a specific processing activity.

        Creates a new consent record or updates existing one.
        Automatically withdraws any previous consent for the same type.

        Args:
            user: User granting consent.
            consent_type: Type of consent (essential, functional, analytics, marketing).
            version: Version of consent policy being accepted.
            ip_address: IP address where consent was given (will be encrypted).
            user_agent: Browser user agent string.
            metadata: Additional metadata (referrer, language, etc.).

        Returns:
            Created ConsentRecord instance.

        Raises:
            ValueError: If consent_type is invalid.
        """
        # Validate consent type
        valid_types = [choice[0] for choice in ConsentRecord.ConsentType.choices]
        if consent_type not in valid_types:
            raise ValueError(f"Invalid consent type: {consent_type}. Must be one of {valid_types}")

        # Withdraw any previous consent for this type
        ConsentRecord.objects.filter(
            user=user,
            consent_type=consent_type,
            granted=True,
        ).update(
            granted=False,
            withdrawn_at=timezone.now(),
        )

        # Prepare metadata
        consent_metadata = metadata or {}
        if ip_address:
            consent_metadata["ip_address"] = ip_address

        # Create new consent record
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type=consent_type,
            granted=True,
            version=version,
            user_agent=user_agent,
            metadata=consent_metadata,
        )

        # Audit log the grant
        if AuditService:
            AuditService.log_event(
                action="consent_granted",
                user=user,
                ip_address=ip_address or "",
                user_agent=user_agent,
                metadata={
                    "consent_type": consent_type,
                    "version": version,
                    "consent_id": str(consent.id),
                },
            )

        return consent

    @staticmethod
    @transaction.atomic
    def withdraw_consent(
        user,
        consent_type: str,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> ConsentRecord | None:
        """Withdraw consent for a specific processing activity.

        Marks the active consent record as withdrawn.

        Args:
            user: User withdrawing consent.
            consent_type: Type of consent to withdraw.
            ip_address: IP address where withdrawal occurred.
            user_agent: Browser user agent string.

        Returns:
            Updated ConsentRecord instance or None if no active consent found.

        Raises:
            ValueError: If attempting to withdraw essential consent.
        """
        # Prevent withdrawal of essential consent
        if consent_type == ConsentRecord.ConsentType.ESSENTIAL:
            raise ValueError("Essential consent cannot be withdrawn (required for service)")

        # Find active consent record
        try:
            consent = ConsentRecord.objects.get(
                user=user,
                consent_type=consent_type,
                granted=True,
                withdrawn_at__isnull=True,
            )
        except ConsentRecord.DoesNotExist:
            return None

        # Mark as withdrawn
        consent.granted = False
        consent.withdrawn_at = timezone.now()
        consent.save(update_fields=["granted", "withdrawn_at"])

        # Audit log the withdrawal
        if AuditService:
            AuditService.log_event(
                action="consent_withdrawn",
                user=user,
                ip_address=ip_address or "",
                user_agent=user_agent,
                metadata={
                    "consent_type": consent_type,
                    "consent_id": str(consent.id),
                },
            )

        return consent

    @staticmethod
    def get_consent_status(user, consent_type: str) -> bool:
        """Check if user has granted consent for a specific type.

        Args:
            user: User to check consent for.
            consent_type: Type of consent to check.

        Returns:
            True if user has active consent, False otherwise.
        """
        return ConsentRecord.objects.filter(
            user=user,
            consent_type=consent_type,
            granted=True,
            withdrawn_at__isnull=True,
        ).exists()

    @staticmethod
    def get_all_consents(user) -> dict[str, bool]:
        """Get consent status for all types.

        Args:
            user: User to get consents for.

        Returns:
            Dictionary mapping consent types to their status (True/False).
        """
        active_consents = ConsentRecord.objects.filter(
            user=user,
            granted=True,
            withdrawn_at__isnull=True,
        ).values_list("consent_type", flat=True)

        return {
            ConsentRecord.ConsentType.ESSENTIAL: ConsentRecord.ConsentType.ESSENTIAL in active_consents,
            ConsentRecord.ConsentType.FUNCTIONAL: ConsentRecord.ConsentType.FUNCTIONAL in active_consents,
            ConsentRecord.ConsentType.ANALYTICS: ConsentRecord.ConsentType.ANALYTICS in active_consents,
            ConsentRecord.ConsentType.MARKETING: ConsentRecord.ConsentType.MARKETING in active_consents,
        }

    @staticmethod
    def get_consent_history(user, consent_type: str | None = None) -> list[ConsentRecord]:
        """Get consent history for a user.

        Args:
            user: User to get history for.
            consent_type: Optional specific consent type to filter by.

        Returns:
            List of ConsentRecord instances ordered by grant date (newest first).
        """
        queryset = ConsentRecord.objects.filter(user=user)

        if consent_type:
            queryset = queryset.filter(consent_type=consent_type)

        return list(queryset.order_by("-granted_at"))

    @staticmethod
    def update_consent_version(
        user,
        consent_type: str,
        new_version: str,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> ConsentRecord:
        """Update consent to a new policy version.

        Withdraws old consent and creates new consent record with updated version.
        Use this when consent policies are updated and require re-acceptance.

        Args:
            user: User updating consent.
            consent_type: Type of consent to update.
            new_version: New version number.
            ip_address: IP address where update occurred.
            user_agent: Browser user agent string.

        Returns:
            New ConsentRecord instance with updated version.
        """
        # Withdraw old consent
        ConsentService.withdraw_consent(  # pyright: ignore[reportCallIssue]
            user=user,  # pyright: ignore[reportCallIssue]
            consent_type=consent_type,  # pyright: ignore[reportCallIssue]
            ip_address=ip_address,  # pyright: ignore[reportCallIssue]
            user_agent=user_agent,  # pyright: ignore[reportCallIssue]
        )

        # Grant new consent with new version
        return ConsentService.grant_consent(  # pyright: ignore[reportCallIssue]
            user=user,  # pyright: ignore[reportCallIssue]
            consent_type=consent_type,  # pyright: ignore[reportCallIssue]
            version=new_version,  # pyright: ignore[reportCallIssue]
            ip_address=ip_address,  # pyright: ignore[reportCallIssue]
            user_agent=user_agent,  # pyright: ignore[reportCallIssue]
        )

    @staticmethod
    def bulk_grant_consent(
        user,
        consent_types: list[str],
        version: str = "1.0.0",
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> list[ConsentRecord]:
        """Grant multiple consents at once.

        Useful for initial registration or cookie consent banners.

        Args:
            user: User granting consents.
            consent_types: List of consent types to grant.
            version: Version of consent policy.
            ip_address: IP address where consents were given.
            user_agent: Browser user agent string.

        Returns:
            List of created ConsentRecord instances.
        """
        consents = []

        for consent_type in consent_types:
            consent = ConsentService.grant_consent(  # pyright: ignore[reportCallIssue]
                user=user,  # pyright: ignore[reportCallIssue]
                consent_type=consent_type,  # pyright: ignore[reportCallIssue]
                version=version,  # pyright: ignore[reportCallIssue]
                ip_address=ip_address,  # pyright: ignore[reportCallIssue]
                user_agent=user_agent,  # pyright: ignore[reportCallIssue]
            )
            consents.append(consent)

        return consents

    @staticmethod
    def check_requires_renewal(user, consent_type: str, current_version: str) -> bool:
        """Check if consent needs to be renewed due to policy version change.

        Args:
            user: User to check.
            consent_type: Type of consent to check.
            current_version: Current policy version.

        Returns:
            True if user's consent version is outdated, False otherwise.
        """
        try:
            consent = ConsentRecord.objects.get(
                user=user,
                consent_type=consent_type,
                granted=True,
                withdrawn_at__isnull=True,
            )
            return consent.version != current_version
        except ConsentRecord.DoesNotExist:
            return True  # No consent granted, requires new consent
