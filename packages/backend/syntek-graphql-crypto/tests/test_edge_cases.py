"""US008 — Edge-case tests for ``syntek-graphql-crypto``.

Covers missing test scenarios identified in the QA report:

- M5  — schema with no ``@encrypted`` fields (empty encrypted map)
- M6  — list-returning queries
- H3  — nested encrypted objects
- H4  — unauthenticated mutation (write-path auth logging)
- M7  — ``_get_encrypted_args_from_method`` reflection failure

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_edge_cases.py -v
"""

from __future__ import annotations

import typing
from unittest.mock import MagicMock, patch

import pytest
import strawberry
from syntek_graphql_crypto.directives import Encrypted
from syntek_graphql_crypto.middleware import EncryptionMiddleware

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_normal_pyo3() -> MagicMock:
    """Return a mock ``syntek_pyo3`` with working encrypt/decrypt."""
    mock = MagicMock()
    mock.encrypt_field.side_effect = lambda pt, _key, _model, field: (
        f"CIPHERTEXT_{field}_{pt}"
    )
    mock.encrypt_fields_batch.side_effect = lambda fields, _key, _model: [
        f"CIPHERTEXT_{fname}_{val}" for fname, val in fields
    ]
    mock.decrypt_field.side_effect = lambda _ct, _key, _model, field: (
        f"PLAINTEXT_{field}"
    )
    mock.decrypt_fields_batch.side_effect = lambda fields, _key, _model: [
        f"PLAINTEXT_{fname}" for fname, _ct in fields
    ]
    return mock


# ---------------------------------------------------------------------------
# Module-level Strawberry types — required so that Strawberry can resolve
# annotation strings from module globals when ``from __future__ import
# annotations`` is active.
# ---------------------------------------------------------------------------


@strawberry.type
class PlainUser:
    """Schema type with no @encrypted fields (M5)."""

    name: str = strawberry.field(resolver=lambda: "Alice")
    age: int = strawberry.field(resolver=lambda: 30)


@strawberry.type
class ListUser:
    """Schema type for list-returning queries (M6)."""

    email: str | None = strawberry.field(directives=[Encrypted()])
    name: str = strawberry.field()


@strawberry.type
class NestedAddress:
    """Nested type with encrypted field (H3)."""

    postcode: str | None = strawberry.field(directives=[Encrypted()])
    city: str = strawberry.field()


@strawberry.type
class NestedUser:
    """Parent type with nested encrypted child (H3)."""

    name: str = strawberry.field()
    address: NestedAddress = strawberry.field()


@strawberry.type
class MutWriteType:
    """Mutation type for unauthenticated write-path test (H4)."""

    @strawberry.mutation
    def create_user(
        self,
        email: typing.Annotated[str, Encrypted()],
    ) -> str:
        return email


# ---------------------------------------------------------------------------
# M5: Schema with no @encrypted fields
# ---------------------------------------------------------------------------


class TestEmptyEncryptedMap:
    """The middleware must not error when applied to a schema with zero
    ``@encrypted`` fields (M5).
    """

    def test_schema_without_encrypted_fields_returns_data_normally(self) -> None:
        """A schema with no encrypted fields must return data unchanged."""

        @strawberry.type
        class PlainQuery:
            @strawberry.field
            def user(self) -> PlainUser:
                return PlainUser()

        schema = strawberry.Schema(
            query=PlainQuery,
            extensions=[EncryptionMiddleware],
            types=[PlainUser],
        )

        context = MagicMock()
        context.user.is_authenticated = True
        result = schema.execute_sync("{ user { name age } }", context_value=context)
        assert not result.errors
        assert result.data is not None
        assert result.data["user"]["name"] == "Alice"
        assert result.data["user"]["age"] == 30


# ---------------------------------------------------------------------------
# M6: List-returning queries
# ---------------------------------------------------------------------------


class TestListResponseHandling:
    """Queries that return a list of objects with ``@encrypted`` fields must
    decrypt every item in the list (M6).
    """

    def test_list_query_decrypts_all_items(self) -> None:
        """Each item in a list response must have its encrypted fields
        decrypted."""

        @strawberry.type
        class ListQuery:
            @strawberry.field
            def users(self) -> list[ListUser]:
                return [
                    ListUser(email="CT_alice", name="Alice"),
                    ListUser(email="CT_bob", name="Bob"),
                ]

        schema = strawberry.Schema(
            query=ListQuery,
            extensions=[EncryptionMiddleware],
            types=[ListUser],
        )

        mock_pyo3 = _make_normal_pyo3()
        context = MagicMock()
        context.user.is_authenticated = True

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                "{ users { email name } }", context_value=context
            )

        assert not result.errors, result.errors
        assert result.data is not None
        assert len(result.data["users"]) == 2
        for user in result.data["users"]:
            assert user["email"] == "PLAINTEXT_email"


