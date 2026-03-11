"""US008 — Red phase: integration tests for ``syntek-graphql-crypto``.

These tests exercise the full write→DB→read cycle through a Strawberry schema
with ``EncryptionMiddleware`` attached.  They verify that:

1. A write mutation stores ciphertext in the DB; a subsequent query decrypts
   it and returns plaintext to the frontend.
2. Batch-group fields are stored individually as ciphertext and returned as
   plaintext.
3. A tampered DB value causes the affected field to be ``null`` with a
   structured error, while other fields remain intact.
4. An unauthenticated read returns ``null`` for all encrypted fields with an
   authorisation error in the response.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

These tests are marked ``integration`` because they exercise the full middleware
pipeline including real ``syntek_pyo3`` calls (after ``maturin develop``).
Where the native extension is unavailable, ``syntek_pyo3`` is mocked.

Run with:
    pytest tests/graphql_crypto/test_integration.py -v

AC coverage:
    AC1, AC4  — individual field write→read roundtrip
    AC2, AC5  — batch field write→read roundtrip
    AC7       — tampered value → null field + error, rest intact
    AC10      — unauthenticated read → null + auth error
"""

from __future__ import annotations

import os
from base64 import b64encode
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Test key (non-secret — tests only)
# ---------------------------------------------------------------------------

_TEST_KEY_BYTES: bytes = bytes(range(32))
_TEST_KEY: str = b64encode(_TEST_KEY_BYTES).decode()

# Ensure env vars are set before schema construction.
os.environ.setdefault("SYNTEK_FIELD_KEY_USER_EMAIL", _TEST_KEY)
os.environ.setdefault("SYNTEK_FIELD_KEY_USER_FIRST_NAME", _TEST_KEY)
os.environ.setdefault("SYNTEK_FIELD_KEY_USER_LAST_NAME", _TEST_KEY)
os.environ.setdefault("SYNTEK_FIELD_KEY_USER_PHONE", _TEST_KEY)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _django_setup():
    """Minimal Django configuration for integration tests.

    Sets up an in-memory SQLite database so that ORM calls in the schema
    resolvers can execute without a real PostgreSQL instance.
    """
    import django  # noqa: PLC0415
    from django.conf import settings  # noqa: PLC0415

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


