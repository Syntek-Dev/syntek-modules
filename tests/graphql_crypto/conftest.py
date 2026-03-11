"""pytest configuration for graphql_crypto integration tests.

Configures minimal Django settings with an in-memory SQLite database before
test collection so that module-level Strawberry type definitions in
``test_integration.py`` can import ``syntek_graphql_crypto`` safely.
"""

from __future__ import annotations

import os
from base64 import b64encode

import django
from django.conf import settings

# ---------------------------------------------------------------------------
# Non-secret 32-byte test key — used for all SYNTEK_FIELD_KEY_* env vars.
# ---------------------------------------------------------------------------
_TEST_KEY_BYTES: bytes = bytes(range(32))
_TEST_KEY: str = b64encode(_TEST_KEY_BYTES).decode()


def pytest_configure(config: object) -> None:
    """Configure minimal Django for graphql_crypto integration tests."""
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_EMAIL", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_FIRST_NAME", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_LAST_NAME", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_PHONE", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_ADDRESS_LINE_1", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_ADDRESS_LINE_2", _TEST_KEY)
    os.environ.setdefault("SYNTEK_FIELD_KEY_USER_POSTCODE", _TEST_KEY)

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
                "syntek_graphql_crypto",
            ],
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
        )
        django.setup()
