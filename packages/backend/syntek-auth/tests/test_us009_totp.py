"""US009 — TOTP service tests for ``syntek-auth``.

Tests cover the full TOTP implementation in ``syntek_auth.services.totp``:

- RFC 4226 HOTP computation (``_hotp``)
- RFC 6238 TOTP derivation at a fixed timestamp (``_totp_at``)
- Secret generation (``generate_totp_secret``)
- Provisioning URI construction (``build_provisioning_uri``)
- TOTP code verification with window tolerance (``verify_totp_code``)
- Backup code generation (``generate_backup_codes``)
- Backup code storage and consumption (``store_backup_codes``, ``consume_backup_code``)
- Full TOTP enable flow (``enable_totp_for_user``)

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import base64
import time

import pyotp
import pytest
from freezegun import freeze_time
from syntek_auth.services.totp import (
    TotpSetupData,
    _hotp,
    _totp_at,
    build_provisioning_uri,
    consume_backup_code,
    enable_totp_for_user,
    generate_backup_codes,
    generate_totp_secret,
    store_backup_codes,
    verify_totp_code,
)

pytestmark = [pytest.mark.unit, pytest.mark.slow]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_secret() -> str:
    """Return a valid, padded-free base32 secret for testing."""
    return generate_totp_secret()


def _pad_secret(secret: str) -> str:
    """Add base32 padding so pyotp can decode the secret."""
    return secret + "=" * ((8 - len(secret) % 8) % 8)


# ---------------------------------------------------------------------------
# _hotp — RFC 4226 HOTP computation
# ---------------------------------------------------------------------------


class TestHotp:
    """Tests for the internal ``_hotp`` function."""

    def test_hotp_returns_integer(self) -> None:
        """``_hotp`` must return an integer."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        result = _hotp(secret, 0)
        assert isinstance(result, int)

    def test_hotp_produces_six_digit_range(self) -> None:
        """The HOTP result must be in [0, 999999] (six-digit range)."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        for counter in range(10):
            result = _hotp(secret, counter)
            assert 0 <= result < 1_000_000

    def test_hotp_deterministic_for_same_inputs(self) -> None:
        """The same key + counter must always produce the same HOTP value."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        assert _hotp(secret, 5) == _hotp(secret, 5)

    def test_hotp_differs_for_different_counters(self) -> None:
        """Different counters must (in general) produce different HOTP values."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        # Statistically almost impossible to collide across consecutive counters
        values = {_hotp(secret, c) for c in range(20)}
        assert len(values) > 1

    def test_hotp_rfc4226_test_vector_counter_0(self) -> None:
        """RFC 4226 Appendix D test vector: secret=12345678901234567890, counter=0 → 755224."""
        # RFC 4226 uses the ASCII bytes of "12345678901234567890"
        key = b"12345678901234567890"
        assert _hotp(key, 0) == 755224

    def test_hotp_rfc4226_test_vector_counter_1(self) -> None:
        """RFC 4226 Appendix D test vector: secret=12345678901234567890, counter=1 → 287082."""
        key = b"12345678901234567890"
        assert _hotp(key, 1) == 287082

    def test_hotp_rfc4226_test_vector_counter_2(self) -> None:
        """RFC 4226 Appendix D test vector: counter=2 → 359152."""
        key = b"12345678901234567890"
        assert _hotp(key, 2) == 359152


# ---------------------------------------------------------------------------
# _totp_at — TOTP derivation at a fixed timestamp
# ---------------------------------------------------------------------------


class TestTotpAt:
    """Tests for the internal ``_totp_at`` function."""

    def test_totp_at_returns_string(self) -> None:
        """``_totp_at`` must return a string."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        assert isinstance(_totp_at(secret, 0), str)

    def test_totp_at_returns_six_characters(self) -> None:
        """The returned TOTP code must always be exactly 6 characters."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        assert len(_totp_at(secret, 1000000)) == 6

    def test_totp_at_is_zero_padded(self) -> None:
        """The code must be zero-padded to 6 digits when the value is small."""
        # Find a counter that produces a code < 100000 to confirm padding.
        secret = b"12345678901234567890"
        # Counter 7 gives 162583 → not small enough, but we can test padding
        # by constructing a scenario where _hotp returns a small value.
        # A safe approach: verify the string always matches r'^\d{6}$'.
        import re

        for ts in range(0, 180, 30):
            code = _totp_at(secret, ts)
            assert re.match(r"^\d{6}$", code), f"Expected 6-digit code, got {code!r}"

    def test_totp_at_agrees_with_pyotp(self) -> None:
        """``_totp_at`` must produce the same code as ``pyotp.TOTP.at()``."""
        raw_secret = generate_totp_secret()
        padded = _pad_secret(raw_secret)
        totp = pyotp.TOTP(padded)

        key_bytes = base64.b32decode(padded, casefold=True)
        frozen_ts = 1_700_000_000  # arbitrary fixed Unix timestamp

        our_code = _totp_at(key_bytes, frozen_ts)
        # pyotp.TOTP.at() accepts a Unix timestamp for the `for_time` arg
        pyotp_code = totp.at(frozen_ts)
        assert our_code == pyotp_code

    def test_totp_at_changes_across_time_steps(self) -> None:
        """Codes for timestamps 30 seconds apart (different steps) must differ."""
        secret = base64.b32decode("JBSWY3DPEHPK3PXP")
        code_step_0 = _totp_at(secret, 0)
        code_step_1 = _totp_at(secret, 30)
        # Different counters → almost certainly different codes
        assert code_step_0 != code_step_1


# ---------------------------------------------------------------------------
# generate_totp_secret
# ---------------------------------------------------------------------------


class TestGenerateTotpSecret:
    """Tests for ``generate_totp_secret``."""

    def test_returns_string(self) -> None:
        """The secret must be a string."""
        assert isinstance(generate_totp_secret(), str)

    def test_no_padding_characters(self) -> None:
        """The returned secret must not contain '=' padding characters."""
        assert "=" not in generate_totp_secret()

    def test_valid_base32(self) -> None:
        """The secret must be decodable as base32 after padding is restored."""
        secret = generate_totp_secret()
        padded = _pad_secret(secret)
        decoded = base64.b32decode(padded, casefold=True)
        assert len(decoded) == 20  # 160-bit secret

    def test_uniqueness(self) -> None:
        """Two successive calls must return different secrets."""
        assert generate_totp_secret() != generate_totp_secret()

    def test_minimum_length(self) -> None:
        """A 20-byte secret encodes to at least 32 base32 characters."""
        secret = generate_totp_secret()
        assert len(secret) >= 32


# ---------------------------------------------------------------------------
# build_provisioning_uri
# ---------------------------------------------------------------------------


class TestBuildProvisioningUri:
    """Tests for ``build_provisioning_uri``."""

    def test_starts_with_otpauth_scheme(self) -> None:
        """The URI must start with ``otpauth://totp/``."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        assert uri.startswith("otpauth://totp/")

    def test_contains_secret_parameter(self) -> None:
        """The URI must include the ``secret`` query parameter."""
        secret = "SECRETABC"  # noqa: S105
        uri = build_provisioning_uri(secret, "alice@example.com", "Syntek")
        assert f"secret={secret}" in uri

    def test_contains_issuer_parameter(self) -> None:
        """The URI must include the ``issuer`` query parameter."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        assert "issuer=Syntek" in uri

    def test_label_contains_account_name(self) -> None:
        """The URI label (path) must contain the percent-encoded account name."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        # The label is percent-encoded: "Syntek:alice@example.com"
        assert "alice%40example.com" in uri or "alice@example.com" in uri

    def test_contains_algorithm_sha1(self) -> None:
        """The URI must specify SHA1 as the algorithm."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        assert "algorithm=SHA1" in uri

    def test_contains_digits_6(self) -> None:
        """The URI must specify 6 digits."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        assert "digits=6" in uri

    def test_contains_period_30(self) -> None:
        """The URI must specify a 30-second period."""
        uri = build_provisioning_uri("SECRETABC", "alice@example.com", "Syntek")
        assert "period=30" in uri

    def test_pyotp_can_parse_uri(self) -> None:
        """The provisioning URI must be parseable by pyotp."""
        secret = generate_totp_secret()
        uri = build_provisioning_uri(secret, "test@example.com", "TestApp")
        parsed = pyotp.parse_uri(uri)
        assert isinstance(parsed, pyotp.TOTP)


