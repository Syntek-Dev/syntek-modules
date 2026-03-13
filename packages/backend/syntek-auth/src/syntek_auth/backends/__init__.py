"""Public backend exports for ``syntek-auth``.

Re-exports ``SyntekAuthBackend`` so that consumers can reference it as
``syntek_auth.backends.SyntekAuthBackend`` in Django's
``AUTHENTICATION_BACKENDS`` setting.
"""

from __future__ import annotations

from syntek_auth.backends.allowlist import (
    BUILTIN_ALLOWED_PROVIDERS,
    MFA_GATED_PROVIDERS,
    is_mfa_gated_provider,
    validate_oauth_providers,
)
from syntek_auth.backends.auth_backend import SyntekAuthBackend

__all__ = [
    "BUILTIN_ALLOWED_PROVIDERS",
    "MFA_GATED_PROVIDERS",
    "SyntekAuthBackend",
    "is_mfa_gated_provider",
    "validate_oauth_providers",
]
