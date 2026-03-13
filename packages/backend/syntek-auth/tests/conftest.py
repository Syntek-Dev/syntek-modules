"""pytest configuration for syntek-auth unit tests — US009 / US076.

Configures minimal Django settings (in-memory SQLite) so that all tests in
this package can run from the repo root without a ``DJANGO_SETTINGS_MODULE``
on ``sys.path``.

``syntek_auth`` is included in ``INSTALLED_APPS`` so that the ``User`` model
defined in ``syntek_auth.models`` is registered in Django's app registry.
``AUTH_USER_MODEL`` is set to ``'syntek_auth.User'`` so that
``get_user_model()`` returns the concrete Syntek user class, as required by
the US009 user-model acceptance criteria.
"""

from __future__ import annotations

import django
from django.conf import settings


def pytest_configure(config: object) -> None:
    """Configure minimal Django for syntek-auth unit tests."""
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
                "syntek_auth",
            ],
            AUTH_USER_MODEL="syntek_auth.User",
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
            # FIELD_HMAC_KEY is the minimum required key — all user creation
            # (manager and factory) needs it to compute lookup tokens.
            # Individual tests may monkeypatch other SYNTEK_AUTH keys as needed.
            SYNTEK_AUTH={
                "FIELD_HMAC_KEY": "a"
                * 64,  # 64-char test key — never use in production
                "FIELD_KEY": "b"
                * 32,  # 32-char test key (32 bytes UTF-8 = AES-256) — never use in production
            },
            # auth.E003 requires USERNAME_FIELD unique=True at the DB level.
            # Email uniqueness is enforced via email_token instead. See ENCRYPTION-GUIDE.md.
            SILENCED_SYSTEM_CHECKS=["auth.E003"],
        )
        django.setup()