# ---------------------------------------------------------------------------
# verify_totp_code
# ---------------------------------------------------------------------------


class TestVerifyTotpCode:
    """Tests for ``verify_totp_code``."""

    @freeze_time("2024-01-15 12:00:00")
    def test_valid_current_code_accepted(self) -> None:
        """A valid code for the current time window must be accepted."""
        secret = generate_totp_secret()
        padded = _pad_secret(secret)
        code = pyotp.TOTP(padded).now()
        assert verify_totp_code(secret, code) is True

    @freeze_time("2024-01-15 12:00:00")
    def test_valid_previous_window_code_accepted(self) -> None:
        """A valid code from the previous 30-second window must be accepted (±1 window)."""
        secret = generate_totp_secret()
        padded = _pad_secret(secret)
        # Previous window: subtract 30 seconds from current Unix time
        frozen_ts = int(time.time()) - 30
        code = pyotp.TOTP(padded).at(frozen_ts)
        assert verify_totp_code(secret, code) is True

    @freeze_time("2024-01-15 12:00:00")
    def test_valid_next_window_code_accepted(self) -> None:
        """A valid code from the next 30-second window must be accepted (±1 window)."""
        secret = generate_totp_secret()
        padded = _pad_secret(secret)
        frozen_ts = int(time.time()) + 30
        code = pyotp.TOTP(padded).at(frozen_ts)
        assert verify_totp_code(secret, code) is True

    def test_wrong_code_rejected(self) -> None:
        """A random 6-digit code that doesn't match must be rejected."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "000000") is False

    def test_non_digit_code_rejected(self) -> None:
        """A code containing non-digit characters must be rejected immediately."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "abc123") is False

    def test_short_code_rejected(self) -> None:
        """A code shorter than 6 digits must be rejected."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "12345") is False

    def test_long_code_rejected(self) -> None:
        """A code longer than 6 digits must be rejected."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "1234567") is False

    def test_empty_code_rejected(self) -> None:
        """An empty string must be rejected."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "") is False

    def test_whitespace_only_code_rejected(self) -> None:
        """A whitespace-only string must be rejected."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "      ") is False

    def test_invalid_base32_secret_rejected(self) -> None:
        """An invalid base32 secret must cause the function to return False, not raise."""
        assert verify_totp_code("!!!NOT_VALID_BASE32!!!", "123456") is False

    @freeze_time("2024-01-15 12:00:00")
    def test_code_with_leading_whitespace_accepted(self) -> None:
        """A code with surrounding whitespace must still be verified (strip applied)."""
        secret = generate_totp_secret()
        padded = _pad_secret(secret)
        code = pyotp.TOTP(padded).now()
        assert verify_totp_code(secret, f"  {code}  ") is True


