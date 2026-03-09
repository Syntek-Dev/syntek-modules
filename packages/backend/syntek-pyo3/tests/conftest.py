"""pytest configuration for syntek-pyo3 Django EncryptedField tests.

Configures minimal Django settings directly so these tests can be run from
the repo root without needing a `DJANGO_SETTINGS_MODULE` path on `sys.path`.
No database fixtures are needed — all tests exercise field-level logic only.
"""

from __future__ import annotations

import django
from django.conf import settings


def pytest_configure(config: object) -> None:
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
        )
        django.setup()
