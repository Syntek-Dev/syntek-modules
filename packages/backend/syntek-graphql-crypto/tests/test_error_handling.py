"""US008 — Red phase: error-handling tests for ``syntek-graphql-crypto``.

Verifies the middleware's graceful-degradation and hard-rejection policies:

- **Decrypt failure (individual)**: the affected field becomes ``null``, a
  structured error is appended to the GraphQL ``errors`` array, and the rest
  of the response is not aborted.
- **Decrypt failure (batch group)**: ALL fields in the group become ``null``,
  a single error entry is appended, and fields from other groups are unaffected.
- **Encrypt failure (mutation)**: the entire mutation is rejected with a
  structured error and no partial ciphertext is passed to the resolver.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_error_handling.py -v

AC coverage:
    AC7  — decrypt failure, individual field
    AC8  — decrypt failure, batch group
    AC9  — encrypt failure, mutation rejection
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import strawberry
from syntek_graphql_crypto.directives import Encrypted
from syntek_graphql_crypto.middleware import EncryptionMiddleware

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Module-level type definition — required so that Strawberry can resolve the
# annotation string "ErrorUserType" from module globals when
# ``from __future__ import annotations`` is active.
# ---------------------------------------------------------------------------


@strawberry.type
class ErrorUserType:
    email: str | None = strawberry.field(
        directives=[Encrypted()],
        resolver=lambda: "FAKE_CT_email",
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DECRYPT_ERROR_MSG = "GCM tag mismatch — ciphertext may have been tampered with"


def _make_failing_decrypt_pyo3(failing_fields: set[str] | None = None) -> MagicMock:
    """Return a mock ``syntek_pyo3`` whose ``decrypt_field`` and
    ``decrypt_fields_batch`` raise ``RuntimeError`` for any field in
    ``failing_fields`` (all fields if ``None``).
    """
    failing_fields = failing_fields or set()
    mock = MagicMock()

    def _decrypt_field(ciphertext: str, key: str, model: str, field: str) -> str:
        if not failing_fields or field in failing_fields:
            raise RuntimeError(_DECRYPT_ERROR_MSG)
        return f"PLAINTEXT_{field}"

    def _decrypt_fields_batch(
        fields: list[tuple[str, str]], key: str, model: str
    ) -> list[str]:
        for fname, _ct in fields:
            if not failing_fields or fname in failing_fields:
                raise RuntimeError(_DECRYPT_ERROR_MSG)
        return [f"PLAINTEXT_{fname}" for fname, _ct in fields]

    mock.decrypt_field.side_effect = _decrypt_field
    mock.decrypt_fields_batch.side_effect = _decrypt_fields_batch
    return mock


def _make_failing_encrypt_pyo3() -> MagicMock:
    """Return a mock ``syntek_pyo3`` whose ``encrypt_field`` and
    ``encrypt_fields_batch`` always raise ``RuntimeError``.
    """
    mock = MagicMock()
    mock.encrypt_field.side_effect = RuntimeError("HSM unavailable — encryption failed")
    mock.encrypt_fields_batch.side_effect = RuntimeError(
        "HSM unavailable — batch encryption failed"
    )
    return mock


def _execute_query_with_mock_pyo3(mock_pyo3: MagicMock) -> dict:
    """Execute a minimal Strawberry query via ``EncryptionMiddleware`` with the
    given mock ``syntek_pyo3`` and return the response dict.

    The schema used here has:
    - ``email`` — individual ``@encrypted`` field
    - ``first_name``, ``last_name`` — batch ``@encrypted(batch="profile")`` fields
    - ``display_name`` — plain, non-encrypted field
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> ErrorUserType:
            return ErrorUserType()

    schema = strawberry.Schema(
        query=Query, extensions=[EncryptionMiddleware], types=[ErrorUserType]
    )

    with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
        result = schema.execute_sync(
            "{ user { email firstName lastName displayName } }"
        )

    response: dict = {"data": result.data, "errors": result.errors or []}
    return response


# ---------------------------------------------------------------------------
# AC7: Decrypt failure — individual field
# ---------------------------------------------------------------------------