@pytest.fixture()
def _schema(_django_setup):
    """A Strawberry schema with ``EncryptionMiddleware`` and a simple in-memory
    ``UserStore`` acting as the "database" for integration tests.
    """
    import strawberry  # noqa: PLC0415

    from syntek_graphql_crypto.directives import Encrypted  # noqa: PLC0415
    from syntek_graphql_crypto.middleware import EncryptionMiddleware  # noqa: PLC0415

    # In-memory store to simulate DB rows.
    store: dict[str, dict[str, str | None]] = {
        "1": {"email": None, "first_name": None, "last_name": None}
    }

    @strawberry.input
    class UpdateUserInput:
        email: str = strawberry.field(directives=[Encrypted()])
        first_name: str = strawberry.field(directives=[Encrypted(batch="profile")])
        last_name: str = strawberry.field(directives=[Encrypted(batch="profile")])

    @strawberry.type
    class UserType:
        email: str | None
        first_name: str | None
        last_name: str | None
        display_name: str

    @strawberry.type
    class MutationType:
        @strawberry.mutation
        def update_user(self, input: UpdateUserInput) -> UserType:
            # Resolver receives ciphertext from middleware — stores in DB.
            store["1"]["email"] = input.email
            store["1"]["first_name"] = input.first_name
            store["1"]["last_name"] = input.last_name
            return UserType(
                email=store["1"]["email"],
                first_name=store["1"]["first_name"],
                last_name=store["1"]["last_name"],
                display_name="Alice Smith",
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(
                email=store["1"]["email"],
                first_name=store["1"]["first_name"],
                last_name=store["1"]["last_name"],
                display_name="Alice Smith",
            )

    return (
        strawberry.Schema(
            query=Query,
            mutation=MutationType,
            extensions=[EncryptionMiddleware],
        ),
        store,
    )


# ---------------------------------------------------------------------------
# AC1 + AC4: Individual field — write stores ciphertext, read returns plaintext
# ---------------------------------------------------------------------------


class TestIndividualFieldRoundtrip:
    """AC1 + AC4: Write mutation → DB stores ciphertext → query returns plaintext."""

    def test_individual_field_write_stores_ciphertext_read_returns_plaintext(
        self,
        _schema,
    ) -> None:
        """After a write mutation the DB must contain a ciphertext string (not
        ``"alice@example.com"``), and a subsequent query must return the original
        plaintext to the frontend (AC1 + AC4).
        """
        schema, store = _schema

        authenticated_context = MagicMock()
        authenticated_context.user.is_authenticated = True

        # Execute the write mutation.
        write_result = schema.execute_sync(
            """
            mutation {
                updateUser(input: {
                    email: "alice@example.com",
                    firstName: "Alice",
                    lastName: "Smith"
                }) {
                    email
                    firstName
                    lastName
                    displayName
                }
            }
            """,
            context_value=authenticated_context,
        )

        assert not write_result.errors, (
            f"Write mutation must succeed: {write_result.errors}"
        )

        # Verify the DB contains ciphertext, not plaintext.
        assert store["1"]["email"] != "alice@example.com", (
            "DB must store ciphertext, not plaintext"
        )
        assert store["1"]["email"] is not None

        # Execute a subsequent read query.
        read_result = schema.execute_sync(
            "{ user { email firstName lastName displayName } }",
            context_value=authenticated_context,
        )

        assert not read_result.errors, (
            f"Read query must succeed: {read_result.errors}"
        )
        assert read_result.data["user"]["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# AC2 + AC5: Batch fields — write stores ciphertext per field, read returns all
# ---------------------------------------------------------------------------


class TestBatchFieldRoundtrip:
    """AC2 + AC5: Batch write → DB ciphertext per field → query returns all plaintext."""

    def test_batch_group_write_stores_ciphertext_per_field_read_returns_all_plaintext(
        self,
        _schema,
    ) -> None:
        """After a batch write mutation the DB must contain individual ciphertext
        strings per field.  A subsequent query must return all original plaintext
        values (AC2 + AC5).
        """
        schema, store = _schema

        authenticated_context = MagicMock()
        authenticated_context.user.is_authenticated = True

        write_result = schema.execute_sync(
            """
            mutation {
                updateUser(input: {
                    email: "alice@example.com",
                    firstName: "Alice",
                    lastName: "Smith"
                }) {
                    email
                    firstName
                    lastName
                }
            }
            """,
            context_value=authenticated_context,
        )

        assert not write_result.errors, (
            f"Write mutation must succeed: {write_result.errors}"
        )

        # Each batch field must be stored separately as ciphertext.
        assert store["1"]["first_name"] != "Alice", (
            "DB must store ciphertext for first_name, not plaintext"
        )
        assert store["1"]["last_name"] != "Smith", (
            "DB must store ciphertext for last_name, not plaintext"
        )
        assert store["1"]["first_name"] != store["1"]["last_name"], (
            "Each field must have its own distinct ciphertext"
        )

        # Read query must return all plaintext values.
        read_result = schema.execute_sync(
            "{ user { email firstName lastName } }",
            context_value=authenticated_context,
        )

        assert not read_result.errors, f"Read query must succeed: {read_result.errors}"
        assert read_result.data["user"]["firstName"] == "Alice"
        assert read_result.data["user"]["lastName"] == "Smith"


# ---------------------------------------------------------------------------
# AC7: Tampered DB value → null field, error in response, rest intact
# ---------------------------------------------------------------------------


class TestTamperedDbValue:
    """AC7: A tampered DB value must cause the affected field to be null with a
    structured error, while non-encrypted fields and other groups remain intact.
    """

    def test_tampered_db_value_returns_null_field_with_error_rest_intact(
        self,
        _schema,
    ) -> None:
        """When the DB contains a tampered / invalid ciphertext for ``email``,
        the query must return ``null`` for that field with an error entry, while
        ``display_name`` and batch-group fields remain readable (AC7).
        """
        import strawberry  # noqa: PLC0415

        from syntek_graphql_crypto.directives import Encrypted  # noqa: PLC0415
        from syntek_graphql_crypto.middleware import EncryptionMiddleware  # noqa: PLC0415

        # Seed the in-memory store with a tampered ciphertext for ``email`` and
        # valid ciphertexts for the profile batch group.  We mock pyo3 so that
        # only the ``email`` field raises on decrypt.
        mock_pyo3 = MagicMock()

        def _selective_decrypt(ciphertext: str, key: str, model: str, field: str) -> str:
            if field == "email":
                raise RuntimeError("GCM tag mismatch")
            return f"PLAINTEXT_{field}"

        mock_pyo3.decrypt_field.side_effect = _selective_decrypt
        mock_pyo3.decrypt_fields_batch.side_effect = lambda fields, key, model: [
            f"PLAINTEXT_{fname}" for _ct, fname in fields
        ]

        @strawberry.type
        class UserType:
            email: str | None = strawberry.field(
                directives=[Encrypted()],
                resolver=lambda: "TAMPERED_CIPHERTEXT",
            )
            first_name: str | None = strawberry.field(
                directives=[Encrypted(batch="profile")],
                resolver=lambda: "FAKE_CT_first_name",
            )
            last_name: str | None = strawberry.field(
                directives=[Encrypted(batch="profile")],
                resolver=lambda: "FAKE_CT_last_name",
            )
            display_name: str = strawberry.field(resolver=lambda: "Alice Smith")

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> UserType:
                return UserType()

        schema = strawberry.Schema(query=Query, extensions=[EncryptionMiddleware])

        authenticated_context = MagicMock()
        authenticated_context.user.is_authenticated = True

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                "{ user { email firstName lastName displayName } }",
                context_value=authenticated_context,
            )

        # ``email`` must be null.
        assert result.data["user"]["email"] is None

        # A structured error must be present.
        assert result.errors, "A structured error must be present for the tampered field"

        # ``display_name`` must still be present.
        assert result.data["user"]["displayName"] == "Alice Smith"

        # Batch profile fields must still be decrypted.
        assert result.data["user"]["firstName"] == "PLAINTEXT_first_name"
        assert result.data["user"]["lastName"] == "PLAINTEXT_last_name"


# ---------------------------------------------------------------------------
# AC10: Unauthenticated read → all encrypted fields null, auth error
# ---------------------------------------------------------------------------


class TestUnauthenticatedRead:
    """AC10: An unauthenticated read must null all encrypted fields and include
    an auth error, while non-encrypted fields are still returned.
    """

    def test_unauthenticated_read_returns_null_encrypted_fields_with_auth_error(
        self,
        _schema,
    ) -> None:
        """All ``@encrypted`` fields must be ``null`` for an unauthenticated
        request.  An auth error must be in the ``errors`` array.
        ``display_name`` (non-encrypted) must still be present (AC10).
        """
        schema, _store = _schema

        mock_pyo3 = MagicMock()
        mock_pyo3.decrypt_field.side_effect = lambda ct, k, m, f: f"PLAINTEXT_{f}"
        mock_pyo3.decrypt_fields_batch.side_effect = lambda fields, k, m: [
            f"PLAINTEXT_{fname}" for _ct, fname in fields
        ]

        unauthenticated_context = MagicMock()
        unauthenticated_context.user.is_authenticated = False

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                "{ user { email firstName lastName displayName } }",
                context_value=unauthenticated_context,
            )

        # All encrypted fields must be null.
        assert result.data["user"]["email"] is None
        assert result.data["user"]["firstName"] is None
        assert result.data["user"]["lastName"] is None

        # An auth error must be in the errors array.
        assert result.errors, "An auth error must be present in the errors array"
        error_text = " ".join(str(e) for e in result.errors).lower()
        assert any(
            kw in error_text
            for kw in ("auth", "unauthenticated", "unauthori", "permission")
        )

        # Non-encrypted field must still be present.
        assert result.data["user"]["displayName"] == "Alice Smith"

        # No decryption must have been attempted.
        mock_pyo3.decrypt_field.assert_not_called()
        mock_pyo3.decrypt_fields_batch.assert_not_called()
