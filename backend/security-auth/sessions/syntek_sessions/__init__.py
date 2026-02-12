"""Syntek Sessions Module.

Provides session management functionality including JWT token storage,
refresh token rotation, device fingerprinting, and session activity tracking.

This module is part of the syntek-security-auth bundle and implements
secure session management patterns following OWASP, NIST, and security best practices.
"""

__version__ = "1.0.0"

default_app_config = "syntek_sessions.apps.SyntekSessionsConfig"
