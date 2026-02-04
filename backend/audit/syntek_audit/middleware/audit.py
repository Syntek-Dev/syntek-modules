"""Security audit logging middleware.

This module provides middleware to log security-relevant events such as:
- Successful and failed authentication attempts
- Authorization failures (403 errors)
- Suspicious request patterns
- CSRF validation failures

Audit logs are written to a separate logger channel for security analysis
and compliance requirements.

GDPR Compliance:
- Security audit logs retain full IP addresses (legitimate interest for security)
- Non-security logs should use anonymised IPs via anonymise_ip()
- Recommended retention: 90 days for security logs, 30 days for general logs
"""

import logging
from typing import TYPE_CHECKING, Any

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from syntek_audit.utils.request import anonymise_ip, get_client_ip

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

# Security audit logger (configured separately from application logs)
security_logger = logging.getLogger("security.audit")

# Re-export for backwards compatibility
__all__ = ["SecurityAuditMiddleware", "anonymise_ip", "get_client_ip"]


def _get_request_header(request: HttpRequest, header_name: str, default: str = "") -> str:
    """Safely get a header value from the request.

    Args:
        request: The HTTP request object.
        header_name: The header name to retrieve.
        default: Default value if header is not present.

    Returns:
        The header value or default.
    """
    return getattr(request.headers, "get", lambda k, d: d)(header_name, default)


class SecurityAuditMiddleware(MiddlewareMixin):
    """Log security-relevant events for audit and compliance purposes.

    This middleware logs the following events:
    - HTTP 403 (Forbidden) responses
    - HTTP 401 (Unauthorized) responses
    - CSRF validation failures
    - Authentication attempts (via Django signals)

    All logs include:
    - Timestamp (automatic via logger)
    - Client IP address
    - Request path
    - HTTP method
    - User agent
    - User (if authenticated)

    Security logs should be sent to a separate logging handler for:
    - Long-term retention
    - Security monitoring and alerting
    - Compliance audit trails
    """

    @staticmethod
    def _get_header(request: HttpRequest, header_name: str, default: str = "") -> str:
        """Safely get a header value from the request.

        Args:
            request: The HTTP request object.
            header_name: The header name to retrieve.
            default: Default value if header is not present.

        Returns:
            The header value or default.
        """
        return _get_request_header(request, header_name, default)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log security events based on response status codes.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.

        Returns:
            The unmodified HTTP response.
        """
        # Log authorization failures
        if response.status_code == 403:
            self._log_authorization_failure(request, response)

        # Log authentication failures
        if response.status_code == 401:
            self._log_authentication_required(request, response)

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse | None:
        """Log security exceptions.

        Args:
            request: The HTTP request object.
            exception: The exception that was raised.

        Returns:
            None (allows normal exception handling to continue).
        """
        if isinstance(exception, PermissionDenied):
            self._log_authorization_failure(request, None)

        return None

    def _log_authorization_failure(
        self, request: HttpRequest, response: HttpResponse | None
    ) -> None:
        """Log when a user is denied access to a resource.

        Uses full IP for security logging (legitimate interest under GDPR).

        Args:
            request: The HTTP request object.
            response: The HTTP response object (may be None for exceptions).
        """
        user: AbstractBaseUser | AnonymousUser = getattr(request, "user", None)  # type: ignore[assignment]
        is_authenticated = getattr(user, "is_authenticated", False)

        security_logger.warning(
            "Authorization failure",
            extra={
                "event_type": "authorization_failure",
                "client_ip": get_client_ip(request),  # Full IP for security
                "path": request.path,
                "method": request.method,
                "user": str(user) if is_authenticated else "anonymous",
                "user_id": getattr(user, "id", None) if is_authenticated else None,
                "user_agent": self._get_header(request, "user-agent"),
                "referer": self._get_header(request, "referer"),
            },
        )

    def _log_authentication_required(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log when authentication is required but not provided.

        Uses full IP for security logging (legitimate interest under GDPR).

        Args:
            request: The HTTP request object.
            response: The HTTP response object.
        """
        security_logger.info(
            "Authentication required",
            extra={
                "event_type": "authentication_required",
                "client_ip": get_client_ip(request),  # Full IP for security
                "path": request.path,
                "method": request.method,
                "user_agent": self._get_header(request, "user-agent"),
            },
        )


# Signal handlers for authentication events


@receiver(user_logged_in)
def log_user_login(sender: Any, request: HttpRequest, user: Any, **kwargs: Any) -> None:
    """Log successful user login events.

    Uses full IP for security logging (legitimate interest under GDPR).

    Args:
        sender: The sender of the signal.
        request: The HTTP request object.
        user: The user who logged in.
        **kwargs: Additional keyword arguments from the signal.
    """
    # Use email as identifier for custom User model (no username field)
    user_identifier = getattr(user, "email", str(user))
    security_logger.info(
        f"User login successful: {user_identifier}",
        extra={
            "event_type": "login_success",
            "user": str(user),
            "user_id": user.id,
            "email": user_identifier,
            "client_ip": get_client_ip(request),  # Full IP for security
            "user_agent": _get_request_header(request, "user-agent"),
        },
    )


@receiver(user_logged_out)
def log_user_logout(sender: Any, request: HttpRequest, user: Any, **kwargs: Any) -> None:
    """Log user logout events.

    Uses full IP for security logging (legitimate interest under GDPR).

    Args:
        sender: The sender of the signal.
        request: The HTTP request object.
        user: The user who logged out.
        **kwargs: Additional keyword arguments from the signal.
    """
    if user is None:
        return

    # Use email as identifier for custom User model (no username field)
    user_identifier = getattr(user, "email", str(user))
    security_logger.info(
        f"User logout: {user_identifier}",
        extra={
            "event_type": "logout",
            "user": str(user),
            "user_id": user.id,
            "email": user_identifier,
            "client_ip": get_client_ip(request),  # Full IP for security
        },
    )


@receiver(user_login_failed)
def log_user_login_failed(
    sender: Any, credentials: Any, request: HttpRequest | None = None, **kwargs: Any
) -> None:
    """Log failed login attempts.

    Uses full IP for security logging (legitimate interest under GDPR).

    Args:
        sender: The sender of the signal.
        credentials: The credentials that were attempted.
        request: The HTTP request object (may be None).
        **kwargs: Additional keyword arguments from the signal.
    """
    if request is None:
        return

    client_ip = get_client_ip(request)  # Full IP for security

    # Support both username and email fields for custom User model
    user_identifier = credentials.get("email") or credentials.get("username", "unknown")

    security_logger.warning(
        f"Failed login attempt for: {user_identifier}",
        extra={
            "event_type": "login_failure",
            "email": user_identifier,
            "client_ip": client_ip,
            "user_agent": _get_request_header(request, "user-agent"),
        },
    )
