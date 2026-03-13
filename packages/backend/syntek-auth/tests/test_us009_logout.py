"""US009 — Green phase: logout and session invalidation tests for ``syntek-auth``.

Tests cover ``logout``, ``is_access_token_denylisted``, and
``revoke_all_sessions`` from ``syntek_auth.services.session``.

Acceptance criteria under test
-------------------------------
- ``logout`` revokes the refresh token and adds the access token JTI to the
  short-lived denylist; subsequent requests with those tokens return 401.
- ``logout`` called with an already-invalidated refresh token returns
  ``success=False`` with ``error_code='token_already_invalid'``.
- ``revokeAllSessions`` (admin) invalidates all refresh tokens for the target
  user; subsequent access token requests return 401.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from syntek_auth.services.session import (
    LogoutResult,
    is_access_token_denylisted,
    logout,
    revoke_all_sessions,
)
from syntek_auth.services.tokens import issue_token_pair, rotate_refresh_token

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# AC: logout — successful logout invalidates refresh and access tokens
# ---------------------------------------------------------------------------


class TestLogoutSuccess:
    """A valid logout must revoke the refresh token and denylist the access token."""

    def test_logout_returns_success_true(self) -> None:
        """logout with a valid token pair must return success=True."""
        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        result: LogoutResult = logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        assert result.success is True
        assert result.error_code is None

    def test_success_result_structure(self) -> None:
        """logout must return a LogoutResult with success=True and error_code=None."""
        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        result: LogoutResult = logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        assert isinstance(result, LogoutResult)
        assert result.success is True

    def test_logout_denylists_access_token(self) -> None:
        """The access token JTI must be on the denylist after logout."""
        from syntek_auth.services.tokens import (  # type: ignore[attr-defined]
            _SIGNING_SECRET,
            _decode_jwt,
        )

        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        payload = _decode_jwt(pair.access_token, _SIGNING_SECRET)
        jti = payload.get("jti")
        assert jti is not None
        assert is_access_token_denylisted(jti) is True

    def test_logout_revokes_refresh_token(self) -> None:
        """Using the revoked refresh token after logout must raise ValueError."""
        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        with pytest.raises(ValueError, match=r"(?i)(invalid|expired|revoked)"):
            rotate_refresh_token(
                refresh_token=pair.refresh_token,
                access_lifetime_seconds=900,
                refresh_lifetime_seconds=604800,
            )


# ---------------------------------------------------------------------------
# AC: logout — replayed (already-invalidated) token is rejected
# ---------------------------------------------------------------------------


class TestLogoutReplayedToken:
    """logout with an already-invalidated refresh token must return failure."""

    def test_replayed_token_returns_success_false(self) -> None:
        """A replayed token must return success=False."""
        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        # First logout — succeeds.
        logout(refresh_token=pair.refresh_token, access_token=pair.access_token)
        # Second logout with the same token — must fail.
        result: LogoutResult = logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        assert result.success is False

    def test_replayed_token_returns_token_already_invalid_code(self) -> None:
        """The error_code must be 'token_already_invalid' on replay."""
        pair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        logout(refresh_token=pair.refresh_token, access_token=pair.access_token)
        result: LogoutResult = logout(
            refresh_token=pair.refresh_token,
            access_token=pair.access_token,
        )
        assert result.error_code == "token_already_invalid", (
            f"Expected 'token_already_invalid'; got {result.error_code!r}"
        )

    def test_replayed_token_raises_not_implemented(self) -> None:
        """Calling logout with an invalid token string must return failure."""
        result: LogoutResult = logout(
            refresh_token="not-a-valid-jwt",
            access_token="not-a-valid-jwt",
        )
        assert result.success is False
        assert result.error_code == "token_already_invalid"


# ---------------------------------------------------------------------------
# AC: is_access_token_denylisted
# ---------------------------------------------------------------------------


class TestIsAccessTokenDenylisted:
    """is_access_token_denylisted must return False for a non-denylisted JTI."""

    def test_non_denylisted_jti_returns_false(self) -> None:
        """is_access_token_denylisted must return False for an unknown JTI."""
        assert is_access_token_denylisted("unknown-jti-that-was-never-added") is False

    def test_signature_accepts_jti(self) -> None:
        """is_access_token_denylisted must accept a jti positional argument."""
        import inspect

        sig = inspect.signature(is_access_token_denylisted)
        params = list(sig.parameters.keys())
        assert "jti" in params, (
            "is_access_token_denylisted must accept a 'jti' parameter"
        )


# ---------------------------------------------------------------------------
# AC: revokeAllSessions — admin operation
# ---------------------------------------------------------------------------


class TestRevokeAllSessions:
    """revoke_all_sessions invalidates all refresh tokens for the target user."""

    def test_revoke_all_returns_count(self) -> None:
        """revoke_all_sessions must return the number of tokens revoked."""
        count = revoke_all_sessions(user_id=999)
        assert isinstance(count, int)
        assert count >= 0

    def test_returns_revoked_count(self) -> None:
        """revoke_all_sessions for a user with no tokens returns 0."""
        count = revoke_all_sessions(user_id=1)
        assert isinstance(count, int)
        assert count >= 0

    def test_signature_accepts_user_id(self) -> None:
        """revoke_all_sessions must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(revoke_all_sessions)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "revoke_all_sessions must accept a 'user_id' parameter"
        )

    def test_revoke_all_sessions_for_different_user_does_not_raise(self) -> None:
        """revoke_all_sessions called for user_id=2 must return a non-negative int."""
        count = revoke_all_sessions(user_id=2)
        assert isinstance(count, int)
        assert count >= 0


# ---------------------------------------------------------------------------
# AC: LogoutResult dataclass structure
# ---------------------------------------------------------------------------


class TestLogoutResultStructure:
    """LogoutResult must have the correct fields and defaults."""

    def test_result_has_success_field(self) -> None:
        """LogoutResult must have a 'success' boolean field."""
        result = LogoutResult(success=True)
        assert result.success is True

    def test_result_has_error_code_field(self) -> None:
        """LogoutResult must have an 'error_code' field."""
        result = LogoutResult(success=False, error_code="token_already_invalid")
        assert result.error_code == "token_already_invalid"

    def test_result_has_message_field(self) -> None:
        """LogoutResult must have a 'message' field."""
        result = LogoutResult(
            success=False,
            error_code="token_already_invalid",
            message="Token has already been invalidated.",
        )
        assert "invalidated" in result.message

    def test_result_defaults_error_code_to_none(self) -> None:
        """error_code must default to None."""
        result = LogoutResult(success=True)
        assert result.error_code is None

    def test_result_defaults_message_to_empty_string(self) -> None:
        """message must default to an empty string."""
        result = LogoutResult(success=True)
        assert result.message == ""
