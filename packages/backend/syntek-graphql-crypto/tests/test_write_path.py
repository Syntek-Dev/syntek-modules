"""US008 — Red phase: write-path (encryption) tests for ``syntek-graphql-crypto``.

Verifies that the ``EncryptionMiddleware`` correctly intercepts mutation input
arguments, routes individual ``@encrypted`` fields through ``encrypt_field`` and
batch ``@encrypted(batch: ...)`` groups through ``encrypt_fields_batch``, and
that no plaintext ever reaches the resolver.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

``syntek_pyo3`` is mocked via ``unittest.mock.patch`` so that the native
extension does not need to be built to run these tests.  The mock
``encrypt_field`` returns ``"FAKE_CIPHERTEXT_<field>"`` for each call, and
``encrypt_fields_batch`` returns a list of ``"FAKE_CIPHERTEXT_<field>"`` strings
in input order.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_write_path.py -v

AC coverage:
    AC1  — individual ``@encrypted`` field encrypted before resolver runs
    AC2  — batch group encrypted in a single ``encrypt_fields_batch`` call
    AC3  — mixed individual + batch: each processed via the correct path
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_pyo3() -> MagicMock:
    """Return a mock ``syntek_pyo3`` module.

    ``encrypt_field`` returns ``"FAKE_CIPHERTEXT_<field>"`` (the 4th positional
    argument is the field name).
    ``encrypt_fields_batch`` returns a list of ``"FAKE_CIPHERTEXT_<field>"``
    strings preserving input order.
    """
    mock = MagicMock()
    mock.encrypt_field.side_effect = lambda _plaintext, _key, _model, field: (
        f"FAKE_CIPHERTEXT_{field}"
    )
    mock.encrypt_fields_batch.side_effect = lambda fields, _key, _model: [
        f"FAKE_CIPHERTEXT_{fname}" for fname, _val in fields
    ]
    return mock


# ---------------------------------------------------------------------------
# AC1: Write path — individual @encrypted fields
# ---------------------------------------------------------------------------


class TestWritePathIndividualField:
    """Individual ``@encrypted`` fields must be encrypted via ``encrypt_field``
    before the resolver receives the value (AC1).
    """

    def test_encrypted_field_value_replaced_with_ciphertext_before_resolver(
        self,
    ) -> None:
        """The resolver must receive a ciphertext string, not the original
        plaintext ``"alice@example.com"`` (AC1).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            received_values: list[str] = []

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_input(
                field_name="email",
                value="alice@example.com",
                batch_group=None,
                capture=received_values.append,
            )

        assert result != "alice@example.com", (
            "Resolver must receive ciphertext, not plaintext"
        )
        assert result == "FAKE_CIPHERTEXT_email"

    def test_individual_field_calls_encrypt_field_exactly_once(self) -> None:
        """Processing one individual ``@encrypted`` field must result in exactly
        one call to ``encrypt_field`` (AC1).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_input(
                field_name="email",
                value="alice@example.com",
                batch_group=None,
            )

        assert mock_pyo3.encrypt_field.call_count == 1

    def test_encrypt_field_called_with_correct_model_field_and_key(self) -> None:
        """``encrypt_field`` must receive the plaintext as the first argument,
        a ``KeyRing`` as the second, the model name as the third, and the
        field name as the fourth (AC1).
        """
        from syntek_pyo3 import KeyRing

        mock_pyo3 = _make_mock_pyo3()

        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_input(
                field_name="email",
                value="alice@example.com",
                batch_group=None,
            )

        mock_pyo3.encrypt_field.assert_called_once()
        call_args = mock_pyo3.encrypt_field.call_args[0]
        assert call_args[0] == "alice@example.com"
        assert isinstance(call_args[1], KeyRing)
        assert call_args[2] == "User"
        assert call_args[3] == "email"

    def test_non_encrypted_field_value_unchanged(self) -> None:
        """A field with no ``@encrypted`` directive must pass through the
        middleware unmodified (AC6).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_input(
                field_name="display_name",
                value="Alice",
                batch_group=None,
                is_encrypted=False,
            )

        assert result == "Alice"
        mock_pyo3.encrypt_field.assert_not_called()


# ---------------------------------------------------------------------------
# AC2: Write path — batch group fields
# ---------------------------------------------------------------------------


