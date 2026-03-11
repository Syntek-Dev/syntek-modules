"""Proxy trust Django settings injection — US076.

When ``syntek-security`` is installed and a reverse proxy is in use the module
must configure three Django settings so the application correctly trusts TLS
termination performed by Nginx:

- ``SECURE_PROXY_SSL_HEADER`` — tuple telling Django that the ``X-Forwarded-Proto``
  header value ``https`` means the connection is secure.
- ``USE_X_FORWARDED_HOST`` — instructs Django to honour the ``X-Forwarded-Host``
  header set by the proxy.
- ``SECURE_SSL_REDIRECT`` — redirects any HTTP request to HTTPS (the proxy
  terminates TLS so Django itself must not re-terminate).

These defaults are applied in ``SyntekSecurityConfig.ready()`` only when they
have not already been overridden by the consuming project's ``settings.py``.
"""

from __future__ import annotations

# Sentinel used by apply_proxy_settings to identify unset defaults.
_UNSET = object()

# The canonical value for SECURE_PROXY_SSL_HEADER in the Syntek proxy stack.
PROXY_SSL_HEADER: tuple[str, str] = ("HTTP_X_FORWARDED_PROTO", "https")


def apply_proxy_settings() -> None:
    """Apply proxy-trust Django settings if they have not been set by the project.

    Injects three settings onto ``django.conf.settings`` when they are absent
    from the project's own settings (i.e. not overridden in the consumer's
    ``settings.py`` or test configuration):

    - ``SECURE_PROXY_SSL_HEADER`` — set to :data:`PROXY_SSL_HEADER`.
    - ``USE_X_FORWARDED_HOST`` — set to ``True``.
    - ``SECURE_SSL_REDIRECT`` — set to ``True``.

    Detection uses ``settings._wrapped.__dict__`` rather than ``hasattr`` so
    that Django's global-settings defaults (which are always accessible via
    ``hasattr``) do not suppress the Syntek proxy defaults.  Only settings
    explicitly assigned by the consuming project are treated as "already set".

    Must be called from ``SyntekSecurityConfig.ready()``.
    """
    from django.conf import settings

    configured: dict = settings._wrapped.__dict__  # type: ignore[union-attr]

    if "SECURE_PROXY_SSL_HEADER" not in configured:
        settings.SECURE_PROXY_SSL_HEADER = PROXY_SSL_HEADER  # type: ignore[misc]

    if "USE_X_FORWARDED_HOST" not in configured:
        settings.USE_X_FORWARDED_HOST = True  # type: ignore[misc]

    if "SECURE_SSL_REDIRECT" not in configured:
        settings.SECURE_SSL_REDIRECT = True  # type: ignore[misc]
