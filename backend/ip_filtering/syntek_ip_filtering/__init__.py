"""IP filtering module for Django.

Provides IP allowlist/blocklist middleware for controlling access based on
client IP addresses. Supports CIDR notation and path-specific rules.
"""

from .middleware.ip_allowlist import IPAllowlistMiddleware

__all__ = ["IPAllowlistMiddleware"]
__version__ = "0.1.0"