class TestWritePathBatchGroup:
    """Batch ``@encrypted(batch: "group")`` fields must be encrypted via a
    single ``encrypt_fields_batch`` call, not via individual ``encrypt_field``
    calls (AC2).
    """

    def test_batch_group_uses_encrypt_fields_batch_not_encrypt_field(self) -> None:
        """When all fields share a batch group, ``encrypt_fields_batch`` must be
        called and ``encrypt_field`` must NOT be called (AC2).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_input(
                batch_group="profile",
                fields=[
                    ("Alice", "first_name"),
                    ("Smith", "last_name"),
                ],
            )

        mock_pyo3.encrypt_fields_batch.assert_called_once()
        mock_pyo3.encrypt_field.assert_not_called()

    def test_batch_group_calls_encrypt_fields_batch_exactly_once(self) -> None:
        """A batch group with three fields must still produce exactly one call to
        ``encrypt_fields_batch`` (AC2).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_input(
                batch_group="address",
                fields=[
                    ("10 Downing Street", "address_line_1"),
                    ("Westminster", "address_line_2"),
                    ("SW1A 2AA", "postcode"),
                ],
            )

        assert mock_pyo3.encrypt_fields_batch.call_count == 1

    def test_batch_fields_replaced_with_ciphertexts(self) -> None:
        """The resolver must receive one ciphertext per field in the batch, in
        the same order as the input (AC2).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            result = middleware.process_batch_input(
                batch_group="profile",
                fields=[
                    ("Alice", "first_name"),
                    ("Smith", "last_name"),
                ],
            )

        assert result == ["FAKE_CIPHERTEXT_first_name", "FAKE_CIPHERTEXT_last_name"]


# ---------------------------------------------------------------------------
# AC3: Write path — mixed individual + batch fields
# ---------------------------------------------------------------------------


class TestWritePathMixed:
    """When a mutation contains both individual and batch ``@encrypted`` fields,
    each must be routed to the correct call path (AC3).
    """

    def test_individual_field_uses_encrypt_field_batch_uses_encrypt_fields_batch(
        self,
    ) -> None:
        """The middleware must call ``encrypt_field`` for individual fields and
        ``encrypt_fields_batch`` for batch fields — never the wrong function
        for either type (AC3).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_input(
                field_name="email",
                value="alice@example.com",
                batch_group=None,
            )
            middleware.process_batch_input(
                batch_group="profile",
                fields=[("Alice", "first_name"), ("Smith", "last_name")],
            )

        mock_pyo3.encrypt_field.assert_called_once()
        mock_pyo3.encrypt_fields_batch.assert_called_once()

    def test_different_batch_groups_produce_separate_calls(self) -> None:
        """Two distinct batch groups must each produce their own call to
        ``encrypt_fields_batch`` — two groups → two calls (AC3).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_input(
                batch_group="profile",
                fields=[("Alice", "first_name"), ("Smith", "last_name")],
            )
            middleware.process_batch_input(
                batch_group="address",
                fields=[
                    ("10 Downing Street", "address_line_1"),
                    ("SW1A 2AA", "postcode"),
                ],
            )

        assert mock_pyo3.encrypt_fields_batch.call_count == 2

    def test_fields_from_different_groups_never_combined(self) -> None:
        """Fields from group ``"profile"`` must never appear in the
        ``encrypt_fields_batch`` call for group ``"address"`` (AC3).
        """
        mock_pyo3 = _make_mock_pyo3()
        with patch("syntek_graphql_crypto.middleware.syntek_pyo3", mock_pyo3):
            from syntek_graphql_crypto.middleware import (
                EncryptionMiddleware,
            )

            middleware = EncryptionMiddleware(model="User")
            middleware.process_batch_input(
                batch_group="profile",
                fields=[("Alice", "first_name"), ("Smith", "last_name")],
            )
            middleware.process_batch_input(
                batch_group="address",
                fields=[("SW1A 2AA", "postcode")],
            )

        calls = mock_pyo3.encrypt_fields_batch.call_args_list
        # Collect all field names passed to each call.
        for c in calls:
            field_names = [fname for fname, _val in c.args[0]]
            if "postcode" in field_names:
                assert "first_name" not in field_names
                assert "last_name" not in field_names
            if "first_name" in field_names or "last_name" in field_names:
                assert "postcode" not in field_names
