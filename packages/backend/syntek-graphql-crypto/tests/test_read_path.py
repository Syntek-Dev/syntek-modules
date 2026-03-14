"""US008 — Red phase: read-path (decryption) tests for ``syntek-graphql-crypto``.

Verifies that the ``EncryptionMiddleware`` correctly intercepts resolver return
values, routes individual ``@encrypted`` fields through ``decrypt_field`` and
batch ``@encrypted(batch: ...)`` groups through ``decrypt_fields_batch``, and
that the frontend receives plaintext — never ciphertext.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

``syntek_pyo3`` is mocked via ``unittest.mock.patch`` so that the native
extension does not need to be built to run these tests.  The mock
``decrypt_field`` returns ``"PLAINTEXT_<field>"`` and ``decrypt_fields_batch``
returns a list of ``"PLAINTEXT_<field>"`` strings in input order.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_read_path.py -v

AC coverage:
    AC4  — individual ``@encrypted`` field decrypted before serialisation
    AC5  — batch group decrypted in a single ``decrypt_fields_batch`` call
    AC6  — non-annotated fields pass through unchanged with no overhead
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_pyo3() -> MagicMock:
    """Return a mock ``syntek_pyo3`` module for read-path tests.

    ``decrypt_field`` returns ``"PLAINTEXT_<field>"`` (the 4th positional
    argument is the field name).
    ``decrypt_fields_batch`` returns a list of ``"PLAINTEXT_<field>"`` strings
    preserving input order.
    """
    mock = MagicMock()
    mock.decrypt_field.side_effect = lambda _ciphertext, _key, _model, field: (
        f"PLAINTEXT_{field}"
    )
    mock.decrypt_fields_batch.side_effect = lambda fields, _key, _model: [
        f"PLAINTEXT_{fname}" for fname, _ct in fields
    ]
    return mock


# ---------------------------------------------------------------------------
# AC4: Read path — individual @encrypted fields
# ---------------------------------------------------------------------------


class TestReadPathIndividualField:
    """Individual ``@encrypted`` fields must be decrypted via ``decrypt_field``
    before the response is serialised and returned to the frontend (AC4).
    """

    def test_encrypted_field_ciphertext_replaced_with_plaintext_after_resolver(
        self,
    ) -> None:
        """The serialised response must contain the decrypted plaintext, not the
        raw ciphertext ``"FAKE_CIPHERTEXT_email"`` that the resolver returned (AC4).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_output(
                field_name="email",
                value="FAKE_CIPHERTEXT_email",
                batch_group=None,
            )

        assert result == "PLAINTEXT_email"
        assert result != "FAKE_CIPHERTEXT_email", (
            "Frontend must receive plaintext, not ciphertext"
        )

    def test_individual_field_calls_decrypt_field_exactly_once(self) -> None:
        """Processing one individual ``@encrypted`` output field must produce
        exactly one call to ``decrypt_field`` (AC4).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_output(
                field_name="email",
                value="FAKE_CIPHERTEXT_email",
                batch_group=None,
            )

        assert mock_pyo3.decrypt_field.call_count == 1

    def test_decrypt_field_called_with_correct_model_field_and_key(self) -> None:
        """``decrypt_field`` must receive the ciphertext as the first argument,
        a ``KeyRing`` as the second, the model name as the third, and the
        field name as the fourth (AC4).
        """
        from syntek_pyo3 import KeyRing

        mock_pyo3 = _make_mock_pyo3()

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_output(
                field_name="email",
                value="FAKE_CIPHERTEXT_email",
                batch_group=None,
            )

        mock_pyo3.decrypt_field.assert_called_once()
        call_args = mock_pyo3.decrypt_field.call_args[0]
        assert call_args[0] == "FAKE_CIPHERTEXT_email"
        assert isinstance(call_args[1], KeyRing)
        assert call_args[2] == "User"
        assert call_args[3] == "email"


# ---------------------------------------------------------------------------
# AC5: Read path — batch group fields
# ---------------------------------------------------------------------------


class TestReadPathBatchGroup:
    """Batch ``@encrypted(batch: "group")`` output fields must be decrypted via
    a single ``decrypt_fields_batch`` call (AC5).
    """

    def test_batch_group_uses_decrypt_fields_batch_not_decrypt_field(self) -> None:
        """When all output fields share a batch group, ``decrypt_fields_batch``
        must be called and ``decrypt_field`` must NOT be called (AC5).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_output(
                batch_group="profile",
                fields=[
                    ("FAKE_CIPHERTEXT_first_name", "first_name"),
                    ("FAKE_CIPHERTEXT_last_name", "last_name"),
                ],
            )

        mock_pyo3.decrypt_fields_batch.assert_called_once()
        mock_pyo3.decrypt_field.assert_not_called()

    def test_batch_group_calls_decrypt_fields_batch_exactly_once(self) -> None:
        """A batch group with three ciphertexts must produce exactly one call to
        ``decrypt_fields_batch`` (AC5).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_output(
                batch_group="address",
                fields=[
                    ("FAKE_CT_address_line_1", "address_line_1"),
                    ("FAKE_CT_address_line_2", "address_line_2"),
                    ("FAKE_CT_postcode", "postcode"),
                ],
            )

        assert mock_pyo3.decrypt_fields_batch.call_count == 1

    def test_all_batch_fields_decrypted_in_response(self) -> None:
        """The middleware must return one plaintext string per batch field, in
        the same order as the input ciphertexts (AC5).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_batch_output(
                batch_group="profile",
                fields=[
                    ("FAKE_CIPHERTEXT_first_name", "first_name"),
                    ("FAKE_CIPHERTEXT_last_name", "last_name"),
                ],
            )

        assert result == ["PLAINTEXT_first_name", "PLAINTEXT_last_name"]


# ---------------------------------------------------------------------------
# AC6: Read path — non-annotated fields (passthrough)
# ---------------------------------------------------------------------------


class TestReadPathPassthrough:
    """Fields without an ``@encrypted`` directive must pass through the
    middleware unchanged with no calls to ``decrypt_field`` or
    ``decrypt_fields_batch`` (AC6).
    """

    def test_non_annotated_field_passes_through_unchanged(self) -> None:
        """A plain string field with no ``@encrypted`` annotation must have the
        same value before and after middleware processing (AC6).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_output(
                field_name="display_name",
                value="Alice",
                batch_group=None,
                is_encrypted=False,
            )

        assert result == "Alice"

    def test_non_annotated_field_does_not_call_decrypt_field(self) -> None:
        """No call to ``decrypt_field`` must be made when processing a
        non-annotated field (AC6).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_output(
                field_name="display_name",
                value="Alice",
                batch_group=None,
                is_encrypted=False,
            )

        mock_pyo3.decrypt_field.assert_not_called()

    def test_non_annotated_field_does_not_call_decrypt_fields_batch(self) -> None:
        """No call to ``decrypt_fields_batch`` must be made when processing a
        non-annotated field (AC6).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_output(
                field_name="display_name",
                value="Alice",
                batch_group=None,
                is_encrypted=False,
            )

        mock_pyo3.decrypt_fields_batch.assert_not_called()
