"""pytest configuration for syntek-security unit tests — US076.

Configures minimal Django settings (in-memory SQLite) so that all tests can
run from the repo root without a ``DJANGO_SETTINGS_MODULE`` on ``sys.path``.
"""

from __future__ import annotations

import django
from django.conf import settings


def pytest_configure(config: object) -> None:
    """Configure minimal Django for syntek-security unit tests."""
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
            # Proxy settings are intentionally absent here — tests verify that
            # apply_proxy_settings() injects them.
        )
        django.setup()
