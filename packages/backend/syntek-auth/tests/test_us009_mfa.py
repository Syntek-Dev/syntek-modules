"""US009 — Red phase: MFA gating and session state tests for ``syntek-auth``.

Tests cover ``enabled_mfa_methods``, ``resolve_session_state``, and
``oidc_amr_satisfies_mfa``.

Acceptance criteria under test
-------------------------------
- Only MFA methods listed in ``MFA_METHODS`` are returned by ``enabled_mfa_methods``.
- When ``MFA_REQUIRED=True`` and the user has no MFA configured, the session
  state has ``full_session=False`` and ``mfa_setup_required=True``.
- When ``MFA_REQUIRED=True`` and the user has MFA configured, a full session is
  issued.
- When ``MFA_REQUIRED=False``, a full session is always issued.
- An OIDC ``amr`` claim containing ``'mfa'`` satisfies the MFA requirement.
- An absent or empty ``amr`` claim does not satisfy the MFA requirement.

All tests **fail** in the red phase because the stub functions raise
``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from syntek_auth.services.mfa import (
    MfaSessionState,
    enabled_mfa_methods,
    oidc_amr_satisfies_mfa,
    resolve_session_state,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# AC: enabled_mfa_methods — gating by MFA_METHODS list
# ---------------------------------------------------------------------------


class TestEnabledMfaMethods:
    """Only configured methods are offered to users."""

    def test_totp_only_returns_totp(self) -> None:
        """When MFA_METHODS=['totp'], only 'totp' is returned."""
        methods = enabled_mfa_methods(["totp"])
        assert methods == ["totp"]

    def test_totp_and_passkey_returns_both(self) -> None:
        """When both 'totp' and 'passkey' are configured, both are returned."""
        methods = enabled_mfa_methods(["totp", "passkey"])
        assert set(methods) == {"totp", "passkey"}

    def test_sms_not_in_methods_when_not_configured(self) -> None:
        """When 'sms' is not in MFA_METHODS, it must not appear in the result."""
        methods = enabled_mfa_methods(["totp"])
        assert "sms" not in methods

    def test_all_four_methods_returned_when_all_configured(self) -> None:
        """All four methods are returned when all are configured."""
        methods = enabled_mfa_methods(["totp", "sms", "email_otp", "passkey"])
        assert set(methods) == {"totp", "sms", "email_otp", "passkey"}

    def test_order_is_canonical(self) -> None:
        """Methods are returned in canonical order: totp, sms, email_otp, passkey."""
        methods = enabled_mfa_methods(["passkey", "email_otp", "sms", "totp"])
        assert methods == ["totp", "sms", "email_otp", "passkey"]

    def test_unrecognised_method_is_excluded(self) -> None:
        """An unrecognised identifier must not appear in the returned list."""
        methods = enabled_mfa_methods(["totp", "carrier_pigeon"])
        assert "carrier_pigeon" not in methods
        assert "totp" in methods


# ---------------------------------------------------------------------------
# AC: resolve_session_state — MFA_REQUIRED enforcement
# ---------------------------------------------------------------------------


class TestResolveSessionState:
    """Session state depends on MFA_REQUIRED and whether MFA is configured."""

    def test_mfa_required_and_not_configured_issues_partial_session(self) -> None:
        """When MFA_REQUIRED=True and user has no MFA, a partial session is issued."""
        state: MfaSessionState = resolve_session_state(
            user_has_mfa_configured=False,
            mfa_required=True,
        )

        assert state.full_session is False
        assert state.mfa_setup_required is True

    def test_mfa_required_and_configured_issues_full_session(self) -> None:
        """When MFA_REQUIRED=True and user has MFA configured, a full session is issued."""
        state: MfaSessionState = resolve_session_state(
            user_has_mfa_configured=True,
            mfa_required=True,
        )

        assert state.full_session is True
        assert state.mfa_setup_required is False

    def test_mfa_not_required_always_issues_full_session(self) -> None:
        """When MFA_REQUIRED=False, a full session is issued regardless of MFA status."""
        state: MfaSessionState = resolve_session_state(
            user_has_mfa_configured=False,
            mfa_required=False,
        )

        assert state.full_session is True
        assert state.mfa_setup_required is False

    def test_mfa_not_required_with_mfa_configured_issues_full_session(self) -> None:
        """When MFA_REQUIRED=False and user has MFA, a full session is still issued."""
        state: MfaSessionState = resolve_session_state(
            user_has_mfa_configured=True,
            mfa_required=False,
        )

        assert state.full_session is True


# ---------------------------------------------------------------------------
# AC: oidc_amr_satisfies_mfa — OIDC amr claim check
# ---------------------------------------------------------------------------


class TestOidcAmrSatisfiesMfa:
    """OIDC amr claim must contain 'mfa' to satisfy MFA_REQUIRED."""

    def test_amr_with_mfa_value_returns_true(self) -> None:
        """An amr claim containing 'mfa' must satisfy the requirement."""
        assert oidc_amr_satisfies_mfa(["mfa"]) is True

    def test_amr_with_mfa_and_other_values_returns_true(self) -> None:
        """An amr claim with 'mfa' among other values must satisfy the requirement."""
        assert oidc_amr_satisfies_mfa(["pwd", "mfa"]) is True

    def test_amr_without_mfa_returns_false(self) -> None:
        """An amr claim that does not contain 'mfa' must not satisfy the requirement."""
        assert oidc_amr_satisfies_mfa(["pwd"]) is False

    def test_empty_amr_returns_false(self) -> None:
        """An empty amr claim must not satisfy the requirement."""
        assert oidc_amr_satisfies_mfa([]) is False

    def test_none_amr_returns_false(self) -> None:
        """A None amr claim (missing claim) must not satisfy the requirement."""
        assert oidc_amr_satisfies_mfa(None) is False

    def test_amr_with_otp_and_pwd_returns_true(self) -> None:
        """The combination ['otp', 'pwd'] is treated as MFA-compliant."""
        assert oidc_amr_satisfies_mfa(["otp", "pwd"]) is True
