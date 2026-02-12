"""IP filtering middleware package."""

from .ip_allowlist import IPAllowlistMiddleware

__all__ = ["IPAllowlistMiddleware"]