# ---------------------------------------------------------------------------
# generate_backup_codes
# ---------------------------------------------------------------------------


class TestGenerateBackupCodes:
    """Tests for ``generate_backup_codes``."""

    def test_returns_list(self) -> None:
        """The result must be a list."""
        assert isinstance(generate_backup_codes(10), list)

    def test_correct_count(self) -> None:
        """The list must contain exactly the requested number of codes."""
        for count in (5, 8, 10):
            assert len(generate_backup_codes(count)) == count

    def test_each_code_is_eight_chars(self) -> None:
        """Each code must be exactly 8 characters long."""
        for code in generate_backup_codes(10):
            assert len(code) == 8

    def test_each_code_is_alphanumeric(self) -> None:
        """Each code must consist only of the allowed alphabet characters."""
        alphabet = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        for code in generate_backup_codes(20):
            for char in code:
                assert char in alphabet, (
                    f"Unexpected character {char!r} in code {code!r}"
                )

    def test_codes_are_unique(self) -> None:
        """Generated codes within one batch must all be unique."""
        codes = generate_backup_codes(20)
        assert len(set(codes)) == len(codes)

    def test_zero_codes(self) -> None:
        """Requesting zero codes must return an empty list."""
        assert generate_backup_codes(0) == []


# ---------------------------------------------------------------------------
# store_backup_codes + consume_backup_code (DB tests)
# ---------------------------------------------------------------------------


