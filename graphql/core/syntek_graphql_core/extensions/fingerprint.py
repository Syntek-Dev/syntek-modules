"""Session fingerprint extension for GraphQL operations.

Captures device and browser information on each request to detect session hijacking,
suspicious activity, and unauthorised access attempts.

Features:
- Device fingerprinting (User-Agent, Accept-Language, Screen resolution)
- IP address tracking
- Geolocation capture (optional)
- Session consistency validation
- Anomaly detection

Configuration:
    GRAPHQL_FINGERPRINT_ENABLED: Enable/disable fingerprinting (default: True)
    GRAPHQL_FINGERPRINT_STRICT: Strict mode (block on mismatch, default: False)
    GRAPHQL_FINGERPRINT_GEOLOCATION: Enable geolocation tracking (default: False)
"""

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.cache import cache
from strawberry.extensions import SchemaExtension

from syntek_graphql_core.errors import AuthenticationError, ErrorCode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class SessionFingerprintExtension(SchemaExtension):
    """Capture and validate session fingerprints for security monitoring.

    Generates a fingerprint from device characteristics and validates it against
    the stored fingerprint for the session. Detects session hijacking by identifying
    when the same session is used from different devices.

    Fingerprint components:
    - User-Agent (browser and OS information)
    - Accept-Language (browser language preferences)
    - IP address (with proxy detection)
    - Screen resolution (if provided by client)
    - Platform information

    The extension operates in two modes:
    - Logging mode (default): Logs mismatches but allows request
    - Strict mode: Blocks requests on fingerprint mismatch

    Configuration:
        GRAPHQL_FINGERPRINT_ENABLED: Enable fingerprinting (default: True)
        GRAPHQL_FINGERPRINT_STRICT: Block on mismatch (default: False)
        GRAPHQL_FINGERPRINT_GEOLOCATION: Track geolocation (default: False)
        GRAPHQL_FINGERPRINT_CACHE_TTL: Cache TTL in seconds (default: 86400)

    Attributes:
        enabled: Whether fingerprinting is enabled
        strict_mode: Whether to block on fingerprint mismatch
        enable_geolocation: Whether to track geolocation
        cache_ttl: Cache time-to-live for fingerprints
    """

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with fingerprint configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load configuration
        self.enabled = getattr(settings, "GRAPHQL_FINGERPRINT_ENABLED", True)
        self.strict_mode = getattr(settings, "GRAPHQL_FINGERPRINT_STRICT", False)
        self.enable_geolocation = getattr(settings, "GRAPHQL_FINGERPRINT_GEOLOCATION", False)
        self.cache_ttl = getattr(settings, "GRAPHQL_FINGERPRINT_CACHE_TTL", 86400)  # 24 hours

    def on_execute(self) -> "Iterator[None]":
        """Execute with session fingerprinting.

        Captures device fingerprint and validates against stored fingerprint.

        Yields:
            None after validation completes.

        Raises:
            AuthenticationError: If strict mode enabled and fingerprint mismatch.
        """
        if not self.enabled:
            yield
            return

        # Only fingerprint authenticated requests
        user = self._get_authenticated_user()

        if not user:
            yield
            return

        # Generate fingerprint
        fingerprint = self._generate_fingerprint()

        # Get stored fingerprint for user
        stored_fingerprint = self._get_stored_fingerprint(user.id)

        if stored_fingerprint:
            # Validate fingerprint
            if fingerprint != stored_fingerprint:
                logger.warning(
                    f"Session fingerprint mismatch for user {user.id}",
                    extra={
                        "user_id": user.id,
                        "current_fingerprint": fingerprint,
                        "stored_fingerprint": stored_fingerprint,
                    },
                )

                if self.strict_mode:
                    raise AuthenticationError(
                        code=ErrorCode.TOKEN_INVALID,
                        message="Session security validation failed. Please log in again.",
                        extensions={"reason": "fingerprint_mismatch"},
                    )
        else:
            # First request, store fingerprint
            self._store_fingerprint(user.id, fingerprint)
            logger.info(
                f"Session fingerprint stored for user {user.id}",
                extra={"user_id": user.id, "fingerprint": fingerprint},
            )

        yield

    def _get_authenticated_user(self) -> Any | None:
        """Get authenticated user from request.

        Returns:
            User object or None if not authenticated.
        """
        context = self.execution_context.context

        if isinstance(context, dict):
            request = context.get("request")
        else:
            request = getattr(context, "request", None)

        if not request:
            return None

        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            return user

        return None

    def _generate_fingerprint(self) -> str:
        """Generate session fingerprint from device characteristics.

        Returns:
            SHA256 hash of fingerprint components.
        """
        context = self.execution_context.context

        if isinstance(context, dict):
            request = context.get("request")
        else:
            request = getattr(context, "request", None)

        if not request:
            return "unknown"

        # Collect fingerprint components
        components = []

        # User-Agent
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        components.append(user_agent)

        # Accept-Language
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        components.append(accept_language)

        # Accept-Encoding
        accept_encoding = request.META.get("HTTP_ACCEPT_ENCODING", "")
        components.append(accept_encoding)

        # IP address (coarse-grained to /24 network for privacy)
        ip_address = self._get_client_ip(request)
        ip_network = self._get_ip_network(ip_address)
        components.append(ip_network)

        # Optional: Screen resolution from custom header
        screen_resolution = request.META.get("HTTP_X_SCREEN_RESOLUTION", "")
        if screen_resolution:
            components.append(screen_resolution)

        # Optional: Platform from custom header
        platform = request.META.get("HTTP_X_PLATFORM", "")
        if platform:
            components.append(platform)

        # Generate hash
        fingerprint_data = "|".join(components)
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()

        return fingerprint_hash

    def _get_client_ip(self, request: Any) -> str:
        """Extract client IP address from request.

        Args:
            request: Django HttpRequest object.

        Returns:
            Client IP address.
        """
        # Try syntek-security-core's get_client_ip if available
        try:
            from syntek_security_core.utils.request import get_client_ip  # type: ignore[import]

            return get_client_ip(request, anonymise=False)
        except (ImportError, AttributeError):
            pass

        # Fallback to manual extraction
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR", "unknown")

    def _get_ip_network(self, ip_address: str) -> str:
        """Get IP network (coarse-grained for privacy).

        Converts IP to /24 network to allow some variation while detecting
        major changes (e.g., different city/country).

        Args:
            ip_address: IP address.

        Returns:
            IP network string (e.g., "192.168.1.0/24").
        """
        if ":" in ip_address:
            # IPv6 - use /64 prefix
            parts = ip_address.split(":")
            return ":".join(parts[:4]) + "::/64"

        # IPv4 - use /24 prefix
        parts = ip_address.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + ".0/24"

        return ip_address

    def _get_stored_fingerprint(self, user_id: Any) -> str | None:
        """Get stored fingerprint for user from cache.

        Args:
            user_id: User ID.

        Returns:
            Stored fingerprint or None if not found.
        """
        cache_key = f"session_fingerprint:{user_id}"
        return cache.get(cache_key)

    def _store_fingerprint(self, user_id: Any, fingerprint: str) -> None:
        """Store fingerprint for user in cache.

        Args:
            user_id: User ID.
            fingerprint: Fingerprint hash.
        """
        cache_key = f"session_fingerprint:{user_id}"
        cache.set(cache_key, fingerprint, self.cache_ttl)
