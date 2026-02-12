"""Consent management service for GDPR Article 7 compliance.

This module provides consent tracking functionality including:
- Consent recording with timestamp and version
- Consent withdrawal tracking
- Consent audit trail
- Regional consent management (EU, USA, etc.)

SECURITY NOTE (GDPR Article 7):
- Record all consent grants and withdrawals
- Include timestamp, version, region, IP address
- Retain consent logs for 7 years (EU) / 5 years (USA)
- Provide consent history for data subject access requests
- Support granular consent (phone, marketing, analytics, etc.)

Example:
    >>> ConsentService.grant_consent(user, "phone", "1.2-EU", "EU", request)
    >>> ConsentService.withdraw_consent(user, "marketing_email", request)
    >>> consents = ConsentService.get_active_consents(user)
"""

import logging
from typing import TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from django.http import HttpRequest

    from syntek_authentication.models import ConsentLog, User

logger = logging.getLogger(__name__)


class ConsentService:
    """Service for managing user consent (GDPR Article 7 compliance).

    Handles consent lifecycle:
    1. Recording consent grants with metadata
    2. Tracking consent withdrawals
    3. Maintaining audit trail
    4. Regional consent management

    Features:
    - Granular consent types
    - Version tracking
    - Regional compliance
    - Audit trail
    - Withdrawal support

    Attributes:
        VALID_CONSENT_TYPES: Valid consent types
        VALID_REGIONS: Valid region codes
    """

    VALID_CONSENT_TYPES = [
        "phone",
        "marketing_email",
        "marketing_sms",
        "analytics",
        "third_party_sharing",
        "profiling",
        "newsletter",
    ]

    VALID_REGIONS = ["EU", "USA", "CA", "AU", "UK", "GLOBAL"]

    @staticmethod
    def _get_client_ip(request: "HttpRequest | None") -> str:
        """Extract client IP address from request.

        Args:
            request: Django HTTP request (optional).

        Returns:
            Client IP address or 'system' if no request.
        """
        if not request:
            return "system"

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "system")

    @staticmethod
    def _get_user_agent(request: "HttpRequest | None") -> str:
        """Extract user agent from request.

        Args:
            request: Django HTTP request (optional).

        Returns:
            User agent string or 'system' if no request.
        """
        if not request:
            return "system"

        return request.META.get("HTTP_USER_AGENT", "unknown")[:500]

    @staticmethod
    @transaction.atomic
    def grant_consent(
        user: "User",
        consent_type: str,
        version: str,
        region: str,
        request: "HttpRequest | None" = None,
    ) -> "ConsentLog":
        """Grant consent for user.

        Args:
            user: User granting consent.
            consent_type: Type of consent (phone, marketing_email, etc.).
            version: Privacy policy/terms version (e.g., "1.2-EU").
            region: Geographic region (EU, USA, etc.).
            request: Django HTTP request (optional).

        Returns:
            ConsentLog object.

        Raises:
            ValueError: If invalid consent type or region.
        """
        from syntek_authentication.models import ConsentLog

        # Validate consent type
        if consent_type not in ConsentService.VALID_CONSENT_TYPES:
            raise ValueError(
                f"Invalid consent type: {consent_type}. "
                f"Must be one of {ConsentService.VALID_CONSENT_TYPES}"
            )

        # Validate region
        if region not in ConsentService.VALID_REGIONS:
            raise ValueError(
                f"Invalid region: {region}. Must be one of {ConsentService.VALID_REGIONS}"
            )

        # Get request metadata
        ip_address = ConsentService._get_client_ip(request)
        user_agent = ConsentService._get_user_agent(request)

        # Create consent log
        consent_log = ConsentLog.objects.create(
            user=user,
            consent_type=consent_type,
            granted=True,
            version=version,
            region=region,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            f"Consent granted: user={user.id}, type={consent_type}, "
            f"version={version}, region={region}"
        )

        return consent_log

    @staticmethod
    @transaction.atomic
    def withdraw_consent(
        user: "User",
        consent_type: str,
        request: "HttpRequest | None" = None,
    ) -> "ConsentLog":
        """Withdraw consent for user.

        Args:
            user: User withdrawing consent.
            consent_type: Type of consent to withdraw.
            request: Django HTTP request (optional).

        Returns:
            ConsentLog object.

        Raises:
            ValueError: If invalid consent type.
        """
        from syntek_authentication.models import ConsentLog

        # Validate consent type
        if consent_type not in ConsentService.VALID_CONSENT_TYPES:
            raise ValueError(
                f"Invalid consent type: {consent_type}. "
                f"Must be one of {ConsentService.VALID_CONSENT_TYPES}"
            )

        # Get current consent to copy version/region
        current_consent = ConsentLog.get_current_consent(user, consent_type)

        version = "N/A"
        region = "GLOBAL"
        if current_consent:
            version = current_consent.version
            region = current_consent.region

        # Get request metadata
        ip_address = ConsentService._get_client_ip(request)
        user_agent = ConsentService._get_user_agent(request)

        # Create withdrawal log
        consent_log = ConsentLog.objects.create(
            user=user,
            consent_type=consent_type,
            granted=False,  # Withdrawal
            version=version,
            region=region,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(f"Consent withdrawn: user={user.id}, type={consent_type}")

        return consent_log

    @staticmethod
    def has_consent(user: "User", consent_type: str) -> bool:
        """Check if user has active consent for type.

        Args:
            user: User to check.
            consent_type: Type of consent to check.

        Returns:
            True if consent granted, False otherwise.
        """
        from syntek_authentication.models import ConsentLog

        current_consent = ConsentLog.get_current_consent(user, consent_type)
        return current_consent is not None and current_consent.granted

    @staticmethod
    def get_active_consents(user: "User") -> dict[str, "ConsentLog"]:
        """Get all active consents for user.

        Args:
            user: User whose consents to retrieve.

        Returns:
            Dict mapping consent type to ConsentLog object.
        """
        from syntek_authentication.models import ConsentLog

        active_consents = {}

        for consent_type in ConsentService.VALID_CONSENT_TYPES:
            current_consent = ConsentLog.get_current_consent(user, consent_type)
            if current_consent and current_consent.granted:
                active_consents[consent_type] = current_consent

        return active_consents

    @staticmethod
    def get_consent_history(user: "User", consent_type: str | None = None) -> list["ConsentLog"]:
        """Get consent history for user.

        Args:
            user: User whose history to retrieve.
            consent_type: Optional filter by consent type.

        Returns:
            List of ConsentLog objects.
        """
        from syntek_authentication.models import ConsentLog

        queryset = ConsentLog.objects.filter(user=user).order_by("-created_at")

        if consent_type:
            queryset = queryset.filter(consent_type=consent_type)

        return list(queryset)

    @staticmethod
    def export_consent_data(user: "User") -> dict:
        """Export consent data for user (GDPR Article 15 compliance).

        Args:
            user: User whose consent data to export.

        Returns:
            Dict with formatted consent data.
        """
        active_consents = ConsentService.get_active_consents(user)
        consent_history = ConsentService.get_consent_history(user)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "active_consents": {
                consent_type: {
                    "granted_at": log.created_at.isoformat(),
                    "version": log.version,
                    "region": log.region,
                }
                for consent_type, log in active_consents.items()
            },
            "consent_history": [
                {
                    "timestamp": log.created_at.isoformat(),
                    "consent_type": log.consent_type,
                    "granted": log.granted,
                    "version": log.version,
                    "region": log.region,
                    "ip_address": log.ip_address,
                }
                for log in consent_history
            ],
            "total_consent_changes": len(consent_history),
        }

    @staticmethod
    @transaction.atomic
    def update_consent_for_region_change(
        user: "User", old_region: str, new_region: str, request: "HttpRequest | None" = None
    ) -> list["ConsentLog"]:
        """Update all consents when user changes region.

        Creates new consent logs with new region while preserving granted status.

        Args:
            user: User changing region.
            old_region: Previous region.
            new_region: New region.
            request: Django HTTP request (optional).

        Returns:
            List of new ConsentLog objects.
        """
        active_consents = ConsentService.get_active_consents(user)
        new_consent_logs = []

        for consent_type, old_consent in active_consents.items():
            # Create new consent log with new region
            new_consent = ConsentService.grant_consent(
                user=user,
                consent_type=consent_type,
                version=old_consent.version.replace(old_region, new_region),
                region=new_region,
                request=request,
            )
            new_consent_logs.append(new_consent)

        logger.info(
            f"Updated {len(new_consent_logs)} consents for user {user.id} "
            f"(region change: {old_region} -> {new_region})"
        )

        return new_consent_logs
