"""Syntek JWT Module.

Provides JWT token management with refresh token rotation and replay detection.

This module is part of the syntek-security-auth bundle and implements
secure JWT patterns following OWASP and security best practices.
"""

__version__ = "1.0.0"

default_app_config = "syntek_jwt.apps.SyntekJwtConfig"
