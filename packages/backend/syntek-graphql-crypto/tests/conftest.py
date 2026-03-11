"""pytest configuration for syntek-graphql-crypto Django / Strawberry unit tests.

Configures minimal Django settings with an in-memory SQLite database so that
all tests in this package can be run from the repo root without needing a
``DJANGO_SETTINGS_MODULE`` on ``sys.path``.

The conftest also provides shared fixtures used across the directive, write-path,
read-path, error-handling, and auth-guard test modules.
"""

from __future__ import annotations

import os
from base64 import b64encode
from unittest.mock import MagicMock

import django
import pytest
from django.conf import settings

# ---------------------------------------------------------------------------
# Non-secret 32-byte test key (base64-encoded) — used for all SYNTEK_FIELD_KEY_*
# environment variables in tests.  Never use a predictable key in production.
# ---------------------------------------------------------------------------
_TEST_KEY_BYTES: bytes = bytes(range(32))  # 32 bytes: 0x00 … 0x1f
_TEST_KEY: str = b64encode(_TEST_KEY_BYTES).decode()


def pytest_configure(config: object) -> None:
    """Configure minimal Django for syntek-graphql-crypto unit tests."""
    # Set encryption key env vars before Django starts so any AppConfig.ready()
    # validation passes.
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def authenticated_info() -> MagicMock:
    """A mock Strawberry ``info`` object representing an authenticated request.

    The middleware checks ``info.context.user.is_authenticated`` before
    performing any decryption (AC10).
    """
    info = MagicMock()
    info.context.user.is_authenticated = True
    return info


@pytest.fixture
def unauthenticated_info() -> MagicMock:
    """A mock Strawberry ``info`` object representing an unauthenticated request.

    Used by auth-guard tests to verify that encrypted fields are nulled and an
    auth error is appended to the GraphQL ``errors`` array (AC10).
    """
    info = MagicMock()
    info.context.user.is_authenticated = False
    return info


@pytest.fixture
def test_schema():  # type: ignore[return]
    """A minimal Strawberry schema with ``@encrypted`` fields for unit tests.

    This fixture is intentionally left as a deferred import so that the schema
    is only constructed once ``syntek_graphql_crypto`` is importable (i.e. in
    the green phase).  During the red phase the import raises
    ``ModuleNotFoundError``, which surfaces as a collection error — the
    expected behaviour for TDD red phase.
    """
    import strawberry
    from syntek_graphql_crypto.directives import Encrypted
    from syntek_graphql_crypto.middleware import EncryptionMiddleware

    @strawberry.type
    class UserType:
        email: str = strawberry.field(
            directives=[Encrypted()],
            resolver=lambda: "FAKE_CIPHERTEXT_email",
        )
        first_name: str = strawberry.field(
            directives=[Encrypted(batch="profile")],
            resolver=lambda: "FAKE_CIPHERTEXT_first_name",
        )
        last_name: str = strawberry.field(
            directives=[Encrypted(batch="profile")],
            resolver=lambda: "FAKE_CIPHERTEXT_last_name",
        )
        display_name: str = strawberry.field(
            resolver=lambda: "Alice",
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType()

    return strawberry.Schema(
        query=Query,
        extensions=[EncryptionMiddleware],
        types=[UserType],
    )
