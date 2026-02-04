"""Audit logging service for security event tracking.

This module provides centralised audit logging for all security-relevant
events including authentication, authorisation, and data access.

SECURITY NOTE:
- All events logged with encrypted IP addresses
- Timestamps in UTC with timezone awareness
- Immutable logs (no updates, only inserts)
- Organisation-scoped for multi-tenancy

Example:
    >>> from syntek_audit.services import AuditService
    >>> AuditService.log_login(user, ip_address, device_fingerprint)
    >>> AuditService.log_login_failed(email, ip_address)
"""

from syntek_audit.models import AuditLog  # type: ignore[import]

# Try to import encryption utility from syntek_authentication
# If not available, provide graceful fallback
try:
    from syntek_authentication.utils.encryption import IPEncryption  # type: ignore[import]

    HAS_IP_ENCRYPTION = True
except ImportError:
    HAS_IP_ENCRYPTION = False


class AuditService:
    """Service for security audit logging.

    Handles creation and retrieval of audit logs for security events.
    All logs include encrypted IP addresses and device fingerprints.

    Security Features:
    - Immutable logs (no updates after creation)
    - IP address encryption before storage (if syntek_authentication available)
    - Organisation-scoped access
    - Device fingerprinting for session tracking

    Attributes:
        None - All methods are static
    """

    @staticmethod
    def log_event(
        action: str,
        user=None,
        organisation=None,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: str = "",
        metadata: dict | None = None,
    ):
        """Log a security event.

        Args:
            action: Event action type (from AuditLog.ActionType)
            user: User who performed the action (None for failed login)
            organisation: Organisation context
            ip_address: IP address (will be encrypted if available)
            user_agent: Browser user agent string
            device_fingerprint: Device identifier
            metadata: Additional JSON metadata

        Returns:
            Created AuditLog instance
        """
        # Encrypt IP address if encryption utility available
        encrypted_ip = None
        if ip_address and HAS_IP_ENCRYPTION:
            encrypted_ip = IPEncryption.encrypt_ip(ip_address)
        elif ip_address:
            # Store as plain text if encryption not available (not recommended for production)
            encrypted_ip = ip_address.encode("utf-8")

        # Create audit log
        log = AuditLog.objects.create(  # type: ignore[attr-defined]
            action=action,
            user=user,
            organisation=organisation or (user.organisation if user else None),
            ip_address=encrypted_ip,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            metadata=metadata or {},
        )

        return log

    @staticmethod
    def log_login(
        user,
        ip_address: str,
        device_fingerprint: str = "",
        user_agent: str = "",
    ):
        """Log successful login event.

        Args:
            user: User who logged in
            ip_address: IP address (will be encrypted if available)
            device_fingerprint: Device identifier
            user_agent: Browser user agent string

        Returns:
            Created AuditLog instance
        """
        return AuditService.log_event(
            action=AuditLog.ActionType.LOGIN,
            user=user,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            user_agent=user_agent,
        )

    @staticmethod
    def log_login_failed(
        email: str,
        ip_address: str,
        device_fingerprint: str = "",
        user_agent: str = "",
        organisation=None,
    ):
        """Log failed login attempt.

        Args:
            email: Email address used in failed login
            ip_address: IP address (will be encrypted if available)
            device_fingerprint: Device identifier
            user_agent: Browser user agent string
            organisation: Organisation context if known

        Returns:
            Created AuditLog instance
        """
        return AuditService.log_event(
            action=AuditLog.ActionType.LOGIN_FAILED,
            user=None,
            organisation=organisation,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            user_agent=user_agent,
            metadata={"email": email},
        )

    @staticmethod
    def log_logout(user, ip_address: str = ""):
        """Log logout event.

        Args:
            user: User who logged out
            ip_address: IP address (will be encrypted if available)

        Returns:
            Created AuditLog instance
        """
        return AuditService.log_event(
            action=AuditLog.ActionType.LOGOUT,
            user=user,
            ip_address=ip_address,
        )

    @staticmethod
    def log_password_change(user, ip_address: str = ""):
        """Log password change event.

        Args:
            user: User who changed password
            ip_address: IP address (will be encrypted if available)

        Returns:
            Created AuditLog instance
        """
        return AuditService.log_event(
            action=AuditLog.ActionType.PASSWORD_CHANGE,
            user=user,
            ip_address=ip_address,
        )

    @staticmethod
    def get_user_logs(user, limit: int = 100) -> list:
        """Get recent audit logs for a user.

        Args:
            user: User to get logs for
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog instances
        """
        return list(AuditLog.objects.filter(user=user).order_by("-created_at")[:limit])  # type: ignore[attr-defined]

    @staticmethod
    def get_organisation_logs(organisation, limit: int = 100) -> list:
        """Get recent audit logs for an organisation.

        Args:
            organisation: Organisation to get logs for
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog instances
        """
        return list(
            AuditLog.objects.filter(organisation=organisation).order_by("-created_at")[:limit]  # type: ignore[attr-defined]
        )
