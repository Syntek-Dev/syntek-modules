"""GraphQL queries for GDPR data subject access requests.

This module defines queries for exporting user data in compliance with
GDPR Article 15 (Right to Access).

SECURITY FEATURES:
- User can only export their own data
- All encrypted fields decrypted for user
- Comprehensive data export (authentication, sessions, MFA, etc.)
- JSON and CSV format support
- Audit logging for compliance
- Temporary download URL with expiry

Implements requirements:
- Phase 2.3: GDPR data export query
- GDPR Article 15: Data Subject Access Request (DSAR)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.gdpr import (  # type: ignore[import]
    ExportMyDataInput,
    ExportMyDataPayload,
)

logger = logging.getLogger(__name__)


@strawberry.type
class GDPRQueries:
    """GraphQL queries for GDPR data access rights."""

    @strawberry.field
    def export_my_data(self, info: Info, input: ExportMyDataInput) -> ExportMyDataPayload:
        """Export all user data (GDPR Article 15 - Data Subject Access Request).

        Exports comprehensive authentication data for the authenticated user including:
        - User profile (email, username, phone - all decrypted)
        - Registration date and verification status
        - Login history (IP addresses decrypted)
        - IP tracking history with geolocation
        - Active and expired sessions
        - MFA devices (TOTP, backup codes, recovery keys)
        - Audit logs (if requested)
        - Consent records

        Security Features:
        - User can only export their own data
        - All encrypted fields decrypted (email, phone, IP addresses)
        - Supports JSON and CSV formats
        - Generates temporary download URL (expires in 1 hour)
        - Comprehensive audit logging
        - GDPR Article 15 compliance

        Args:
            info: GraphQL execution info
            input: Export configuration (format, include options)

        Returns:
            ExportMyDataPayload with download URL and metadata

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If format invalid or export fails

        Example:
            >>> query {
            >>>   exportMyData(input: {
            >>>     format: "json",
            >>>     includeAuditLogs: true,
            >>>     includeIpTracking: true,
            >>>     includeLoginHistory: true
            >>>   }) {
            >>>     success
            >>>     message
            >>>     downloadUrl
            >>>     format
            >>>     expiresAt
            >>>     fileSizeBytes
            >>>   }
            >>> }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Validate format
        if input.format not in ["json", "csv"]:
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                'Invalid format. Must be "json" or "csv"',
            )

        # Import service
        try:
            from apps.core.services.audit_service import AuditService  # type: ignore[import]
            from syntek_authentication.services.gdpr_service import (
                GDPRService,  # type: ignore[import]
            )
        except ImportError:
            logger.error("GDPRService not available")
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Data export service not available. Please contact support.",
            )

        # Generate data export
        try:
            export_result = GDPRService.export_user_data(
                user=user,
                format=input.format,
                include_audit_logs=input.include_audit_logs,
                include_ip_tracking=input.include_ip_tracking,
                include_login_history=input.include_login_history,
            )

            # Log DSAR (GDPR compliance requirement)
            AuditService.log_event(
                action="gdpr_dsar_requested",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "format": input.format,
                    "include_audit_logs": input.include_audit_logs,
                    "include_ip_tracking": input.include_ip_tracking,
                    "include_login_history": input.include_login_history,
                    "file_size_bytes": export_result["file_size_bytes"],
                    "download_url_expires_at": export_result["expires_at"],
                },
            )

            return ExportMyDataPayload(
                success=True,
                message="Data export complete. Download link expires in 1 hour.",
                download_url=export_result["download_url"],
                format=input.format,
                expires_at=export_result["expires_at"],
                file_size_bytes=export_result["file_size_bytes"],
            )

        except Exception as e:
            logger.error(f"Failed to export user data: {e}")

            # Log failed DSAR
            AuditService.log_event(
                action="gdpr_dsar_failed",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "format": input.format,
                    "error": str(e),
                },
            )

            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Failed to generate data export. Please try again or contact support.",
            )
