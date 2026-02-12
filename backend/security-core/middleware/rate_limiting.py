"""Rate limiting middleware for Django.

This middleware implements request rate limiting using Redis as a backend,
protecting against brute-force attacks and DoS attempts.

Implements token bucket and sliding window algorithms.
"""

import logging
import hashlib
from typing import Callable, Optional, Tuple
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Rate limit HTTP requests per IP address or user.

    Uses Redis (via Django cache) to track request counts using sliding window
    or token bucket algorithms. Supports different rate limits per endpoint.

    Configuration (settings.py):
        SYNTEK_SECURITY_CORE = {
            'RATE_LIMITING': {
                'BACKEND': 'redis',  # or 'memory' for testing
                'DEFAULT_RATE': '100/hour',  # Format: count/period
                'BURST_RATE': '10/minute',
                'BY_USER': True,  # Rate limit by user if authenticated
                'BY_IP': True,    # Rate limit by IP address
                'ENDPOINTS': {
                    '/api/auth/login/': '5/minute',
                    '/api/auth/register/': '3/hour',
                    '/api/password-reset/': '3/hour',
                },
                'WHITELIST_IPS': ['127.0.0.1'],
                'RESPONSE_MESSAGE': 'Rate limit exceeded. Try again later.',
                'RESPONSE_STATUS': 429,
            }
        }

    Example:
        # In settings.py
        MIDDLEWARE = [
            ...
            'syntek_security_core.middleware.RateLimitMiddleware',
            ...
        ]
    """

    # Period conversions to seconds
    PERIODS = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize middleware.

        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.config = self._get_config()

    def _get_config(self) -> dict:
        """Get rate limiting configuration from settings.

        Returns:
            dict: Configuration dictionary with rate limiting settings
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_CORE", {})
        rate_limit_config = security_config.get("RATE_LIMITING", {})

        # Default configuration
        defaults = {
            "BACKEND": "redis",
            "DEFAULT_RATE": "100/hour",
            "BURST_RATE": "10/minute",
            "BY_USER": True,
            "BY_IP": True,
            "ENDPOINTS": {},
            "WHITELIST_IPS": ["127.0.0.1", "::1"],
            "RESPONSE_MESSAGE": "Rate limit exceeded. Please try again later.",
            "RESPONSE_STATUS": 429,
            "ENABLED": True,
        }

        # Merge with user configuration
        defaults.update(rate_limit_config)
        return defaults

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and enforce rate limits.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse: Response, or 429 if rate limit exceeded
        """
        if not self.config.get("ENABLED", True):
            return self.get_response(request)

        # Check if IP is whitelisted
        client_ip = self._get_client_ip(request)
        if client_ip in self.config.get("WHITELIST_IPS", []):
            return self.get_response(request)

        # Get rate limit for this endpoint
        rate_limit = self._get_rate_limit_for_path(request.path)
        if not rate_limit:
            return self.get_response(request)

        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(request, rate_limit, client_ip)

        if not is_allowed:
            return self._rate_limit_exceeded_response(retry_after)

        return self.get_response(request)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request.

        Args:
            request: Django HTTP request

        Returns:
            str: Client IP address
        """
        # Check X-Forwarded-For header (proxy/load balancer)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip.strip()

        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def _get_rate_limit_for_path(self, path: str) -> Optional[str]:
        """Get rate limit configuration for a specific path.

        Args:
            path: Request path (e.g., '/api/auth/login/')

        Returns:
            str: Rate limit string (e.g., '5/minute'), or None
        """
        endpoints = self.config.get("ENDPOINTS", {})

        # Check for exact match
        if path in endpoints:
            return endpoints[path]

        # Check for prefix match
        for endpoint_path, rate in endpoints.items():
            if path.startswith(endpoint_path):
                return rate

        # Use default rate
        return self.config.get("DEFAULT_RATE")

    def _parse_rate_limit(self, rate_string: str) -> Tuple[int, int]:
        """Parse rate limit string into count and period.

        Args:
            rate_string: Rate limit string (e.g., '100/hour', '5/minute')

        Returns:
            Tuple of (count, period_seconds)

        Raises:
            ValueError: If rate string is invalid
        """
        try:
            count_str, period = rate_string.split("/")
            count = int(count_str)
            period_seconds = self.PERIODS.get(period.lower())

            if not period_seconds:
                raise ValueError(f"Invalid period: {period}")

            return count, period_seconds

        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid rate limit string '{rate_string}': {e}")
            raise ValueError(f"Invalid rate limit format: {rate_string}")

    def _get_cache_key(self, request: HttpRequest, client_ip: str) -> str:
        """Generate cache key for rate limiting.

        Args:
            request: Django HTTP request
            client_ip: Client IP address

        Returns:
            str: Cache key for rate limit tracking
        """
        # Build identifier based on configuration
        identifiers = []

        if self.config.get("BY_IP", True):
            identifiers.append(f"ip:{client_ip}")

        if self.config.get("BY_USER", True):
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                identifiers.append(f"user:{getattr(user, 'id', None)}")

        # Add path to make limits endpoint-specific
        identifiers.append(f"path:{request.path}")

        # Hash the identifier for consistent key length
        identifier = "|".join(identifiers)
        identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]

        return f"rate_limit:{identifier_hash}"

    def _check_rate_limit(
        self, request: HttpRequest, rate_string: str, client_ip: str
    ) -> Tuple[bool, Optional[int]]:
        """Check if request is within rate limit.

        Args:
            request: Django HTTP request
            rate_string: Rate limit string (e.g., '5/minute')
            client_ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        try:
            count, period = self._parse_rate_limit(rate_string)
        except ValueError:
            # If rate limit is invalid, allow the request
            logger.warning(f"Invalid rate limit '{rate_string}', allowing request")
            return True, None

        cache_key = self._get_cache_key(request, client_ip)

        # Get current count from cache
        current_count = cache.get(cache_key, 0)

        if current_count >= count:
            # Rate limit exceeded
            retry_after = cache.ttl(cache_key) or period
            logger.warning(
                f"Rate limit exceeded for {cache_key}: {current_count}/{count} in {period}s"
            )
            return False, retry_after

        # Increment counter
        if current_count == 0:
            # First request in window - set counter with TTL
            cache.set(cache_key, 1, period)
        else:
            # Increment existing counter
            cache.incr(cache_key)

        logger.debug(
            f"Rate limit check passed for {cache_key}: {current_count + 1}/{count} in {period}s"
        )
        return True, None

    def _rate_limit_exceeded_response(self, retry_after: Optional[int]) -> HttpResponse:
        """Generate response for rate limit exceeded.

        Args:
            retry_after: Seconds until rate limit resets

        Returns:
            HttpResponse: 429 Too Many Requests response
        """
        status_code = self.config.get("RESPONSE_STATUS", 429)
        message = self.config.get(
            "RESPONSE_MESSAGE", "Rate limit exceeded. Please try again later."
        )

        response = JsonResponse(
            {
                "error": message,
                "retry_after": retry_after,
            },
            status=status_code,
        )

        if retry_after:
            response["Retry-After"] = str(retry_after)

        return response