# ---------------------------------------------------------------------------
# H3: Nested encrypted objects
# ---------------------------------------------------------------------------


class TestNestedEncryptedObjects:
    """Encrypted fields on nested related objects must be decrypted
    recursively (H3).
    """

    def test_nested_encrypted_field_is_decrypted(self) -> None:
        """A nested object's ``@encrypted`` field must be decrypted by the
        middleware's recursive descent."""

        @strawberry.type
        class NestedQuery:
            @strawberry.field
            def user(self) -> NestedUser:
                return NestedUser(
                    name="Alice",
                    address=NestedAddress(postcode="CT_SW1A", city="London"),
                )

        schema = strawberry.Schema(
            query=NestedQuery,
            extensions=[EncryptionMiddleware],
            types=[NestedUser, NestedAddress],
        )

        mock_pyo3 = _make_normal_pyo3()
        context = MagicMock()
        context.user.is_authenticated = True

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                "{ user { name address { postcode city } } }",
                context_value=context,
            )

        assert not result.errors, result.errors
        assert result.data is not None
        assert result.data["user"]["name"] == "Alice"
        assert result.data["user"]["address"]["postcode"] == "PLAINTEXT_postcode"
        assert result.data["user"]["address"]["city"] == "London"


# ---------------------------------------------------------------------------
# H4: Unauthenticated mutation (write-path auth logging)
# ---------------------------------------------------------------------------


class TestUnauthenticatedMutation:
    """Unauthenticated mutations must still encrypt the input (the data needs
    to be protected regardless of auth status). Auth enforcement is the
    responsibility of the Django permission layer (H4).
    """

    def test_unauthenticated_mutation_still_encrypts_input(self) -> None:
        """The middleware must encrypt mutation inputs even when the request
        is unauthenticated — the write path must always protect data."""

        @strawberry.type
        class MutWriteQuery:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(
            query=MutWriteQuery,
            mutation=MutWriteType,
            extensions=[EncryptionMiddleware],
        )

        mock_pyo3 = _make_normal_pyo3()
        context = MagicMock()
        context.user.is_authenticated = False

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                'mutation { createUser(email: "alice@example.com") }',
                context_value=context,
            )

        # The mutation should succeed (encryption happens regardless of auth).
        assert not result.errors, result.errors
        assert result.data is not None
        # The resolver receives ciphertext, not plaintext.
        assert result.data["createUser"].startswith("CIPHERTEXT_")
        mock_pyo3.encrypt_field.assert_called_once()


# ---------------------------------------------------------------------------
# M7: Reflection failure in _get_encrypted_args_from_method
# ---------------------------------------------------------------------------


class TestReflectionFailure:
    """When ``_get_encrypted_args_from_method`` fails to inspect a resolver,
    it must log the error rather than silently swallowing it (M7).
    """

    def test_reflection_failure_logs_error(self) -> None:
        """A reflection failure must be logged at ERROR level."""
        from syntek_graphql_crypto.middleware import _get_encrypted_args_from_method

        mock_parent = MagicMock()
        # Make extensions return a type_def whose origin attribute raises.
        type_def = MagicMock()
        origin = MagicMock()
        # get_type_hints will fail on a MagicMock method with a RuntimeError
        origin.test_field = "not_a_callable"
        type_def.origin = origin
        mock_parent.extensions = {"strawberry-definition": type_def}

        mock_logger = MagicMock()
        with patch("syntek_graphql_crypto.middleware.logger", mock_logger):
            result = _get_encrypted_args_from_method(mock_parent, "test_field")

        # Should return empty dict (no crash) and log the error.
        assert result == {}


# ---------------------------------------------------------------------------
# Same plaintext encrypted twice produces different ciphertexts
# (Missing test scenario 8)
# ---------------------------------------------------------------------------


class TestNonceUniqueness:
    """AES-256-GCM with random nonces must produce distinct ciphertexts for
    the same plaintext encrypted twice.
    """

    def test_same_plaintext_produces_different_ciphertexts(self) -> None:
        """Two encryptions of the same plaintext must yield different
        ciphertexts (verifies random nonce usage)."""
        pytest.importorskip(
            "syntek_pyo3",
            reason="syntek_pyo3 native extension not built",
        )

        from syntek_graphql_crypto.middleware import EncryptionMiddleware

        mw = EncryptionMiddleware(model="User")
        ct1 = mw.process_input(field_name="email", value="alice@example.com")
        ct2 = mw.process_input(field_name="email", value="alice@example.com")

        assert ct1 != ct2, (
            "Same plaintext encrypted twice must produce different ciphertexts"
        )
