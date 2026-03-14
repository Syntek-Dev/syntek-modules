"""US007 — Django EncryptedField model field tests.

Verifies the behaviour of `EncryptedField` and `EncryptedFieldDescriptor` as
described in US007.  The architecture boundary is the GraphQL layer:

  Write path: GraphQL middleware encrypts → resolver saves ciphertext → DB
  Read path:  DB returns ciphertext → resolver returns it → middleware decrypts

`EncryptedField` is therefore a *storage-and-validation type only*.  It never
encrypts on save or decrypts on load.  Its sole responsibility is:

  1. Accept versioned ciphertext (base64ct, decoded >= 30 bytes, version >= 1)
     on pre_save.
  2. Reject plaintext and unversioned ciphertexts with `ValidationError`.
  3. Return raw ciphertext from `from_db_value` — no decryption.
  4. Record model name and field name via the encrypted field registry so the
     GraphQL middleware can resolve the correct AAD without manual annotation.

Run with:
    pytest packages/backend/syntek-pyo3/tests/test_encrypted_field.py -v
"""

from __future__ import annotations

import base64
import struct

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Synthetic versioned ciphertext: version=1 (big-endian) + 28 zero-bytes = 30 bytes.
# This passes is_valid_ciphertext_format (>= 30 bytes, version != 0).
_VALID_CIPHERTEXT = base64.b64encode(struct.pack(">H", 1) + b"\x00" * 28).decode()

# TEST KEY ONLY — NOT FOR PRODUCTION USE.  Generate from a CSPRNG in production.
_TEST_KEY = bytes(range(32))

# Values that look like plaintext or unversioned blobs — all must be rejected.
_PLAINTEXT_VALUES = [
    "hello@example.com",
    "plaintext value",
    "short",
    "not-base64!!!",
    "",
    " ",
    # Unversioned-layout blob: 28 bytes all zeros → version = 0x0000 = 0 (reserved)
    base64.b64encode(b"\x00" * 28).decode(),
]


# ---------------------------------------------------------------------------
# AC1: EncryptedField and EncryptedFieldDescriptor are importable from syntek_pyo3
# ---------------------------------------------------------------------------


class TestEncryptedFieldImport:
    def test_encrypted_field_importable(self) -> None:
        from syntek_pyo3 import EncryptedField  # noqa: F401

    def test_encrypted_field_descriptor_importable(self) -> None:
        from syntek_pyo3 import EncryptedFieldDescriptor  # noqa: F401

    def test_key_ring_importable(self) -> None:
        from syntek_pyo3 import KeyRing  # noqa: F401


# ---------------------------------------------------------------------------
# AC2: EncryptedField accepts a valid versioned ciphertext without raising
# ---------------------------------------------------------------------------


class TestEncryptedFieldAcceptsCiphertext:
    def test_valid_ciphertext_fixture_passes_validation(self) -> None:
        """Synthetic versioned ciphertext (version=1, >= 30 bytes) passes."""
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.validate(_VALID_CIPHERTEXT, model_instance=None)

    def test_real_ciphertext_from_encrypt_field_passes(self) -> None:
        """Ciphertext produced by encrypt_field (versioned API) passes validation."""
        from syntek_pyo3 import EncryptedField, KeyRing, encrypt_field

        ring = KeyRing()
        ring.add(1, _TEST_KEY)
        ct = encrypt_field("hello@example.com", ring, "User", "email")
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
# AC3: EncryptedField rejects plaintext and unversioned blobs
# ---------------------------------------------------------------------------


