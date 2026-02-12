"""CSRF protection middleware for GraphQL and REST APIs.

This middleware provides enhanced CSRF protection compatible with GraphQL,
using double-submit cookie pattern and custom headers.

Works alongside Django's built-in CSRF for comprehensive protection.
"""

import logging
import secrets
from typing import Callable
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import CsrfViewMiddleware as DjangoCsrfMiddleware

logger = logging.getLogger(__name__)


class GraphQLCSRFMiddleware:
    """CSRF protection for GraphQL and AJAX requests.

    Implements double-submit cookie pattern with custom headers for
    GraphQL compatibility. Works in addition to Django's CSRF middleware.

    Protection mechanisms:
    1. Custom header verification (X-CSRFToken)
    2. Double-submit cookie pattern
    3. Origin/Referer header validation
    4. Token rotation on authentication changes

    Configuration (settings.py):
        SYNTEK_SECURITY_CORE = {
            'CSRF': {
                'ENABLED': True,
                'TOKEN_ROTATION': True,  # Rotate on login/logout
                'COOKIE_NAME': 'csrftoken',
                'HEADER_NAME': 'HTTP_X_CSRFTOKEN',
                'COOKIE_AGE': 31449600,  # 1 year
                'COOKIE_SECURE': True,   # Require HTTPS
                'COOKIE_HTTPONLY': False,  # Must be readable by JS
                'COOKIE_SAMESITE': 'Strict',
                'EXEMPT_PATHS': ['/health/', '/metrics/'],
                'GRAPHQL_PATHS': ['/graphql', '/api/graphql'],
            }
        }

    Example:
        # In settings.py
        MIDDLEWARE = [
            ...
            'django.middleware.csrf.CsrfViewMiddleware',
            'syntek_security_core.middleware.GraphQLCSRFMiddleware',
            ...
        ]
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize middleware.

        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.config = self._get_config()
        self.django_csrf = DjangoCsrfMiddleware(get_response)

    def _get_config(self) -> dict:
        """Get CSRF configuration from settings.

        Returns:
            dict: Configuration dictionary with CSRF settings
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_CORE", {})
        csrf_config = security_config.get("CSRF", {})

        # Default configuration
        defaults = {
            "ENABLED": True,
            "TOKEN_ROTATION": True,
            "COOKIE_NAME": "csrftoken",
            "HEADER_NAME": "HTTP_X_CSRFTOKEN",
            "COOKIE_AGE": 31449600,  # 1 year
            "COOKIE_SECURE": not settings.DEBUG,
            "COOKIE_HTTPONLY": False,
            "COOKIE_SAMESITE": "Strict",
            "EXEMPT_PATHS": ["/health/", "/metrics/", "/admin/"],
            "GRAPHQL_PATHS": ["/graphql", "/api/graphql"],
            "SAFE_METHODS": {"GET", "HEAD", "OPTIONS", "TRACE"},
        }

        # Merge with user configuration
        defaults.update(csrf_config)
        return defaults

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and enforce CSRF protection.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse: Response, or 403 if CSRF validation fails
        """
        if not self.config.get("ENABLED", True):
            return self.get_response(request)

        # Check if path is exempt
        if self._is_exempt(request):
            return self.get_response(request)

        # Safe methods don't need CSRF protection
        if request.method in self.config.get("SAFE_METHODS", {"GET", "HEAD", "OPTIONS", "TRACE"}):
            response = self.get_response(request)
            self._set_csrf_cookie(request, response)
            return response

        # Check if this is a GraphQL request
        is_graphql = self._is_graphql_request(request)

        # Verify CSRF token
        if not self._verify_csrf_token(request, is_graphql):
            return self._csrf_failure_response(request)

        # Verify origin/referer headers
        if not self._verify_origin(request):
            return self._csrf_failure_response(request, reason="Invalid origin")

        response = self.get_response(request)

        # Set/update CSRF cookie in response
        self._set_csrf_cookie(request, response)

        return response

    def _is_exempt(self, request: HttpRequest) -> bool:
        """Check if request path is exempt from CSRF protection.

        Args:
            request: Django HTTP request

        Returns:
            bool: True if path is exempt
        """
        exempt_paths = self.config.get("EXEMPT_PATHS", [])
        return any(request.path.startswith(path) for path in exempt_paths)

    def _is_graphql_request(self, request: HttpRequest) -> bool:
        """Check if request is to a GraphQL endpoint.

        Args:
            request: Django HTTP request

        Returns:
            bool: True if GraphQL request
        """
        graphql_paths = self.config.get("GRAPHQL_PATHS", [])
        return any(request.path.startswith(path) for path in graphql_paths)

    def _verify_csrf_token(self, request: HttpRequest, is_graphql: bool) -> bool:
        """Verify CSRF token from header and cookie.

        Args:
            request: Django HTTP request
            is_graphql: Whether this is a GraphQL request

        Returns:
            bool: True if token is valid
        """
        # Get token from custom header
        header_name = self.config.get("HEADER_NAME", "HTTP_X_CSRFTOKEN")
        token_from_header = request.META.get(header_name, "")

        # Get token from cookie
        cookie_name = self.config.get("COOKIE_NAME", "csrftoken")
        token_from_cookie = request.COOKIES.get(cookie_name, "")

        # Both must be present
        if not token_from_header or not token_from_cookie:
            logger.warning(
                f"CSRF token missing: header={bool(token_from_header)}, "
                f"cookie={bool(token_from_cookie)}"
            )
            return False

        # Tokens must match (double-submit pattern)
        if not secrets.compare_digest(token_from_header, token_from_cookie):
            logger.warning("CSRF token mismatch between header and cookie")
            return False

        logger.debug("CSRF token validation successful")
        return True

    def _verify_origin(self, request: HttpRequest) -> bool:
        """Verify Origin or Referer header matches allowed origins.

        Args:
            request: Django HTTP request

        Returns:
            bool: True if origin is valid
        """
        # Get allowed hosts from Django settings
        allowed_hosts = settings.ALLOWED_HOSTS

        # Get origin from header
        origin = request.META.get("HTTP_ORIGIN", "")
        referer = request.META.get("HTTP_REFERER", "")

        # At least one must be present
        if not origin and not referer:
            logger.warning("Neither Origin nor Referer header present")
            return False

        # Extract host from origin/referer
        if origin:
            origin_host = origin.split("://")[-1].split("/")[0].split(":")[0]
        else:
            origin_host = referer.split("://")[-1].split("/")[0].split(":")[0]

        # Check against allowed hosts
        is_allowed = any(
            origin_host == host or origin_host.endswith(f".{host}")
            for host in allowed_hosts
            if host != "*"
        )

        if not is_allowed:
            logger.warning(f"Origin '{origin_host}' not in ALLOWED_HOSTS")

        return is_allowed

    def _set_csrf_cookie(self, request: HttpRequest, response: HttpResponse) -> None:
        """Set or update CSRF token cookie in response.

        Args:
            request: Django HTTP request
            response: Django HTTP response
        """
        cookie_name = self.config.get("COOKIE_NAME", "csrftoken")

        # Check if cookie already exists
        if cookie_name in request.COOKIES:
            # Rotate token if configured
            if self.config.get("TOKEN_ROTATION", True):
                if self._should_rotate_token(request):
                    self._generate_new_token(request, response)
            return

        # Generate new token for first-time visitors
        self._generate_new_token(request, response)

    def _should_rotate_token(self, request: HttpRequest) -> bool:
        """Check if CSRF token should be rotated.

        Args:
            request: Django HTTP request

        Returns:
            bool: True if token should be rotated
        """
        # Rotate on authentication state changes
        if hasattr(request, "user"):
            # Check if user just logged in
            if request.path in ["/api/auth/login/", "/accounts/login/"]:
                return True

            # Check if user just logged out
            if request.path in ["/api/auth/logout/", "/accounts/logout/"]:
                return True

        return False

    def _generate_new_token(self, request: HttpRequest, response: HttpResponse) -> None:
        """Generate and set new CSRF token.

        Args:
            request: Django HTTP request
            response: Django HTTP response
        """
        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)

        # Set cookie
        cookie_name = self.config.get("COOKIE_NAME", "csrftoken")
        cookie_age = self.config.get("COOKIE_AGE", 31449600)
        cookie_secure = self.config.get("COOKIE_SECURE", not settings.DEBUG)
        cookie_httponly = self.config.get("COOKIE_HTTPONLY", False)
        cookie_samesite = self.config.get("COOKIE_SAMESITE", "Strict")

        response.set_cookie(
            cookie_name,
            token,
            max_age=cookie_age,
            secure=cookie_secure,
            httponly=cookie_httponly,
            samesite=cookie_samesite,
        )

        logger.debug(f"Generated new CSRF token for {request.path}")

    def _csrf_failure_response(
        self, request: HttpRequest, reason: str = "CSRF verification failed"
    ) -> HttpResponse:
        """Generate response for CSRF validation failure.

        Args:
            request: Django HTTP request
            reason: Failure reason for logging

        Returns:
            HttpResponse: 403 Forbidden response
        """
        logger.warning(f"CSRF validation failed for {request.method} {request.path}: {reason}")

        return JsonResponse(
            {
                "error": "CSRF verification failed",
                "detail": "Request blocked due to failed security checks",
            },
            status=403,
        )
