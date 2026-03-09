"""US007 — Red phase: Python binding tests for the `syntek_pyo3` extension.

Tests that the native extension module exposes the correct Python API and that
each function behaves according to its acceptance criteria.

All tests FAIL during the red phase because `syntek_pyo3` currently registers
no Python symbols (empty `#[pymodule]`).  They will pass after the green phase.

Run after `maturin develop`:
    pytest tests/pyo3/test_pyo3_bindings.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# 32-byte test key (non-secret — tests only; never use predictable keys in production).
_KEY = bytes(range(32))


# ---------------------------------------------------------------------------
# AC1: All six symbols are importable from syntek_pyo3
# ---------------------------------------------------------------------------


class TestModuleImport:
    """The extension must export the six documented symbols on import."""

    def test_import_encrypt_field(self) -> None:
        from syntek_pyo3 import encrypt_field  # noqa: F401

    def test_import_decrypt_field(self) -> None:
        from syntek_pyo3 import decrypt_field  # noqa: F401

    def test_import_encrypt_fields_batch(self) -> None:
        from syntek_pyo3 import encrypt_fields_batch  # noqa: F401

    def test_import_decrypt_fields_batch(self) -> None:
        from syntek_pyo3 import decrypt_fields_batch  # noqa: F401

    def test_import_hash_password(self) -> None:
        from syntek_pyo3 import hash_password  # noqa: F401

    def test_import_verify_password(self) -> None:
        from syntek_pyo3 import verify_password  # noqa: F401

    def test_all_six_symbols_importable_at_once(self) -> None:
        from syntek_pyo3 import (  # noqa: F401
            decrypt_field,
            decrypt_fields_batch,
            encrypt_field,
            encrypt_fields_batch,
            hash_password,
            verify_password,
        )


# ---------------------------------------------------------------------------
# AC: encrypt_field
# ---------------------------------------------------------------------------


class TestEncryptField:
    def test_returns_non_empty_string(self) -> None:
        from syntek_pyo3 import encrypt_field

        result = encrypt_field("hello@example.com", _KEY, "User", "email")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_two_calls_produce_different_ciphertexts(self) -> None:
        """Each call generates a fresh random nonce."""
        from syntek_pyo3 import encrypt_field

        ct1 = encrypt_field("same plaintext", _KEY, "User", "email")
        ct2 = encrypt_field("same plaintext", _KEY, "User", "email")
        assert ct1 != ct2

    def test_invalid_key_length_raises(self) -> None:
        from syntek_pyo3 import encrypt_field

        with pytest.raises(Exception):
            encrypt_field("plaintext", b"too-short", "User", "email")


# ---------------------------------------------------------------------------
# AC: decrypt_field
# ---------------------------------------------------------------------------


class TestDecryptField:
    def test_roundtrip_recovers_original_plaintext(self) -> None:
        from syntek_pyo3 import decrypt_field, encrypt_field

        plaintext = "user@example.com"
        ct = encrypt_field(plaintext, _KEY, "User", "email")
        assert decrypt_field(ct, _KEY, "User", "email") == plaintext

    def test_unicode_plaintext_round_trips(self) -> None:
        from syntek_pyo3 import decrypt_field, encrypt_field

        plaintext = "héllo wörld — £50"
        ct = encrypt_field(plaintext, _KEY, "User", "name")
        assert decrypt_field(ct, _KEY, "User", "name") == plaintext

    def test_tampered_ciphertext_raises(self) -> None:
        from syntek_pyo3 import decrypt_field, encrypt_field

        ct = encrypt_field("secret", _KEY, "User", "email")
        corrupted = ct[:-1] + ("A" if ct[-1] != "A" else "B")
        with pytest.raises(Exception):
            decrypt_field(corrupted, _KEY, "User", "email")

    def test_invalid_base64_raises(self) -> None:
        from syntek_pyo3 import decrypt_field

        with pytest.raises(Exception):
            decrypt_field("not-valid-base64!!!", _KEY, "User", "email")

    def test_wrong_key_raises(self) -> None:
        from syntek_pyo3 import decrypt_field, encrypt_field

        ct = encrypt_field("secret", _KEY, "User", "email")
        with pytest.raises(Exception):
            decrypt_field(ct, bytes(32), "User", "email")

    def test_aad_model_mismatch_raises(self) -> None:
        """Ciphertext bound to 'User' is rejected when decrypted as 'Order'."""
        from syntek_pyo3 import decrypt_field, encrypt_field

        ct = encrypt_field("secret", _KEY, "User", "email")
        with pytest.raises(Exception):
            decrypt_field(ct, _KEY, "Order", "email")

    def test_aad_field_mismatch_raises(self) -> None:
        """Ciphertext bound to 'email' is rejected when decrypted as 'phone'."""
        from syntek_pyo3 import decrypt_field, encrypt_field

        ct = encrypt_field("secret", _KEY, "User", "email")
        with pytest.raises(Exception):
            decrypt_field(ct, _KEY, "User", "phone")

    def test_failure_raises_exception_not_returns_none(self) -> None:
        """On any failure an exception must be raised — no silent None return."""
        from syntek_pyo3 import decrypt_field

        with pytest.raises(Exception):
            decrypt_field("not-valid-base64!!!", _KEY, "User", "email")


# ---------------------------------------------------------------------------
# AC: encrypt_fields_batch
# ---------------------------------------------------------------------------


class TestEncryptFieldsBatch:
    def test_returns_list_of_correct_length(self) -> None:
        from syntek_pyo3 import encrypt_fields_batch

        fields = [("email", "hello@example.com"), ("phone", "+441234567890")]
        result = encrypt_fields_batch(fields, _KEY, "User")
        assert len(result) == 2

    def test_preserves_field_order(self) -> None:
        """The nth ciphertext corresponds to the nth input field."""
        from syntek_pyo3 import decrypt_field, encrypt_fields_batch

        fields = [("email", "a@example.com"), ("phone", "+441111111111")]
        ciphertexts = encrypt_fields_batch(fields, _KEY, "User")
        assert decrypt_field(ciphertexts[0], _KEY, "User", "email") == "a@example.com"
        assert decrypt_field(ciphertexts[1], _KEY, "User", "phone") == "+441111111111"

    def test_empty_input_returns_empty_list(self) -> None:
        from syntek_pyo3 import encrypt_fields_batch

        assert encrypt_fields_batch([], _KEY, "User") == []

    def test_invalid_key_raises(self) -> None:
        from syntek_pyo3 import encrypt_fields_batch

        with pytest.raises(Exception):
            encrypt_fields_batch([("email", "x@example.com")], b"bad", "User")


# ---------------------------------------------------------------------------
# AC: decrypt_fields_batch
# ---------------------------------------------------------------------------


class TestDecryptFieldsBatch:
    def test_roundtrip_recovers_all_plaintexts(self) -> None:
        from syntek_pyo3 import decrypt_fields_batch, encrypt_fields_batch

        originals = [("email", "hello@example.com"), ("phone", "+441234567890")]
        encrypted = encrypt_fields_batch(originals, _KEY, "User")
        pairs = [("email", encrypted[0]), ("phone", encrypted[1])]
        assert decrypt_fields_batch(pairs, _KEY, "User") == [
            "hello@example.com",
            "+441234567890",
        ]

    def test_one_tampered_field_raises_for_entire_batch(self) -> None:
        """Atomicity guarantee: one failure aborts the whole batch."""
        from syntek_pyo3 import decrypt_fields_batch, encrypt_fields_batch

        encrypted = encrypt_fields_batch([("email", "ok@example.com")], _KEY, "User")
        pairs = [("email", encrypted[0]), ("phone", "not-valid-base64!!!")]
        with pytest.raises(Exception):
            decrypt_fields_batch(pairs, _KEY, "User")

    def test_empty_input_returns_empty_list(self) -> None:
        from syntek_pyo3 import decrypt_fields_batch

        assert decrypt_fields_batch([], _KEY, "User") == []


# ---------------------------------------------------------------------------
# AC: hash_password / verify_password
# ---------------------------------------------------------------------------


class TestHashPassword:
    def test_returns_argon2id_phc_string(self) -> None:
        from syntek_pyo3 import hash_password

        result = hash_password("correct-horse-battery-staple")
        assert isinstance(result, str)
        assert result.startswith("$argon2id$")

    def test_empty_password_raises(self) -> None:
        from syntek_pyo3 import hash_password

        with pytest.raises(Exception):
            hash_password("")

    def test_two_calls_produce_different_hashes(self) -> None:
        """A fresh random salt is generated each call."""
        from syntek_pyo3 import hash_password

        assert hash_password("same-password") != hash_password("same-password")


class TestVerifyPassword:
    def test_correct_password_returns_true(self) -> None:
        from syntek_pyo3 import hash_password, verify_password

        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_wrong_password_returns_false(self) -> None:
        from syntek_pyo3 import hash_password, verify_password

        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_empty_candidate_returns_false(self) -> None:
        from syntek_pyo3 import hash_password, verify_password

        hashed = hash_password("some-password")
        assert verify_password("", hashed) is False
