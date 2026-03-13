# Root conftest — presence here ensures pytest adds the repo root to sys.path,
# making the `tests` package importable across all test invocations.
#
# Django is configured here once, before any subdirectory conftest can claim
# ``settings.configure()``.  Without this, ``tests/graphql_crypto/conftest.py``
# wins the race and omits ``syntek_auth`` from INSTALLED_APPS, causing a
# ``RuntimeError`` when ``test_us009_user_model.py`` imports Django models.

from __future__ import annotations

import django
from django.conf import settings


def pytest_configure(config: object) -> None:
    """Unified Django configuration for the full syntek-modules test suite.

    Includes every Django app needed across all test packages so that
    subdirectory conftest files (which all guard with ``if not
    settings.configured:``) inherit this shared baseline rather than racing to
    call ``settings.configure()`` themselves.
    """
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
                "syntek_graphql_crypto",
            ],
            AUTH_USER_MODEL="syntek_auth.User",
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
            SYNTEK_AUTH={
                "FIELD_HMAC_KEY": "a" * 64,  # 64-char test key — never use in production
                "FIELD_KEY": "b" * 32,  # 32-char test key (32 bytes UTF-8 = AES-256) — never use in production
                # Minimal Argon2id params for test speed — never use in production.
                # Production defaults: m=65536, t=3, p=4 (deliberately slow).
                "ARGON2ID_TIME_COST": 1,
                "ARGON2ID_MEMORY_COST": 8,
                "ARGON2ID_PARALLELISM": 1,
            },
            SILENCED_SYSTEM_CHECKS=["auth.E003"],
        )
        django.setup()
