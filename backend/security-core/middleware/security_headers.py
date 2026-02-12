"""Security headers middleware for Django.

This middleware adds comprehensive HTTP security headers to all responses,
protecting against XSS, clickjacking, MIME-sniffing, and other attacks.

Implements OWASP recommendations and security best practices.
"""

import logging
from typing import Callable, Optional
from django.conf import settings
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to HTTP responses.

    Adds the following headers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY/SAMEORIGIN
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin-Embedder-Policy (COEP)
    - Cross-Origin-Opener-Policy (COOP)
    - Cross-Origin-Resource-Policy (CORP)

    Configuration (settings.py):
        SYNTEK_SECURITY_CORE = {
            'HEADERS': {
                'ENABLE_HSTS': True,
                'HSTS_MAX_AGE': 31536000,  # 1 year
                'HSTS_INCLUDE_SUBDOMAINS': True,
                'HSTS_PRELOAD': True,
                'X_FRAME_OPTIONS': 'DENY',  # or 'SAMEORIGIN'
                'CSP': "default-src 'self'; script-src 'self' 'unsafe-inline'",
                'REFERRER_POLICY': 'strict-origin-when-cross-origin',
                'PERMISSIONS_POLICY': 'geolocation=(), microphone=(), camera=()',
                'ENABLE_COEP': True,
                'ENABLE_COOP': True,
                'ENABLE_CORP': True,
            }
        }
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize middleware.

        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.config = self._get_config()

    def _get_config(self) -> dict:
        """Get security headers configuration from settings.

        Returns:
            dict: Configuration dictionary with security header settings
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_CORE", {})
        headers_config = security_config.get("HEADERS", {})

        # Default configuration
        defaults = {
            "ENABLE_HSTS": True,
            "HSTS_MAX_AGE": 31536000,  # 1 year in seconds
            "HSTS_INCLUDE_SUBDOMAINS": True,
            "HSTS_PRELOAD": True,
            "X_FRAME_OPTIONS": "DENY",
            "CSP": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
            "REFERRER_POLICY": "strict-origin-when-cross-origin",
            "PERMISSIONS_POLICY": (
                "geolocation=(), microphone=(), camera=(), payment=(), "
                "usb=(), magnetometer=(), gyroscope=(), speaker=()"
            ),
            "ENABLE_COEP": False,  # Can break some integrations
            "ENABLE_COOP": True,
            "ENABLE_CORP": True,
        }

        # Merge with user configuration
        defaults.update(headers_config)
        return defaults

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and add security headers to response.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse: Response with security headers added
        """
        response = self.get_response(request)
        self._add_security_headers(response, request)
        return response

    def _add_security_headers(self, response: HttpResponse, request: HttpRequest) -> None:
        """Add all security headers to the response.

        Args:
            response: Django HTTP response to add headers to
            request: Django HTTP request (for context)
        """
        # X-Content-Type-Options: Prevent MIME-sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevent clickjacking
        x_frame_options = self.config.get("X_FRAME_OPTIONS", "DENY")
        response["X-Frame-Options"] = x_frame_options

        # X-XSS-Protection: Enable browser XSS filter (legacy browsers)
        response["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS): Force HTTPS
        if self.config.get("ENABLE_HSTS", True) and request.is_secure():
            hsts_value = self._build_hsts_header()
            if hsts_value:
                response["Strict-Transport-Security"] = hsts_value

        # Content-Security-Policy: Control resource loading
        csp = self.config.get("CSP")
        if csp:
            response["Content-Security-Policy"] = csp

        # Referrer-Policy: Control referrer information
        referrer_policy = self.config.get("REFERRER_POLICY")
        if referrer_policy:
            response["Referrer-Policy"] = referrer_policy

        # Permissions-Policy: Control browser features
        permissions_policy = self.config.get("PERMISSIONS_POLICY")
        if permissions_policy:
            response["Permissions-Policy"] = permissions_policy

        # Cross-Origin-Embedder-Policy: Isolate from cross-origin
        if self.config.get("ENABLE_COEP", False):
            response["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cross-Origin-Opener-Policy: Isolate browsing context
        if self.config.get("ENABLE_COOP", True):
            response["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cross-Origin-Resource-Policy: Control resource sharing
        if self.config.get("ENABLE_CORP", True):
            response["Cross-Origin-Resource-Policy"] = "same-origin"

        logger.debug(f"Added security headers to response for {request.path}")

    def _build_hsts_header(self) -> Optional[str]:
        """Build the HSTS header value.

        Returns:
            str: HSTS header value, or None if HSTS is disabled
        """
        if not self.config.get("ENABLE_HSTS", True):
            return None

        max_age = self.config.get("HSTS_MAX_AGE", 31536000)
        parts = [f"max-age={max_age}"]

        if self.config.get("HSTS_INCLUDE_SUBDOMAINS", True):
            parts.append("includeSubDomains")

        if self.config.get("HSTS_PRELOAD", True):
            parts.append("preload")

        return "; ".join(parts)