class TestEncryptedFieldRejectsPlaintext:
    @pytest.mark.parametrize("bad_value", _PLAINTEXT_VALUES)
    def test_validate_raises_validation_error_for_bad_values(
        self, bad_value: str
    ) -> None:
        """validate() raises ValidationError for plaintext and unversioned blobs."""
        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        with pytest.raises(ValidationError):
            field.validate(bad_value, model_instance=None)

    @pytest.mark.parametrize("bad_value", _PLAINTEXT_VALUES)
    def test_pre_save_raises_validation_error_for_bad_values(
        self, bad_value: str
    ) -> None:
        """pre_save() raises ValidationError — bad values must never reach the DB."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = bad_value
        with pytest.raises(ValidationError):
            field.pre_save(instance, add=False)


# ---------------------------------------------------------------------------
# C2 fix: unversioned ciphertext format is explicitly rejected
# ---------------------------------------------------------------------------


class TestCrossFormatRejection:
    def test_unversioned_blob_version_zero_fails_validate(self) -> None:
        """A 28-byte zero blob (unversioned layout, version=0) must fail validation.

        This confirms the format check explicitly rejects unversioned ciphertexts
        whose first 2 bytes happen to encode version 0.
        """
        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        unversioned_blob = base64.b64encode(b"\x00" * 28).decode()
        field = EncryptedField()
        with pytest.raises(ValidationError):
            field.validate(unversioned_blob, model_instance=None)

    def test_versioned_ciphertext_round_trip(self) -> None:
        """A ciphertext produced by encrypt_field decrypts correctly via decrypt_field."""
        from syntek_pyo3 import KeyRing, decrypt_field, encrypt_field

        ring = KeyRing()
        ring.add(1, _TEST_KEY)
        ct = encrypt_field("secret@example.com", ring, "User", "email")
        pt = decrypt_field(ct, ring, "User", "email")
        assert pt == "secret@example.com"

    def test_wrong_aad_fails_decryption(self) -> None:
        """A ciphertext encrypted for User.email must not decrypt for User.phone."""
        from syntek_pyo3 import DecryptionError, KeyRing, decrypt_field, encrypt_field

        ring = KeyRing()
        ring.add(1, _TEST_KEY)
        ct = encrypt_field("secret", ring, "User", "email")
        with pytest.raises(DecryptionError):
            decrypt_field(ct, ring, "User", "phone")


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
        """Decryption is the GraphQL middleware's job — from_db_value must not decrypt."""
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
    def test_contribute_to_class_registers_in_registry(self) -> None:
        """After contribute_to_class, (model_name, field_name) is in the registry."""
        from syntek_pyo3 import EncryptedField, get_encrypted_field_registry

        class FakeModel:
            pass

        field = EncryptedField()
        field.contribute_to_class(FakeModel, "email")

        registry = get_encrypted_field_registry()
        assert ("FakeModel", "email") in registry

    def test_field_object_not_overwritten_on_class(self) -> None:
        """contribute_to_class must not replace the field on the model class."""
        from syntek_pyo3 import EncryptedField

        class FakeModel:
            pass

        field = EncryptedField()
        FakeModel.email = field  # type: ignore[attr-defined]
        field.contribute_to_class(FakeModel, "email")

        # The original EncryptedField instance must still be on the class.
        assert isinstance(FakeModel.email, EncryptedField)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# KeyRing: basic Python-level sanity checks
# ---------------------------------------------------------------------------


class TestKeyRing:
    def test_empty_ring_is_empty(self) -> None:
        from syntek_pyo3 import KeyRing

        ring = KeyRing()
        assert ring.is_empty()
        assert len(ring) == 0

    def test_add_key_increases_length(self) -> None:
        from syntek_pyo3 import KeyRing

        ring = KeyRing()
        ring.add(1, _TEST_KEY)
        assert not ring.is_empty()
        assert len(ring) == 1

    def test_version_zero_rejected(self) -> None:
        from syntek_pyo3 import KeyRing

        ring = KeyRing()
        with pytest.raises(ValueError, match="version"):
            ring.add(0, _TEST_KEY)

    def test_duplicate_version_rejected(self) -> None:
        from syntek_pyo3 import KeyRing

        ring = KeyRing()
        ring.add(1, _TEST_KEY)
        with pytest.raises(ValueError, match="already"):
            ring.add(1, _TEST_KEY)

    def test_wrong_key_length_rejected(self) -> None:
        from syntek_pyo3 import KeyRing

        ring = KeyRing()
        with pytest.raises(ValueError, match="32 bytes"):
            ring.add(1, b"\x00" * 16)  # 16 bytes, not 32

    def test_nullable_field_pre_save_returns_none(self) -> None:
        """EncryptedField(null=True) returns None from pre_save when value is None."""
        from unittest.mock import MagicMock

        from syntek_pyo3 import EncryptedField

        field = EncryptedField(null=True, blank=True)
        field.attname = "email"
        instance = MagicMock()
        instance.email = None
        assert field.pre_save(instance, add=False) is None

    def test_non_nullable_field_pre_save_raises_for_none(self) -> None:
        """EncryptedField() (non-nullable) raises ValidationError for None."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = None
        with pytest.raises(ValidationError):
            field.pre_save(instance, add=False)
