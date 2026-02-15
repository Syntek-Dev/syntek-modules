"""PII access logging service for GDPR Article 32 compliance.

This module provides audit logging for all PII access operations including:
- Admin access to encrypted emails
- Admin access to encrypted phone numbers
- Admin access to encrypted IP addresses
- Export operations
- Deletion operations

SECURITY NOTE (GDPR Article 32):
- Log all admin access to encrypted PII
- Include timestamp, admin user, action, resource
- Retain logs for 3 years (EU) / 5 years (USA)
- Provide logs for data subject access requests
- Automatic log rotation and archival

Example:
    >>> PIIAccessLogService.log_access(admin_user, "view", "email", user_id, user)
    >>> logs = PIIAccessLogService.get_access_logs_for_user(user)
    >>> PIIAccessLogService.export_access_logs_for_user(user)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from django.http import HttpRequest

    from syntek_authentication.models import PIIAccessLog, User

logger = logging.getLogger(__name__)


class PIIAccessLogService:
    """Service for logging PII access (GDPR Article 32 compliance).

    Handles audit logging for:
    1. Admin access to encrypted emails
    2. Admin access to encrypted phone numbers
    3. Admin access to encrypted IP addresses
    4. Export operations (GDPR Article 20)
    5. Deletion operations (GDPR Article 17)

    Features:
    - Automatic logging on PII decryption
    - Timestamp and admin tracking
    - Resource type and action tracking
    - Export for data subject access requests
    - Retention policy enforcement

    Attributes:
        VALID_ACTIONS: Valid action types
        VALID_RESOURCE_TYPES: Valid resource types
        RETENTION_DAYS_EU: EU retention period (GDPR)
        RETENTION_DAYS_USA: USA retention period (CCPA)
    """

    VALID_ACTIONS = ["view", "export", "modify", "delete"]
    VALID_RESOURCE_TYPES = ["email", "phone", "ip_address", "full_profile"]

    # Retention periods per region
    RETENTION_DAYS_EU = 2555  # ~7 years (EU financial record standard)
    RETENTION_DAYS_USA = 1825  # ~5 years (California AG recommendation)
    RETENTION_DAYS_GLOBAL = 1095  # ~3 years (default)

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
    @transaction.atomic
    def log_access(
        admin_user: "User",
        action: str,
        resource_type: str,
        resource_id: int | str,
        user_affected: "User",
        request: "HttpRequest | None" = None,
    ) -> "PIIAccessLog":
        """Log PII access operation.

        Args:
            admin_user: Admin performing the operation.
            action: Type of action (view, export, modify, delete).
            resource_type: Type of resource (email, phone, ip_address, full_profile).
            resource_id: ID of accessed resource.
            user_affected: User whose PII was accessed.
            request: Django HTTP request (optional).

        Returns:
            PIIAccessLog object.

        Raises:
            ValueError: If invalid action or resource type.
        """
        from syntek_authentication.models import PIIAccessLog

        # Validate action
        if action not in PIIAccessLogService.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action: {action}. Must be one of {PIIAccessLogService.VALID_ACTIONS}"
            )

        # Validate resource type
        if resource_type not in PIIAccessLogService.VALID_RESOURCE_TYPES:
            raise ValueError(
                f"Invalid resource type: {resource_type}. "
                f"Must be one of {PIIAccessLogService.VALID_RESOURCE_TYPES}"
            )

        # Get admin IP address
        admin_ip = PIIAccessLogService._get_client_ip(request)

        # Create log entry
        log_entry = PIIAccessLog.objects.create(
            admin_user=admin_user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_affected=user_affected,
            ip_address=admin_ip,
        )

        logger.info(
            f"PII access logged: admin={admin_user.id}, action={action}, "
            f"resource={resource_type}, user={user_affected.id}"
        )

        return log_entry

    @staticmethod
    def get_access_logs_for_user(user: "User", limit: int = 100) -> list["PIIAccessLog"]:
        """Get PII access logs for user (for GDPR access requests).

        Args:
            user: User whose logs to retrieve.
            limit: Maximum number of logs to return.

        Returns:
            List of PIIAccessLog objects.
        """
        from syntek_authentication.models import PIIAccessLog

        return list(
            PIIAccessLog.objects.filter(user_affected=user).order_by("-accessed_at")[:limit]
        )

    @staticmethod
    def get_access_logs_for_admin(admin_user: "User", limit: int = 100) -> list["PIIAccessLog"]:
        """Get PII access logs by admin.

        Args:
            admin_user: Admin whose logs to retrieve.
            limit: Maximum number of logs to return.

        Returns:
            List of PIIAccessLog objects.
        """
        from syntek_authentication.models import PIIAccessLog

        return list(
            PIIAccessLog.objects.filter(admin_user=admin_user).order_by("-accessed_at")[:limit]
        )

    @staticmethod
    def export_access_logs_for_user(user: "User") -> dict:
        """Export PII access logs for user (GDPR Article 15 compliance).

        Args:
            user: User whose logs to export.

        Returns:
            Dict with formatted access logs.
        """
        logs = PIIAccessLogService.get_access_logs_for_user(user, limit=1000)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "access_logs": [
                {
                    "timestamp": log.accessed_at.isoformat(),
                    "admin_email": log.admin_user.email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "admin_ip": log.ip_address,
                }
                for log in logs
            ],
            "total_accesses": len(logs),
        }

    @staticmethod
    def cleanup_old_logs(region: str = "GLOBAL") -> int:
        """Clean up old PII access logs based on retention policy.

        Args:
            region: Region for retention policy (EU, USA, GLOBAL).

        Returns:
            Number of logs deleted.
        """
        from syntek_authentication.models import PIIAccessLog

        # Determine retention period
        if region == "EU":
            retention_days = PIIAccessLogService.RETENTION_DAYS_EU
        elif region == "USA":
            retention_days = PIIAccessLogService.RETENTION_DAYS_USA
        else:
            retention_days = PIIAccessLogService.RETENTION_DAYS_GLOBAL

        cutoff_date = timezone.now() - timedelta(days=retention_days)

        deleted_count, _ = PIIAccessLog.objects.filter(accessed_at__lt=cutoff_date).delete()

        logger.info(
            f"Cleaned up {deleted_count} old PII access logs "
            f"(region={region}, retention={retention_days} days)"
        )

        return deleted_count

    @staticmethod
    def get_access_statistics(user: "User") -> dict:
        """Get PII access statistics for user.

        Args:
            user: User whose statistics to retrieve.

        Returns:
            Dict with access statistics.
        """
        from django.db.models import Count

        from syntek_authentication.models import PIIAccessLog

        # Get counts by action
        action_counts = (
            PIIAccessLog.objects.filter(user_affected=user)
            .values("action")
            .annotate(count=Count("action"))
        )

        # Get counts by resource type
        resource_counts = (
            PIIAccessLog.objects.filter(user_affected=user)
            .values("resource_type")
            .annotate(count=Count("resource_type"))
        )

        # Get recent access date
        recent_log = (
            PIIAccessLog.objects.filter(user_affected=user).order_by("-accessed_at").first()
        )

        return {
            "total_accesses": PIIAccessLog.objects.filter(user_affected=user).count(),
            "by_action": {item["action"]: item["count"] for item in action_counts},
            "by_resource": {item["resource_type"]: item["count"] for item in resource_counts},
            "last_access": recent_log.accessed_at.isoformat() if recent_log else None,
            "last_admin": recent_log.admin_user.email if recent_log else None,
        }
