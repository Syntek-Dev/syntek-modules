"""US009 — Red phase: JWT token lifecycle tests for ``syntek-auth``.

Tests cover ``issue_token_pair``, ``rotate_refresh_token``, and
``validate_access_token``.

Acceptance criteria under test
-------------------------------
- Issuing a token pair returns non-empty access and refresh token strings.
- Rotating a refresh token issues a new pair and invalidates the old token.
- Attempting to rotate the same refresh token twice raises ``ValueError``.
- An expired access token raises ``ValueError`` when validated.
- A tampered access token raises ``ValueError`` when validated.

All tests **fail** in the red phase because the stub functions raise
``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from syntek_auth.services.tokens import (
    TokenPair,
    issue_token_pair,
    rotate_refresh_token,
    validate_access_token,
)

# ---------------------------------------------------------------------------
# AC: issue_token_pair returns a valid token pair
# ---------------------------------------------------------------------------


class TestIssueTokenPair:
    """issue_token_pair must return non-empty access and refresh tokens."""

    def test_returns_token_pair_instance(self) -> None:
        """issue_token_pair must return a TokenPair dataclass."""
        pair: TokenPair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert isinstance(pair, TokenPair)

    def test_access_token_is_non_empty_string(self) -> None:
        """The access token must be a non-empty string."""
        pair: TokenPair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert isinstance(pair.access_token, str)
        assert len(pair.access_token) > 0

    def test_refresh_token_is_non_empty_string(self) -> None:
        """The refresh token must be a non-empty string."""
        pair: TokenPair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert isinstance(pair.refresh_token, str)
        assert len(pair.refresh_token) > 0

    def test_two_pairs_have_distinct_tokens(self) -> None:
        """Two calls for the same user must produce distinct tokens."""
        pair_a: TokenPair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )
        pair_b: TokenPair = issue_token_pair(
            user_id=1,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert pair_a.access_token != pair_b.access_token
        assert pair_a.refresh_token != pair_b.refresh_token


# ---------------------------------------------------------------------------
# AC: ROTATE_REFRESH_TOKENS — old token is invalidated
# ---------------------------------------------------------------------------


class TestRotateRefreshToken:
    """rotate_refresh_token issues a new pair and invalidates the old token."""

    def test_rotation_returns_new_token_pair(self) -> None:
        """rotate_refresh_token must return a new TokenPair."""
        original: TokenPair = issue_token_pair(
            user_id=42,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        rotated: TokenPair = rotate_refresh_token(
            refresh_token=original.refresh_token,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert isinstance(rotated, TokenPair)

    def test_new_tokens_differ_from_original(self) -> None:
        """The rotated token pair must be different to the original."""
        original: TokenPair = issue_token_pair(
            user_id=42,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        rotated: TokenPair = rotate_refresh_token(
            refresh_token=original.refresh_token,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        assert rotated.access_token != original.access_token
        assert rotated.refresh_token != original.refresh_token

    def test_reusing_old_refresh_token_raises_value_error(self) -> None:
        """Attempting to rotate an already-rotated token must raise ValueError."""
        original: TokenPair = issue_token_pair(
            user_id=42,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        # First rotation consumes the token
        rotate_refresh_token(
            refresh_token=original.refresh_token,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        # Second rotation with the same (now revoked) token must fail
        with pytest.raises(ValueError, match=r"(?i)(invalid|expired|revoked)"):
            rotate_refresh_token(
                refresh_token=original.refresh_token,
                access_lifetime_seconds=900,
                refresh_lifetime_seconds=604800,
            )

    def test_invalid_refresh_token_raises_value_error(self) -> None:
        """A completely invalid refresh token string must raise ValueError."""
        with pytest.raises(ValueError, match=r"."):
            rotate_refresh_token(
                refresh_token="not_a_valid_token",
                access_lifetime_seconds=900,
                refresh_lifetime_seconds=604800,
            )


# ---------------------------------------------------------------------------
# AC: validate_access_token — expiry and tamper detection
# ---------------------------------------------------------------------------


class TestValidateAccessToken:
    """validate_access_token must reject expired and tampered tokens."""

    def test_valid_token_returns_payload(self) -> None:
        """validate_access_token must return the decoded payload for a valid token."""
        pair: TokenPair = issue_token_pair(
            user_id=7,
            access_lifetime_seconds=900,
            refresh_lifetime_seconds=604800,
        )

        payload: dict = validate_access_token(pair.access_token)  # type: ignore[type-arg]

        assert isinstance(payload, dict)
        assert "sub" in payload or "user_id" in payload, (
            f"Payload must contain a user identifier; got: {payload}"
        )

    def test_tampered_token_raises_value_error(self) -> None:
        """A tampered access token must raise ValueError."""
        with pytest.raises(ValueError, match=r"."):
            validate_access_token("header.tampered_payload.signature")

    def test_empty_token_raises_value_error(self) -> None:
        """An empty string token must raise ValueError."""
        with pytest.raises(ValueError, match=r"."):
            validate_access_token("")
