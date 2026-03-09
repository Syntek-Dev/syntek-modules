"""US007 — Red phase: Django EncryptedField model field tests.

Verifies the behaviour of `EncryptedField` and `EncryptedFieldDescriptor` as
described in US007.  The architecture boundary is the GraphQL layer:

  Write path: GraphQL middleware encrypts → resolver saves ciphertext → DB
  Read path:  DB returns ciphertext → resolver returns it → middleware decrypts

`EncryptedField` is therefore a *storage-and-validation type only*.  It never
encrypts on save or decrypts on load.  Its sole responsibility is:

  1. Accept ciphertext (valid base64ct, decoded length >= 28 bytes) on pre_save.
  2. Reject plaintext with `ValidationError` before the DB write.
  3. Return raw ciphertext from `from_db_value` — no decryption.
  4. Record model name and field name via `EncryptedFieldDescriptor` so the
     GraphQL middleware can resolve the correct AAD without manual annotation.

All tests FAIL during the red phase because `EncryptedField` and
`EncryptedFieldDescriptor` are not yet implemented.

Run with:
    pytest packages/backend/syntek-pyo3/tests/test_encrypted_field.py -v
"""

from __future__ import annotations

import base64

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 30 zero-bytes → valid base64, decoded length = 30 >= 28 (minimum ciphertext shell).
_VALID_CIPHERTEXT = base64.b64encode(b"\x00" * 30).decode()

# Values that look like plaintext and must be rejected.
_PLAINTEXT_VALUES = [
    "hello@example.com",
    "plaintext value",
    "short",
    "not-base64!!!",
    "",
    " ",
]


# ---------------------------------------------------------------------------
# AC1: EncryptedField and EncryptedFieldDescriptor are importable from syntek_pyo3
# ---------------------------------------------------------------------------


class TestEncryptedFieldImport:
    def test_encrypted_field_importable(self) -> None:
        from syntek_pyo3 import EncryptedField  # noqa: F401

    def test_encrypted_field_descriptor_importable(self) -> None:
        from syntek_pyo3 import EncryptedFieldDescriptor  # noqa: F401


# ---------------------------------------------------------------------------
# AC2: EncryptedField accepts a valid ciphertext without raising
# ---------------------------------------------------------------------------


class TestEncryptedFieldAcceptsCiphertext:
    def test_valid_ciphertext_fixture_passes_validation(self) -> None:
        """Base64ct string with >= 28 decoded bytes passes validation."""
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.validate(_VALID_CIPHERTEXT, model_instance=None)

    def test_real_ciphertext_from_encrypt_field_passes(self) -> None:
        """Ciphertext produced by `encrypt_field` must always pass
        EncryptedField validation.
        """
        from syntek_pyo3 import EncryptedField, encrypt_field

        key = bytes(range(32))
        ct = encrypt_field("hello@example.com", key, "User", "email")
        field = EncryptedField()
        field.validate(ct, model_instance=None)

    def test_pre_save_returns_ciphertext_unchanged(self) -> None:
        """pre_save must not re-encrypt — it returns the value as-is."""
        from unittest.mock import MagicMock

        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = _VALID_CIPHERTEXT
        assert field.pre_save(instance, add=False) == _VALID_CIPHERTEXT


# ---------------------------------------------------------------------------
# AC3: EncryptedField rejects plaintext before the DB write
# ---------------------------------------------------------------------------


class TestEncryptedFieldRejectsPlaintext:
    @pytest.mark.parametrize("plaintext", _PLAINTEXT_VALUES)
    def test_validate_raises_validation_error_for_plaintext(
        self, plaintext: str
    ) -> None:
        """validate() must raise ValidationError for any plaintext-looking value."""
        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        with pytest.raises(ValidationError):
            field.validate(plaintext, model_instance=None)

    @pytest.mark.parametrize("plaintext", _PLAINTEXT_VALUES)
    def test_pre_save_raises_validation_error_for_plaintext(
        self, plaintext: str
    ) -> None:
        """pre_save() must raise ValidationError — plaintext must never reach the DB."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = plaintext
        with pytest.raises(ValidationError):
            field.pre_save(instance, add=False)


# ---------------------------------------------------------------------------
# AC4: from_db_value is a passthrough — no decryption occurs
# ---------------------------------------------------------------------------


class TestFromDbValue:
    def test_returns_ciphertext_unchanged(self) -> None:
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        result = field.from_db_value(
            _VALID_CIPHERTEXT, expression=None, connection=None
        )
        assert result == _VALID_CIPHERTEXT

    def test_returns_none_for_null_db_value(self) -> None:
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        assert field.from_db_value(None, expression=None, connection=None) is None

    def test_does_not_call_decrypt_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Decryption is the GraphQL middleware's job —
        from_db_value must not decrypt.
        """
        import syntek_pyo3
        from syntek_pyo3 import EncryptedField

        calls: list[str] = []

        def _spy(*args: object, **kwargs: object) -> str:
            calls.append("decrypt_field called")
            return "plaintext"

        monkeypatch.setattr(syntek_pyo3, "decrypt_field", _spy, raising=False)

        field = EncryptedField()
        field.from_db_value(_VALID_CIPHERTEXT, expression=None, connection=None)
        assert calls == [], "from_db_value must not call decrypt_field"


# ---------------------------------------------------------------------------
# EncryptedFieldDescriptor: records model + field name for GraphQL middleware
# ---------------------------------------------------------------------------


class TestEncryptedFieldDescriptor:
    def test_contribute_to_class_sets_descriptor_with_model_and_field_name(
        self,
    ) -> None:
        """After contribute_to_class, the descriptor must expose
        model_name and field_name.
        """
        from syntek_pyo3 import EncryptedField

        class FakeModel:
            pass

        field = EncryptedField()
        field.contribute_to_class(FakeModel, "email")

        descriptor = FakeModel.__dict__.get("email")
        assert descriptor is not None, (
            "EncryptedField did not set a descriptor on the model class"
        )
        assert descriptor.model_name == "FakeModel"
        assert descriptor.field_name == "email"

    def test_descriptor_is_instance_of_encrypted_field_descriptor(self) -> None:
        from syntek_pyo3 import EncryptedField, EncryptedFieldDescriptor

        class FakeModel:
            pass

        field = EncryptedField()
        field.contribute_to_class(FakeModel, "phone")

        descriptor = FakeModel.__dict__.get("phone")
        assert isinstance(descriptor, EncryptedFieldDescriptor)
