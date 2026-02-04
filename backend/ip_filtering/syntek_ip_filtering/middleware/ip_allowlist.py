"""IP allowlist/blocklist middleware for Django.

This middleware implements IP-based access control, allowing or denying
requests based on IP addresses. Supports CIDR notation and wildcards.

Useful for restricting access to admin areas, staging environments, or APIs.
"""

import logging
import ipaddress
from typing import Callable, List, Optional
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.core.cache import cache

logger = logging.getLogger(__name__)


class IPAllowlistMiddleware:
    """IP allowlist/blocklist middleware.

    Controls access based on client IP addresses. Supports:
    - Allowlist (whitelist) mode: Only specified IPs allowed
    - Blocklist (blacklist) mode: All IPs allowed except specified
    - CIDR notation (e.g., 192.168.1.0/24)
    - Individual IP addresses
    - Path-specific rules
    - Caching for performance

    Configuration (settings.py):
        SYNTEK_IP_FILTERING = {
            'MODE': 'allowlist',  # or 'blocklist'
            'ALLOWED_IPS': [
                '127.0.0.1',
                '192.168.1.0/24',
                '10.0.0.0/8',
            ],
            'BLOCKED_IPS': [
                '1.2.3.4',
                '5.6.7.0/24',
            ],
            'PROTECTED_PATHS': [
                '/admin/',
                '/api/admin/',
                '/internal/',
            ],
            'ENABLE_CACHING': True,
            'CACHE_TTL': 300,  # 5 minutes
            'RESPONSE_MESSAGE': 'Access denied',
            'RESPONSE_STATUS': 403,
            'LOG_BLOCKED': True,
        }

    Example:
        # In settings.py
        MIDDLEWARE = [
            ...
            'syntek_ip_filtering.middleware.IPAllowlistMiddleware',
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
        self._allowed_networks: Optional[List[ipaddress.IPv4Network]] = None
        self._blocked_networks: Optional[List[ipaddress.IPv4Network]] = None

    def _get_config(self) -> dict:
        """Get IP filtering configuration from settings.

        Returns:
            dict: Configuration dictionary
        """
        ip_config = getattr(settings, "SYNTEK_IP_FILTERING", {})

        # Default configuration
        defaults = {
            "MODE": "allowlist",
            "ALLOWED_IPS": ["127.0.0.1", "::1"],
            "BLOCKED_IPS": [],
            "PROTECTED_PATHS": ["/admin/", "/api/admin/"],
            "ENABLE_CACHING": True,
            "CACHE_TTL": 300,
            "RESPONSE_MESSAGE": "Access denied from your IP address",
            "RESPONSE_STATUS": 403,
            "LOG_BLOCKED": True,
            "ENABLED": True,
        }

        # Merge with user configuration
        defaults.update(ip_config)
        return defaults

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and enforce IP filtering.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse: Response, or 403 if IP is blocked
        """
        if not self.config.get("ENABLED", True):
            return self.get_response(request)

        # Check if path is protected
        if not self._is_protected_path(request.path):
            return self.get_response(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check if IP is allowed
        if not self._is_ip_allowed(client_ip):
            return self._access_denied_response(request, client_ip)

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
            # Take the first IP in the chain (original client)
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip.strip()

        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def _is_protected_path(self, path: str) -> bool:
        """Check if request path requires IP filtering.

        Args:
            path: Request path

        Returns:
            bool: True if path is protected
        """
        protected_paths = self.config.get("PROTECTED_PATHS", [])

        # If no protected paths specified, protect all paths
        if not protected_paths:
            return True

        return any(path.startswith(protected) for protected in protected_paths)

    def _is_ip_allowed(self, client_ip: str) -> bool:
        """Check if client IP is allowed access.

        Args:
            client_ip: Client IP address

        Returns:
            bool: True if IP is allowed
        """
        # Check cache first
        if self.config.get("ENABLE_CACHING", True):
            cache_key = f"ip_allowed:{client_ip}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Determine based on mode
        mode = self.config.get("MODE", "allowlist")

        if mode == "allowlist":
            result = self._is_ip_in_allowlist(client_ip)
        elif mode == "blocklist":
            result = not self._is_ip_in_blocklist(client_ip)
        else:
            logger.error(f"Invalid IP filtering mode: {mode}")
            result = False  # Fail closed

        # Cache result
        if self.config.get("ENABLE_CACHING", True):
            cache_ttl = self.config.get("CACHE_TTL", 300)
            cache.set(cache_key, result, cache_ttl)

        return result

    def _is_ip_in_allowlist(self, client_ip: str) -> bool:
        """Check if IP is in the allowlist.

        Args:
            client_ip: Client IP address

        Returns:
            bool: True if IP is allowed
        """
        allowed_ips = self.config.get("ALLOWED_IPS", [])

        # Parse client IP
        try:
            client_addr = ipaddress.ip_address(client_ip)
        except ValueError:
            logger.warning(f"Invalid client IP address: {client_ip}")
            return False

        # Build allowed networks cache
        if self._allowed_networks is None:
            self._allowed_networks = self._parse_ip_list(allowed_ips)

        # Check if IP matches any allowed network
        for network in self._allowed_networks:
            if client_addr in network:
                return True

        return False

    def _is_ip_in_blocklist(self, client_ip: str) -> bool:
        """Check if IP is in the blocklist.

        Args:
            client_ip: Client IP address

        Returns:
            bool: True if IP is blocked
        """
        blocked_ips = self.config.get("BLOCKED_IPS", [])

        # Parse client IP
        try:
            client_addr = ipaddress.ip_address(client_ip)
        except ValueError:
            logger.warning(f"Invalid client IP address: {client_ip}")
            return False

        # Build blocked networks cache
        if self._blocked_networks is None:
            self._blocked_networks = self._parse_ip_list(blocked_ips)

        # Check if IP matches any blocked network
        for network in self._blocked_networks:
            if client_addr in network:
                return True

        return False

    def _parse_ip_list(self, ip_list: List[str]) -> List[ipaddress.IPv4Network]:
        """Parse list of IPs/CIDR ranges into network objects.

        Args:
            ip_list: List of IP addresses or CIDR ranges

        Returns:
            List of IPv4Network objects
        """
        networks = []

        for ip_or_cidr in ip_list:
            try:
                # Try parsing as network (CIDR)
                if "/" in ip_or_cidr:
                    network = ipaddress.ip_network(ip_or_cidr, strict=False)
                else:
                    # Individual IP - create /32 network
                    network = ipaddress.ip_network(f"{ip_or_cidr}/32", strict=False)

                networks.append(network)

            except ValueError as e:
                logger.error(f"Invalid IP/CIDR '{ip_or_cidr}': {e}")
                continue

        return networks

    def _access_denied_response(self, request: HttpRequest, client_ip: str) -> HttpResponse:
        """Generate response for blocked IP.

        Args:
            request: Django HTTP request
            client_ip: Client IP address that was blocked

        Returns:
            HttpResponse: 403 Forbidden response
        """
        # Log blocked access
        if self.config.get("LOG_BLOCKED", True):
            logger.warning(f"Access denied for IP {client_ip} to {request.method} {request.path}")

        # Get response message
        message = self.config.get("RESPONSE_MESSAGE", "Access denied from your IP address")

        # Return forbidden response
        return HttpResponseForbidden(message)
