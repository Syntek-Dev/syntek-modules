"""US008 — Red phase: auth-guard tests for ``syntek-graphql-crypto``.

Verifies that the ``EncryptionMiddleware`` enforces authentication before
performing any decryption:

- Unauthenticated requests must receive ``null`` for all ``@encrypted`` fields.
- An authorisation error must be appended to the GraphQL ``errors`` array.
- Non-encrypted fields must still be returned (the request is not aborted).
- No decryption must be attempted for unauthenticated requests.
- The attempt must be logged via the syntek-logging integration.
- Authenticated requests must proceed normally through the decryption path.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_auth_guard.py -v

AC coverage:
    AC10 — unauthenticated request → encrypted fields null, auth error logged
    AC11 — resolver isolation (verified as a side-effect of auth-guard behaviour)
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
# annotation string "AuthUserType" from module globals when
# ``from __future__ import annotations`` is active.
# ---------------------------------------------------------------------------


@strawberry.type
class AuthUserType:
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


def _make_normal_pyo3() -> MagicMock:
    """Return a mock ``syntek_pyo3`` whose ``decrypt_field`` returns plaintext."""
    mock = MagicMock()
    mock.decrypt_field.side_effect = lambda _ct, _key, _model, field: (
        f"PLAINTEXT_{field}"
    )
    mock.decrypt_fields_batch.side_effect = lambda fields, _key, _model: [
        f"PLAINTEXT_{fname}" for fname, _ct in fields
    ]
    return mock


def _build_schema_with_middleware() -> strawberry.Schema:
    """Build a minimal Strawberry schema with ``EncryptionMiddleware`` attached."""

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> AuthUserType:
            return AuthUserType()

    return strawberry.Schema(
        query=Query, extensions=[EncryptionMiddleware], types=[AuthUserType]
    )


def _execute_with_auth(*, authenticated: bool, mock_pyo3: MagicMock) -> dict:
    """Execute the test schema query with the given authentication state.

    ``info.context.user.is_authenticated`` is set to ``authenticated``.
    """
    schema = _build_schema_with_middleware()

    context = MagicMock()
    context.user.is_authenticated = authenticated

    with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
        result = schema.execute_sync(
            "{ user { email firstName lastName displayName } }",
            context_value=context,
        )

    return {"data": result.data, "errors": result.errors or []}


# ---------------------------------------------------------------------------
# AC10: Auth guard — unauthenticated requests
# ---------------------------------------------------------------------------


class TestAuthGuard:
    """The middleware must enforce authentication before any decryption (AC10)."""

    def test_unauthenticated_request_sets_encrypted_field_to_null(self) -> None:
        """All ``@encrypted`` fields must be ``null`` when the request is
        unauthenticated (AC10).
        """
        mock_pyo3 = _make_normal_pyo3()
        response = _execute_with_auth(authenticated=False, mock_pyo3=mock_pyo3)
        assert response["data"]["user"]["email"] is None
        assert response["data"]["user"]["firstName"] is None
        assert response["data"]["user"]["lastName"] is None

    def test_unauthenticated_request_appends_auth_error_to_errors_array(
        self,
    ) -> None:
        """An authorisation error must be appended to the GraphQL ``errors``
        array so the client can distinguish an auth failure from a data error
        (AC10).
        """
        mock_pyo3 = _make_normal_pyo3()
        response = _execute_with_auth(authenticated=False, mock_pyo3=mock_pyo3)
        assert len(response["errors"]) >= 1, (
            "At least one auth error must be present in errors array"
        )
        error_text = " ".join(str(e) for e in response["errors"]).lower()
        assert any(
            keyword in error_text
            for keyword in ("auth", "unauthenticated", "unauthori", "permission")
        ), f"Error must be recognisable as an auth error: {response['errors']}"

    def test_unauthenticated_request_does_not_abort_entire_response(self) -> None:
        """Non-encrypted fields must still be present in the response even when
        the request is unauthenticated — the request must not be aborted
        entirely (AC10).
        """
        mock_pyo3 = _make_normal_pyo3()
        response = _execute_with_auth(authenticated=False, mock_pyo3=mock_pyo3)
        assert response["data"]["user"]["displayName"] == "Alice Smith"

    def test_unauthenticated_request_does_not_call_decrypt_field(self) -> None:
        """``decrypt_field`` must not be called when the request is
        unauthenticated — no decryption must be attempted (AC10).
        """
        mock_pyo3 = _make_normal_pyo3()
        _execute_with_auth(authenticated=False, mock_pyo3=mock_pyo3)
        mock_pyo3.decrypt_field.assert_not_called()

    def test_auth_error_is_logged_via_syntek_logging(self) -> None:
        """The unauthenticated access attempt must be logged via the
        syntek-logging integration (``warning`` or ``info`` level) so that
        operators can detect and alert on repeated auth failures (AC10).
        """
        mock_pyo3 = _make_normal_pyo3()
        mock_logger = MagicMock()

        with patch("syntek_graphql_crypto.middleware.logger", mock_logger):
            _execute_with_auth(authenticated=False, mock_pyo3=mock_pyo3)

        # The middleware must call logger.warning or logger.info with a message
        # that references authentication.
        logged = (
            mock_logger.warning.called
            or mock_logger.info.called
            or mock_logger.error.called
        )
        assert logged, (
            "Unauthenticated access attempt must be logged via syntek-logging"
        )

        # Collect all logged messages and verify at least one contains an
        # auth-related keyword.
        all_calls = (
            list(mock_logger.warning.call_args_list)
            + list(mock_logger.info.call_args_list)
            + list(mock_logger.error.call_args_list)
        )
        messages = " ".join(str(c) for c in all_calls).lower()
        assert any(
            kw in messages for kw in ("unauthenticated", "auth", "encrypted", "access")
        ), f"Logged message must reference authentication: {all_calls}"

    def test_authenticated_request_decrypts_normally(self) -> None:
        """When the request is authenticated, all ``@encrypted`` fields must be
        decrypted and returned as plaintext — the happy path (AC10 / AC4 / AC5).
        """
        mock_pyo3 = _make_normal_pyo3()
        response = _execute_with_auth(authenticated=True, mock_pyo3=mock_pyo3)
        assert response["data"]["user"]["email"] == "PLAINTEXT_email"
        assert response["data"]["user"]["firstName"] == "PLAINTEXT_first_name"
        assert response["data"]["user"]["lastName"] == "PLAINTEXT_last_name"
        assert not response["errors"], (
            "No errors expected for a fully authenticated and successful request"
        )