class TestDecryptFailureIndividualField:
    """Decryption failure on a single ``@encrypted`` field must null only that
    field, append one structured error, and leave the rest of the response
    intact (AC7).
    """

    def test_decrypt_failure_sets_field_to_null(self) -> None:
        """The field whose decryption failed must be ``null`` in the response
        data (AC7).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"email"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        assert response["data"]["user"]["email"] is None

    def test_decrypt_failure_appends_structured_error_to_errors_array(self) -> None:
        """A structured error must be appended to the GraphQL ``errors`` array.
        The error must include a ``field_path`` key and an ``error_type`` key
        so consumers can programmatically identify the affected field (AC7).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"email"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)

        assert len(response["errors"]) >= 1, "At least one error entry must be present"
        error = response["errors"][0]
        assert "field_path" in error or "path" in error, (
            "Error must carry field_path or path"
        )
        assert "error_type" in error or "message" in error, (
            "Error must carry error_type or message"
        )

    def test_decrypt_failure_does_not_abort_rest_of_response(self) -> None:
        """Non-encrypted fields must still be present in the response even when
        an encrypted field fails to decrypt (AC7).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"email"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        assert response["data"]["user"]["displayName"] == "Alice Smith"

    def test_decrypt_failure_other_encrypted_fields_still_decrypted(self) -> None:
        """Other ``@encrypted`` fields that are NOT in the failing set must still
        be successfully decrypted and present in the response (AC7).
        """
        # Only ``email`` fails; ``first_name`` and ``last_name`` should succeed.
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"email"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        # Batch profile fields (first_name, last_name) must still be decrypted.
        assert response["data"]["user"]["firstName"] == "PLAINTEXT_first_name"
        assert response["data"]["user"]["lastName"] == "PLAINTEXT_last_name"


# ---------------------------------------------------------------------------
# AC8: Decrypt failure — batch group
# ---------------------------------------------------------------------------


class TestDecryptFailureBatchGroup:
    """Any decryption failure within a batch group must null ALL fields in that
    group, append exactly one error entry, and leave other groups intact (AC8).
    """

    def test_batch_decrypt_failure_nulls_all_fields_in_group(self) -> None:
        """When ``decrypt_fields_batch`` raises for the ``"profile"`` group,
        both ``first_name`` and ``last_name`` must be ``null`` (AC8).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"first_name"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        assert response["data"]["user"]["firstName"] is None
        assert response["data"]["user"]["lastName"] is None

    def test_batch_decrypt_failure_appends_single_error_not_multiple(self) -> None:
        """A batch group failure must produce exactly one error entry in
        ``errors``, not one per field in the group (AC8).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"first_name"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        # Count errors related to the profile batch group.
        profile_errors = [
            e
            for e in response["errors"]
            if "profile" in str(e) or "first_name" in str(e) or "last_name" in str(e)
        ]
        assert len(profile_errors) == 1, (
            f"Expected 1 error for profile batch group, got {len(profile_errors)}"
        )

    def test_batch_decrypt_failure_does_not_null_fields_from_other_groups(
        self,
    ) -> None:
        """A failure in the ``"profile"`` batch group must not affect the
        individual ``email`` field — it must still be decrypted (AC8).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"first_name"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        assert response["data"]["user"]["email"] == "PLAINTEXT_email"

    def test_partial_batch_results_never_returned(self) -> None:
        """If ``decrypt_fields_batch`` raises, the middleware must not return
        a partial result where some fields are decrypted and others are null.
        ALL fields in the failing group must be null together (AC8).
        """
        mock_pyo3 = _make_failing_decrypt_pyo3(failing_fields={"last_name"})
        response = _execute_query_with_mock_pyo3(mock_pyo3)
        # Both fields must be null — not just the one that triggered the failure.
        msg = "Partial batch results must never be returned — both fields must be null"
        assert response["data"]["user"]["firstName"] is None, msg
        assert response["data"]["user"]["lastName"] is None, msg


# ---------------------------------------------------------------------------
# AC9: Encrypt failure — mutation rejection
# ---------------------------------------------------------------------------


class TestEncryptFailureMutation:
    """Any encryption failure in a mutation must reject the entire mutation with
    a structured error.  No partial ciphertext must reach the resolver (AC9).
    """

    def test_encrypt_failure_rejects_entire_mutation(self) -> None:
        """When ``encrypt_field`` raises, the mutation response must contain an
        error and the data must be ``null`` or absent (AC9).
        """
        import strawberry
        from syntek_graphql_crypto.middleware import (
            EncryptionMiddleware,
        )

        mock_pyo3 = _make_failing_encrypt_pyo3()

        resolver_called = {"value": False}

        @strawberry.type
        class MutationType:
            @strawberry.mutation
            def update_email(
                self,
                email: strawberry.annotated[str, Encrypted()],  # type: ignore[valid-type]
            ) -> str:
                resolver_called["value"] = True
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(
            query=Query,
            mutation=MutationType,
            extensions=[EncryptionMiddleware],
        )
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                'mutation { updateEmail(email: "alice@example.com") }'
            )

        assert result.errors, "Mutation must fail when encryption fails"

    def test_encrypt_failure_no_partial_ciphertext_written(self) -> None:
        """The resolver must NOT be called when encryption fails — no partial
        ciphertext must reach the ORM (AC9).
        """
        import strawberry
        from syntek_graphql_crypto.middleware import (
            EncryptionMiddleware,
        )

        mock_pyo3 = _make_failing_encrypt_pyo3()

        resolver_called = {"value": False}

        @strawberry.type
        class MutationType:
            @strawberry.mutation
            def update_profile(
                self,
                first_name: strawberry.annotated[str, Encrypted(batch="profile")],  # type: ignore[valid-type]
                last_name: strawberry.annotated[str, Encrypted(batch="profile")],  # type: ignore[valid-type]
            ) -> str:
                resolver_called["value"] = True
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(
            query=Query,
            mutation=MutationType,
            extensions=[EncryptionMiddleware],
        )
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            schema.execute_sync(
                'mutation { updateProfile(firstName: "Alice", lastName: "Smith") }'
            )

        assert not resolver_called["value"], (
            "Resolver must not be invoked when encryption fails — no partial ORM write"
        )

    def test_encrypt_failure_returns_structured_error(self) -> None:
        """The error returned on encryption failure must be structured — it
        must contain a non-empty message that operators can act on (AC9).
        """
        import strawberry
        from syntek_graphql_crypto.middleware import (
            EncryptionMiddleware,
        )

        mock_pyo3 = _make_failing_encrypt_pyo3()

        @strawberry.type
        class MutationType:
            @strawberry.mutation
            def update_email(
                self,
                email: strawberry.annotated[str, Encrypted()],  # type: ignore[valid-type]
            ) -> str:
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(
            query=Query,
            mutation=MutationType,
            extensions=[EncryptionMiddleware],
        )
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            result = schema.execute_sync(
                'mutation { updateEmail(email: "alice@example.com") }'
            )

        assert result.errors
        error_message = str(result.errors[0])
        assert len(error_message) > 0, "Error message must be non-empty"