class TestStoreAndConsumeBackupCodes:
    """Tests for ``store_backup_codes`` and ``consume_backup_code``."""

    @pytest.mark.django_db
    def test_store_and_consume_single_code(self) -> None:
        """A stored backup code must be consumable exactly once."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        codes = generate_backup_codes(5)
        store_backup_codes(user.pk, codes)

        # Consuming the first code must succeed.
        assert consume_backup_code(user.pk, codes[0]) is True

    @pytest.mark.django_db
    def test_consumed_code_cannot_be_used_again(self) -> None:
        """After a backup code is consumed, a second attempt must return False."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        codes = generate_backup_codes(5)
        store_backup_codes(user.pk, codes)

        consume_backup_code(user.pk, codes[0])
        assert consume_backup_code(user.pk, codes[0]) is False

    @pytest.mark.django_db
    def test_wrong_code_returns_false(self) -> None:
        """Supplying a code not in the stored set must return False."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        codes = generate_backup_codes(5)
        store_backup_codes(user.pk, codes)

        assert consume_backup_code(user.pk, "XXXXXXXX") is False

    @pytest.mark.django_db
    def test_store_replaces_existing_codes(self) -> None:
        """Calling ``store_backup_codes`` twice must replace the old codes."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        first_batch = generate_backup_codes(5)
        store_backup_codes(user.pk, first_batch)

        second_batch = generate_backup_codes(5)
        store_backup_codes(user.pk, second_batch)

        # The old codes are deleted — they must no longer be consumable.
        assert consume_backup_code(user.pk, first_batch[0]) is False
        # The new codes must be consumable.
        assert consume_backup_code(user.pk, second_batch[0]) is True

    @pytest.mark.django_db
    def test_consume_code_for_wrong_user_returns_false(self) -> None:
        """Consuming a code under the wrong user_id must return False."""
        from syntek_auth.factories.user import UserFactory

        user_a = UserFactory.create()
        user_b = UserFactory.create()
        codes = generate_backup_codes(5)
        store_backup_codes(user_a.pk, codes)

        assert consume_backup_code(user_b.pk, codes[0]) is False

    @pytest.mark.django_db
    def test_consume_when_no_codes_stored_returns_false(self) -> None:
        """When no codes are stored for a user, consuming any code returns False."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        assert consume_backup_code(user.pk, "ABCD1234") is False

    @pytest.mark.django_db
    def test_all_codes_are_independently_consumable(self) -> None:
        """Each code in a batch must be individually consumable."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        codes = generate_backup_codes(4)
        store_backup_codes(user.pk, codes)

        for code in codes:
            assert consume_backup_code(user.pk, code) is True


# ---------------------------------------------------------------------------
# enable_totp_for_user (DB tests)
# ---------------------------------------------------------------------------


class TestEnableTotpForUser:
    """Tests for ``enable_totp_for_user``."""

    @pytest.mark.django_db
    def test_returns_totp_setup_data(self) -> None:
        """``enable_totp_for_user`` must return a ``TotpSetupData`` instance."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        result = enable_totp_for_user(user.pk, "Syntek", 8)
        assert isinstance(result, TotpSetupData)

    @pytest.mark.django_db
    def test_provisioning_uri_is_valid_otpauth(self) -> None:
        """The provisioning URI must start with ``otpauth://totp/``."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        result = enable_totp_for_user(user.pk, "Syntek", 8)
        assert result.provisioning_uri.startswith("otpauth://totp/")

    @pytest.mark.django_db
    def test_backup_codes_correct_count(self) -> None:
        """The returned backup codes list must have the requested length."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        result = enable_totp_for_user(user.pk, "Syntek", 10)
        assert len(result.backup_codes) == 10

    @pytest.mark.django_db
    def test_backup_codes_are_stored_and_consumable(self) -> None:
        """The backup codes returned must be stored and usable for recovery."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        result = enable_totp_for_user(user.pk, "Syntek", 5)

        # At least the first code must be consumable.
        assert consume_backup_code(user.pk, result.backup_codes[0]) is True

    @pytest.mark.django_db
    def test_issuer_appears_in_provisioning_uri(self) -> None:
        """The issuer name must be present in the provisioning URI."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        result = enable_totp_for_user(user.pk, "MyOrg", 5)
        assert "MyOrg" in result.provisioning_uri

    @pytest.mark.django_db
    def test_unknown_user_raises(self) -> None:
        """Supplying a non-existent user_id must raise ``DoesNotExist``."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        with pytest.raises(UserModel.DoesNotExist):
            enable_totp_for_user(999999, "Syntek", 5)

    @pytest.mark.django_db
    def test_totp_secret_stored_on_user_when_field_exists(self) -> None:
        """``totp_secret`` must be populated on the user model after setup."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        enable_totp_for_user(user.pk, "Syntek", 5)
        user.refresh_from_db()
        assert user.totp_secret
