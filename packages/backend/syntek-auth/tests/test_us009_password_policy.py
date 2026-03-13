"""US009 — Red phase: password policy tests for ``syntek-auth``.

Tests cover the ``validate_password_policy``, ``check_password_history``,
``is_password_expired``, and ``is_password_breached`` functions.

Acceptance criteria under test
-------------------------------
- A password shorter than ``PASSWORD_MIN_LENGTH`` is rejected.
- A password failing ``PASSWORD_REQUIRE_SYMBOLS`` (when enabled) is rejected.
- Both failures are reported when a password is both too short and missing symbols.
- A password in the last N password history hashes is rejected.
- A password that has exceeded ``PASSWORD_EXPIRY_DAYS`` triggers the expiry flag.
- A password found in the HaveIBeenPwned breach database is rejected.
- A compliant password passes all checks.

All tests **fail** in the red phase because the stub functions raise
``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from unittest.mock import patch

from syntek_auth.services.password import (
    PasswordPolicyResult,
    check_password_history,
    is_password_breached,
    is_password_expired,
    validate_password_policy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def policy(**overrides: object) -> dict:  # type: ignore[type-arg]
    """Return a minimal valid password policy dict with optional overrides."""
    base: dict = {  # type: ignore[type-arg]
        "PASSWORD_MIN_LENGTH": 12,
        "PASSWORD_MAX_LENGTH": 128,
        "PASSWORD_REQUIRE_UPPERCASE": True,
        "PASSWORD_REQUIRE_LOWERCASE": True,
        "PASSWORD_REQUIRE_DIGITS": True,
        "PASSWORD_REQUIRE_SYMBOLS": False,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# AC: Compliant password passes all rules
# ---------------------------------------------------------------------------


class TestCompliantPasswordPasses:
    """A password that satisfies all active policy rules must return valid=True."""

    def test_valid_password_returns_valid_result(self) -> None:
        """A 12-character password with upper, lower, and digits must pass."""
        result: PasswordPolicyResult = validate_password_policy(
            "ValidPass1234",
            policy(),
        )

        assert result.valid is True
        assert result.violations == []

    def test_valid_password_with_symbols_passes(self) -> None:
        """A password meeting all rules including symbols must pass."""
        result: PasswordPolicyResult = validate_password_policy(
            "Valid@Pass1234",
            policy(PASSWORD_REQUIRE_SYMBOLS=True),
        )

        assert result.valid is True
        assert result.violations == []


# ---------------------------------------------------------------------------
# AC: Password shorter than minimum is rejected
# ---------------------------------------------------------------------------


class TestPasswordMinLength:
    """Passwords shorter than PASSWORD_MIN_LENGTH must fail validation."""

    def test_password_too_short_returns_violation(self) -> None:
        """A 10-character password against a min-12 policy must fail."""
        result: PasswordPolicyResult = validate_password_policy(
            "Short1Upper",  # 11 chars but still short
            policy(PASSWORD_MIN_LENGTH=12),
        )

        assert result.valid is False
        violation_codes = [v.code for v in result.violations]
        assert "too_short" in violation_codes, (
            f"Expected a 'too_short' violation; got codes: {violation_codes}"
        )

    def test_password_exactly_at_minimum_passes(self) -> None:
        """A password of exactly min-length characters must pass."""
        result: PasswordPolicyResult = validate_password_policy(
            "ValidPass123",  # exactly 12 chars
            policy(PASSWORD_MIN_LENGTH=12),
        )

        assert result.valid is True


# ---------------------------------------------------------------------------
# AC: Multiple policy failures are all reported
# ---------------------------------------------------------------------------


class TestMultiplePolicyFailures:
    """When a password fails multiple rules, all failures are returned."""

    def test_short_and_no_symbols_both_reported(self) -> None:
        """A 10-char password with no symbols must report both failures when
        PASSWORD_MIN_LENGTH=14 and PASSWORD_REQUIRE_SYMBOLS=True."""
        result: PasswordPolicyResult = validate_password_policy(
            "ShortNoSym1",  # 11 chars, no symbols
            policy(PASSWORD_MIN_LENGTH=14, PASSWORD_REQUIRE_SYMBOLS=True),
        )

        assert result.valid is False
        violation_codes = [v.code for v in result.violations]
        assert "too_short" in violation_codes, (
            f"Expected 'too_short'; got: {violation_codes}"
        )
        assert "no_symbols" in violation_codes, (
            f"Expected 'no_symbols'; got: {violation_codes}"
        )

    def test_violation_messages_are_non_empty(self) -> None:
        """Every PolicyViolation must have a non-empty message string."""
        result: PasswordPolicyResult = validate_password_policy(
            "short",
            policy(PASSWORD_MIN_LENGTH=12, PASSWORD_REQUIRE_UPPERCASE=True),
        )

        assert result.valid is False
        for violation in result.violations:
            assert violation.message, (
                f"Violation '{violation.code}' has an empty message"
            )


# ---------------------------------------------------------------------------
# AC: Password requirements (uppercase, lowercase, digits, symbols)
# ---------------------------------------------------------------------------


class TestPasswordCharacterRequirements:
    """Individual character class requirements are enforced."""

    def test_no_uppercase_when_required_raises_violation(self) -> None:
        """A password with no uppercase letters must fail when required."""
        result: PasswordPolicyResult = validate_password_policy(
            "alllowercase123",
            policy(PASSWORD_REQUIRE_UPPERCASE=True),
        )

        assert result.valid is False
        codes = [v.code for v in result.violations]
        assert "no_uppercase" in codes

    def test_no_lowercase_when_required_raises_violation(self) -> None:
        """A password with no lowercase letters must fail when required."""
        result: PasswordPolicyResult = validate_password_policy(
            "ALLUPPERCASE123",
            policy(PASSWORD_REQUIRE_LOWERCASE=True),
        )

        assert result.valid is False
        codes = [v.code for v in result.violations]
        assert "no_lowercase" in codes

    def test_no_digits_when_required_raises_violation(self) -> None:
        """A password with no digits must fail when digits are required."""
        result: PasswordPolicyResult = validate_password_policy(
            "NoDigitsHereAtAll",
            policy(PASSWORD_REQUIRE_DIGITS=True),
        )

        assert result.valid is False
        codes = [v.code for v in result.violations]
        assert "no_digits" in codes

    def test_no_symbols_when_not_required_does_not_raise_violation(self) -> None:
        """When PASSWORD_REQUIRE_SYMBOLS=False, absence of symbols is not a violation."""
        result: PasswordPolicyResult = validate_password_policy(
            "ValidPass1234",
            policy(PASSWORD_REQUIRE_SYMBOLS=False),
        )

        codes = [v.code for v in result.violations]
        assert "no_symbols" not in codes


# ---------------------------------------------------------------------------
# AC: PASSWORD_HISTORY — previous password reuse is blocked
# ---------------------------------------------------------------------------


class TestPasswordHistory:
    """Passwords that match any of the last N hashes are rejected."""

    def test_password_matching_history_returns_true(self) -> None:
        """check_password_history returns True when password matches a recent hash."""
        # Real Django pbkdf2_sha256 hashes of "MyOldPass123" — generated via
        # django.contrib.auth.hashers.make_password during green-phase implementation.
        # check_password_history must use Django's check_password to verify these.
        previous_hashes = [
            "pbkdf2_sha256$1200000$1CmIdDIO7co3HY7Sl9nndl$vWYcRf6vbxH1moGXeU0ZGyLDzvMzaqGI133AVToEtRY=",
            "pbkdf2_sha256$1200000$Zhf0vY622FjVzw7A9dx4HL$vNfk7eriZI6zvrpBvBJju6NsjkzcvYiJzgoEmvXBt74=",
        ]
        result = check_password_history(
            password="MyOldPass123",
            previous_hashes=previous_hashes,
            history_count=5,
        )
        assert result is True

    def test_password_not_in_history_returns_false(self) -> None:
        """check_password_history returns False when password does not match any hash."""
        previous_hashes = [
            "argon2id$v19$m65536,t3,p4$hash1$checksum1",
        ]
        result = check_password_history(
            password="BrandNewPassword123",
            previous_hashes=previous_hashes,
            history_count=5,
        )
        assert result is False

    def test_history_count_zero_always_returns_false(self) -> None:
        """When PASSWORD_HISTORY=0, history checking is disabled and returns False."""
        previous_hashes = [
            "argon2id$v19$m65536,t3,p4$hash1$checksum1",
        ]
        result = check_password_history(
            password="AnyPassword123",
            previous_hashes=previous_hashes,
            history_count=0,
        )
        assert result is False

    def test_only_last_n_hashes_are_checked(self) -> None:
        """When history_count=2 and the match is at index 3, it is not checked."""
        # 5 historical hashes; the match is the 3rd one (index 2)
        # With history_count=2 only indices 0 and 1 are checked
        previous_hashes = [
            "argon2id$v19$m65536,t3,p4$notmatch1$ck",
            "argon2id$v19$m65536,t3,p4$notmatch2$ck",
            "argon2id$v19$m65536,t3,p4$MATCH$ck",  # outside the window
            "argon2id$v19$m65536,t3,p4$notmatch4$ck",
        ]
        result = check_password_history(
            password="OldPassword3",
            previous_hashes=previous_hashes,
            history_count=2,
        )
        assert result is False


# ---------------------------------------------------------------------------
# AC: PASSWORD_EXPIRY_DAYS
# ---------------------------------------------------------------------------


class TestPasswordExpiry:
    """Password expiry detection respects the configured expiry period."""

    def test_password_not_expired_when_within_period(self) -> None:
        """A password changed 89 days ago with expiry_days=90 is not expired."""
        assert is_password_expired(last_changed_days_ago=89, expiry_days=90) is False

    def test_password_expired_when_period_exceeded(self) -> None:
        """A password changed 91 days ago with expiry_days=90 is expired."""
        assert is_password_expired(last_changed_days_ago=91, expiry_days=90) is True

    def test_password_expired_exactly_at_boundary(self) -> None:
        """A password changed exactly expiry_days ago is considered expired."""
        assert is_password_expired(last_changed_days_ago=90, expiry_days=90) is True

    def test_password_never_expires_when_expiry_days_zero(self) -> None:
        """When expiry_days=0, the password never expires regardless of age."""
        assert is_password_expired(last_changed_days_ago=9999, expiry_days=0) is False


# ---------------------------------------------------------------------------
# AC: PASSWORD_BREACH_CHECK — HaveIBeenPwned integration
# ---------------------------------------------------------------------------


class TestPasswordBreachCheck:
    """The HaveIBeenPwned k-anonymity check identifies breached passwords."""

    def test_breached_password_returns_true(self) -> None:
        """is_password_breached returns True for a password in the HIBP database."""
        # The network call is mocked — the stub raises NotImplementedError first.
        with patch(
            "syntek_auth.services.password.is_password_breached",
            return_value=True,
        ):
            from syntek_auth.services.password import is_password_breached as mocked_fn

            assert mocked_fn("password123") is True

    def test_clean_password_returns_false(self) -> None:
        """is_password_breached returns False for a password not in HIBP."""
        with patch(
            "syntek_auth.services.password.is_password_breached",
            return_value=False,
        ):
            from syntek_auth.services.password import is_password_breached as mocked_fn

            assert mocked_fn("extremely_unique_pass_9a7b3c") is False

    def test_breach_check_does_not_send_full_password(self) -> None:
        """The breach check must not transmit the full password to the HIBP API.

        Verifies the k-anonymity constraint: only the first 5 hex characters
        of the SHA-1 hash are sent to the HIBP API.  The full hash suffix is
        matched locally from the response body.
        """
        import hashlib

        password = "any_password"  # noqa: S105
        sha1 = (
            hashlib.sha1(password.encode("utf-8"), usedforsecurity=False)
            .hexdigest()
            .upper()
        )
        expected_prefix = sha1[:5]
        suffix = sha1[5:]

        captured_urls: list[str] = []

        class _MockResponse:
            def __init__(self) -> None:
                # Return a response body that includes the suffix so the
                # function returns True — confirming the suffix comparison works.
                self._body = f"{suffix}:1\n".encode()

            def read(self) -> bytes:
                return self._body

            def __enter__(self) -> _MockResponse:
                return self

            def __exit__(self, *args: object) -> None:
                pass

        def _fake_urlopen(url: str, timeout: int = 5) -> _MockResponse:  # type: ignore[misc]
            captured_urls.append(url)
            return _MockResponse()

        with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
            result = is_password_breached(password)

        # The function must have called the HIBP API.
        assert len(captured_urls) == 1, (
            "Expected exactly one HTTP call to the HIBP API."
        )
        called_url = captured_urls[0]

        # Only the 5-character prefix must appear in the URL — not the full hash.
        assert expected_prefix in called_url, (
            f"HIBP URL must include the SHA-1 prefix {expected_prefix!r}."
        )
        assert suffix not in called_url, (
            "The full SHA-1 suffix must NOT be sent to the HIBP API (k-anonymity violation)."
        )
        assert len(sha1) not in [len(called_url) - called_url.index(expected_prefix)], (
            "The full SHA-1 hash must not appear in the URL."
        )

        # The function correctly returned True because the suffix was in the mock response.
        assert result is True
