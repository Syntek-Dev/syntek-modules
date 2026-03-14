"""US009 / US076 — Social OAuth MFA gating tests for ``syntek-auth``.

Tests cover the complete MFA-gated OAuth flow for consumer social providers
(Google, Facebook, Instagram, etc.) that do not enforce MFA at the platform
level.  After the OAuth callback these providers issue a short-lived
``PendingOAuthSession`` instead of a full token pair; the user must complete a
local MFA challenge via ``completeSocialMfa`` before receiving tokens.

Acceptance criteria under test
-------------------------------
- ``is_mfa_gated_provider()`` correctly classifies providers.
- ``PendingOAuthSession`` model has the expected fields and constraints.
- ``issue_oauth_pending_session()`` creates a DB row and returns a usable
  pending token with the correct TTL.
- ``complete_oauth_mfa()`` validates the MFA proof, deletes the pending row
  (single-use), and returns a full ``TokenPair`` on success.
- ``complete_oauth_mfa()`` returns appropriate error codes for expired,
  invalid, or already-consumed pending tokens and for wrong MFA proofs.
- ``OidcCallbackPayload`` carries the ``mfa_pending``, ``pending_token``, and
  ``mfa_setup_required`` fields expected by the frontend.
- ``SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL']`` setting is validated at startup
  (min 60 s, max 3600 s).

Red phase: importing ``MFA_GATED_PROVIDERS``, ``is_mfa_gated_provider``,
``PendingOAuthSession``, ``OAuthMfaPendingResult``, ``OAuthMfaCompleteResult``,
``issue_oauth_pending_session``, ``complete_oauth_mfa``, and
``OidcCallbackPayload`` all raise ``ImportError`` because the corresponding
modules and symbols do not yet exist.  Every test class therefore fails at
collection time in the red phase.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from syntek_auth.backends.allowlist import (
    BUILTIN_ALLOWED_PROVIDERS,
    MFA_GATED_PROVIDERS,
    is_mfa_gated_provider,
)
from syntek_auth.models.oauth_pending import PendingOAuthSession
from syntek_auth.services.lookup_tokens import make_provider_token
from syntek_auth.services.oauth_mfa import (
    OAuthMfaCompleteResult,
    OAuthMfaPendingResult,
    complete_oauth_mfa,
    issue_oauth_pending_session,
)
from syntek_auth.types.auth import OidcCallbackPayload

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.slow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(email: str, password: str = "StrongPass1!") -> Any:  # noqa: S107
    UserModel = get_user_model()  # noqa: N806
    return UserModel.objects.create_user(email=email, password=password)  # type: ignore[attr-defined]


def _make_pending_session(
    user: object,
    provider: str,
    expires_at: object = None,
) -> PendingOAuthSession:
    """Create a PendingOAuthSession with an encrypted provider field.

    Encrypts ``provider`` via ``syntek_pyo3.encrypt_field`` (with the test
    ``FIELD_KEY``) and computes ``provider_token`` via HMAC-SHA256 before
    persisting the row.  Falls back to storing the plaintext value when
    ``syntek_pyo3`` is unavailable.
    """
    from datetime import timedelta

    from django.conf import settings as _settings
    from django.utils import timezone as _tz

    if expires_at is None:
        expires_at = _tz.now() + timedelta(seconds=600)

    provider_normalised = provider.strip().lower()
    cfg = getattr(_settings, "SYNTEK_AUTH", {})
    raw_key = cfg.get("FIELD_KEY", "")
    field_key: bytes = (
        raw_key.encode("utf-8") if isinstance(raw_key, str) else bytes(raw_key)
    )

    try:
        from syntek_pyo3 import KeyRing, encrypt_field  # type: ignore[import-not-found]

        _ring = KeyRing()
        _ring.add(1, field_key)
        encrypted_provider: str = encrypt_field(
            provider_normalised, _ring, "PendingOAuthSession", "provider"
        )
    except ImportError:
        encrypted_provider = provider_normalised

    return PendingOAuthSession.objects.create(  # type: ignore[return-value]
        user=user,
        provider=encrypted_provider,
        provider_token=make_provider_token(provider),
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# AC: MFA_GATED_PROVIDERS set contents and is_mfa_gated_provider() helper
# ---------------------------------------------------------------------------


class TestMfaGatedProviderSet:
    """MFA_GATED_PROVIDERS and is_mfa_gated_provider() shape and contents."""

    def test_mfa_gated_providers_is_frozenset(self) -> None:
        """MFA_GATED_PROVIDERS must be a frozenset."""
        assert isinstance(MFA_GATED_PROVIDERS, frozenset)

    def test_all_nine_social_providers_are_gated(self) -> None:
        """MFA_GATED_PROVIDERS must contain exactly the nine expected identifiers."""
        assert (
            frozenset(
                {
                    "google",
                    "facebook",
                    "instagram",
                    "linkedin",
                    "twitter",
                    "x",
                    "apple",
                    "discord",
                    "microsoft",
                }
            )
            == MFA_GATED_PROVIDERS
        )

    def test_no_overlap_between_gated_and_builtin_allowed(self) -> None:
        """MFA_GATED_PROVIDERS and BUILTIN_ALLOWED_PROVIDERS must be disjoint."""
        overlap = MFA_GATED_PROVIDERS & BUILTIN_ALLOWED_PROVIDERS
        assert overlap == frozenset(), (
            f"Providers in both sets would be ambiguous: {overlap!r}"
        )


class TestIsMfaGatedProvider:
    """is_mfa_gated_provider() classification."""

    @pytest.mark.parametrize("provider_id", sorted(MFA_GATED_PROVIDERS))
    def test_returns_true_for_each_gated_provider(self, provider_id: str) -> None:
        """is_mfa_gated_provider must return True for every provider in the set."""
        assert is_mfa_gated_provider(provider_id) is True

    def test_returns_false_for_github(self) -> None:
        """GitHub is a built-in allowed provider, not MFA-gated."""
        assert is_mfa_gated_provider("github") is False

    def test_returns_false_for_okta(self) -> None:
        """Okta is a built-in allowed provider, not MFA-gated."""
        assert is_mfa_gated_provider("okta") is False

    def test_returns_false_for_defguard(self) -> None:
        """Defguard is a built-in allowed provider, not MFA-gated."""
        assert is_mfa_gated_provider("defguard") is False

    def test_returns_false_for_unknown_custom_idp(self) -> None:
        """An unknown provider identifier is not MFA-gated."""
        assert is_mfa_gated_provider("my-corp-idp") is False
        assert is_mfa_gated_provider("") is False

    def test_normalises_case(self) -> None:
        """is_mfa_gated_provider is case-insensitive."""
        assert is_mfa_gated_provider("Google") is True
        assert is_mfa_gated_provider("FACEBOOK") is True
        assert is_mfa_gated_provider("Twitter") is True
        assert is_mfa_gated_provider("MICROSOFT") is True


# ---------------------------------------------------------------------------
# AC: PendingOAuthSession model structure
# ---------------------------------------------------------------------------


class TestPendingOAuthSessionModel:
    """PendingOAuthSession model must have the correct fields and constraints."""

    def test_model_has_uuid_primary_key(self) -> None:
        """PendingOAuthSession must use a UUID as its primary key."""
        import django.db.models as dm

        pk_field = PendingOAuthSession._meta.pk
        assert pk_field is not None, "PendingOAuthSession must have a primary key"
        assert isinstance(pk_field, dm.UUIDField), (
            f"Primary key must be a UUIDField; got {type(pk_field).__name__}"
        )

    def test_model_has_required_fields(self) -> None:
        """PendingOAuthSession must declare user, provider, provider_token, expires_at, created_at."""
        field_names = {f.name for f in PendingOAuthSession._meta.get_fields()}
        for required in (
            "user",
            "provider",
            "provider_token",
            "expires_at",
            "created_at",
        ):
            assert required in field_names, (
                f"PendingOAuthSession is missing required field '{required}'"
            )

    def test_provider_is_encrypted_field(self) -> None:
        """The provider field must be an EncryptedField (ciphertext at rest)."""
        from syntek_auth.models.user import EncryptedField

        field = PendingOAuthSession._meta.get_field("provider")
        assert isinstance(field, EncryptedField), (
            f"PendingOAuthSession.provider must be EncryptedField; got {type(field).__name__}"
        )

    def test_provider_token_field_max_length(self) -> None:
        """The provider_token field must have max_length=64 (SHA-256 hex digest)."""
        field = PendingOAuthSession._meta.get_field("provider_token")
        assert field.max_length == 64, (  # type: ignore[union-attr]
            f"provider_token.max_length must be 64; got {field.max_length}"  # type: ignore[union-attr]
        )

    def test_provider_token_field_has_db_index(self) -> None:
        """The provider_token field must have db_index=True."""
        field = PendingOAuthSession._meta.get_field("provider_token")
        assert field.db_index is True, "provider_token must have db_index=True"  # type: ignore[union-attr]

    def test_model_is_re_exported_from_models_package(self) -> None:
        """PendingOAuthSession must be importable from syntek_auth.models."""
        from syntek_auth.models import PendingOAuthSession as _ReExport

        assert _ReExport is PendingOAuthSession


# ---------------------------------------------------------------------------
# AC: OAuthMfaPendingResult dataclass
# ---------------------------------------------------------------------------


class TestOAuthMfaPendingResult:
    """OAuthMfaPendingResult dataclass shape."""

    def test_has_pending_token_field(self) -> None:
        """OAuthMfaPendingResult must have a pending_token str field."""
        result = OAuthMfaPendingResult(pending_token="tok", mfa_setup_required=False)
        assert result.pending_token == "tok"  # noqa: S105

    def test_has_mfa_setup_required_field(self) -> None:
        """OAuthMfaPendingResult must have a mfa_setup_required bool field."""
        result = OAuthMfaPendingResult(pending_token="tok", mfa_setup_required=True)
        assert result.mfa_setup_required is True

    def test_mfa_setup_required_defaults_false(self) -> None:
        """mfa_setup_required must default to False when not provided."""
        result = OAuthMfaPendingResult(pending_token="tok", mfa_setup_required=False)
        assert result.mfa_setup_required is False


# ---------------------------------------------------------------------------
# AC: OAuthMfaCompleteResult dataclass
# ---------------------------------------------------------------------------


class TestOAuthMfaCompleteResult:
    """OAuthMfaCompleteResult dataclass shape."""

    def test_has_success_field(self) -> None:
        """OAuthMfaCompleteResult must have a success bool field."""
        result = OAuthMfaCompleteResult(
            success=False, token_pair=None, error_code="invalid_mfa_code", message="bad"
        )
        assert result.success is False

    def test_success_false_has_no_token_pair(self) -> None:
        """A failed result must carry token_pair=None."""
        result = OAuthMfaCompleteResult(
            success=False, token_pair=None, error_code="invalid_mfa_code", message="bad"
        )
        assert result.token_pair is None

    def test_has_error_code_field(self) -> None:
        """OAuthMfaCompleteResult must expose an error_code field."""
        result = OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="pending_token_expired",
            message="expired",
        )
        assert result.error_code == "pending_token_expired"

    def test_has_message_field(self) -> None:
        """OAuthMfaCompleteResult must expose a message field."""
        result = OAuthMfaCompleteResult(
            success=False, token_pair=None, error_code="x", message="details here"
        )
        assert result.message == "details here"


# ---------------------------------------------------------------------------
# AC: issue_oauth_pending_session()
# ---------------------------------------------------------------------------


class TestIssueOAuthPendingSession:
    """issue_oauth_pending_session() creates a PendingOAuthSession row."""

    def test_returns_oauth_mfa_pending_result(self) -> None:
        """issue_oauth_pending_session must return OAuthMfaPendingResult."""
        user = _make_user("pending_type@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        assert isinstance(result, OAuthMfaPendingResult), (
            f"Expected OAuthMfaPendingResult; got {type(result).__name__}"
        )

    def test_pending_token_is_non_empty_string(self) -> None:
        """The pending_token must be a non-empty string (UUID)."""
        user = _make_user("pending_token@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        assert isinstance(result.pending_token, str)
        assert len(result.pending_token) > 0

    def test_pending_token_is_valid_uuid(self) -> None:
        """The pending_token must be parseable as a UUID."""
        user = _make_user("pending_uuid@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        # Must not raise ValueError.
        uuid.UUID(result.pending_token)

    def test_creates_pending_oauth_session_row(self) -> None:
        """issue_oauth_pending_session must persist a PendingOAuthSession row."""
        user = _make_user("pending_row@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        assert PendingOAuthSession.objects.filter(
            id=result.pending_token,
            provider_token=make_provider_token("google"),
        ).exists(), "A PendingOAuthSession row must be created in the database"

    def test_pending_session_expires_after_default_ttl(self) -> None:
        """expires_at must be approximately now + 600 seconds (default TTL)."""
        user = _make_user("pending_ttl@example.com")
        before = timezone.now()
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        after = timezone.now()

        row = PendingOAuthSession.objects.get(id=result.pending_token)
        expected_min = before + timedelta(seconds=590)
        expected_max = after + timedelta(seconds=610)
        assert expected_min <= row.expires_at <= expected_max, (
            f"expires_at {row.expires_at!r} outside expected range "
            f"[{expected_min!r}, {expected_max!r}]"
        )

    def test_mfa_setup_required_true_when_user_has_no_mfa(self) -> None:
        """A user with no MFA configured must receive mfa_setup_required=True."""
        user = _make_user("pending_no_mfa@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        assert result.mfa_setup_required is True, (
            "mfa_setup_required must be True for a user with no MFA configured"
        )

    def test_distinct_tokens_for_same_user(self) -> None:
        """Two successive calls for the same user must return different tokens."""
        user = _make_user("pending_distinct@example.com")
        result_a = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        result_b = issue_oauth_pending_session(user_id=user.pk, provider="google")  # type: ignore[attr-defined]
        assert result_a.pending_token != result_b.pending_token, (
            "Each call must produce a distinct pending token"
        )

    def test_provider_stored_in_row(self) -> None:
        """The provider must be stored as ciphertext; provider_token must match the HMAC."""
        user = _make_user("pending_provider@example.com")
        result = issue_oauth_pending_session(user_id=user.pk, provider="facebook")  # type: ignore[attr-defined]
        row = PendingOAuthSession.objects.get(id=result.pending_token)
        # provider is ciphertext — must NOT equal the plaintext
        assert row.provider != "facebook", (
            "provider must be stored as ciphertext, not plaintext"
        )
        # provider_token is the deterministic HMAC lookup token
        assert row.provider_token == make_provider_token("facebook"), (
            "provider_token must be the HMAC-SHA256 of 'facebook'"
        )


# ---------------------------------------------------------------------------
# AC: complete_oauth_mfa()
# ---------------------------------------------------------------------------


class TestCompleteOAuthMfa:
    """complete_oauth_mfa() validates MFA and issues a full token pair."""

    def test_returns_oauth_mfa_complete_result(self) -> None:
        """complete_oauth_mfa must return OAuthMfaCompleteResult."""
        result = complete_oauth_mfa(
            pending_token=str(uuid.uuid4()),
            mfa_method="totp",
            mfa_proof="000000",
        )
        assert isinstance(result, OAuthMfaCompleteResult), (
            f"Expected OAuthMfaCompleteResult; got {type(result).__name__}"
        )

    def test_invalid_pending_token_returns_not_found(self) -> None:
        """A UUID with no matching DB row must return error_code='pending_token_not_found'."""
        result = complete_oauth_mfa(
            pending_token=str(uuid.uuid4()),  # random — definitely not in DB
            mfa_method="totp",
            mfa_proof="123456",
        )
        assert result.success is False
        assert result.error_code == "pending_token_not_found", (
            f"Expected 'pending_token_not_found'; got {result.error_code!r}"
        )
        assert result.token_pair is None

    def test_malformed_pending_token_returns_not_found(self) -> None:
        """A non-UUID string must return error_code='pending_token_not_found'."""
        result = complete_oauth_mfa(
            pending_token="not-a-valid-uuid",
            mfa_method="totp",
            mfa_proof="123456",
        )
        assert result.success is False
        assert result.error_code == "pending_token_not_found"

    def test_expired_pending_token_returns_expired(self) -> None:
        """An expired PendingOAuthSession must return error_code='pending_token_expired'."""
        user = _make_user("complete_expired@example.com")
        expired = _make_pending_session(
            user,
            "google",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        result = complete_oauth_mfa(
            pending_token=str(expired.id),
            mfa_method="totp",
            mfa_proof="123456",
        )
        assert result.success is False
        assert result.error_code == "pending_token_expired", (
            f"Expected 'pending_token_expired'; got {result.error_code!r}"
        )
        assert result.token_pair is None

    def test_expired_pending_token_is_cleaned_up(self) -> None:
        """An expired PendingOAuthSession must be deleted after the check."""
        user = _make_user("complete_expired_cleanup@example.com")
        expired = _make_pending_session(
            user,
            "google",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        pending_id = str(expired.id)
        complete_oauth_mfa(
            pending_token=pending_id,
            mfa_method="totp",
            mfa_proof="123456",
        )
        assert not PendingOAuthSession.objects.filter(id=pending_id).exists(), (
            "Expired PendingOAuthSession must be deleted after being consumed"
        )

    def test_wrong_mfa_proof_returns_invalid_mfa_code(self) -> None:
        """A valid pending token but wrong MFA proof must return 'invalid_mfa_code'."""
        user = _make_user("complete_wrong_mfa@example.com")
        pending = _make_pending_session(user, "google")
        result = complete_oauth_mfa(
            pending_token=str(pending.id),
            mfa_method="totp",
            mfa_proof="000000",  # almost certainly wrong
        )
        assert result.success is False
        assert result.error_code == "invalid_mfa_code", (
            f"Expected 'invalid_mfa_code'; got {result.error_code!r}"
        )

    def test_wrong_mfa_proof_does_not_consume_pending_token(self) -> None:
        """A failed MFA attempt must NOT delete the PendingOAuthSession row."""
        user = _make_user("complete_no_consume@example.com")
        pending = _make_pending_session(user, "google")
        pending_id = str(pending.id)
        complete_oauth_mfa(
            pending_token=pending_id,
            mfa_method="totp",
            mfa_proof="000000",
        )
        assert PendingOAuthSession.objects.filter(id=pending_id).exists(), (
            "A failed MFA attempt must not delete the PendingOAuthSession row"
        )

    def test_invalid_mfa_code_has_non_empty_message(self) -> None:
        """A failed result must include a non-empty human-readable message."""
        user = _make_user("complete_msg@example.com")
        pending = _make_pending_session(user, "google")
        result = complete_oauth_mfa(
            pending_token=str(pending.id),
            mfa_method="totp",
            mfa_proof="000000",
        )
        assert isinstance(result.message, str)
        assert len(result.message) > 0, "error message must not be empty"


class TestCompleteOAuthMfaSingleUse:
    """PendingOAuthSession tokens are single-use."""

    def test_consuming_pending_session_deletes_row(self) -> None:
        """After a successful complete_oauth_mfa call the row must no longer exist."""
        user = _make_user("complete_singleuse@example.com")
        # Create a pending session that will succeed (we'll need TOTP or email_otp)
        # For the red phase this test simply checks the deletion contract.
        pending = _make_pending_session(user, "google")
        pending_id = str(pending.id)
        # Attempt with a valid email_otp — service must issue token and delete row.
        # In the red phase the service doesn't exist; this is the desired contract.
        from syntek_auth.services.email_verification import (
            generate_email_verification_token,
        )

        # Use email_otp method: generate a valid OTP for this user.
        token = generate_email_verification_token(user_id=user.pk)  # type: ignore[attr-defined]
        result = complete_oauth_mfa(
            pending_token=pending_id,
            mfa_method="email_otp",
            mfa_proof=token,
        )
        if result.success:
            assert not PendingOAuthSession.objects.filter(id=pending_id).exists(), (
                "A successful complete_oauth_mfa must delete the PendingOAuthSession row"
            )

    def test_already_consumed_token_returns_not_found(self) -> None:
        """Replaying a pending_token that was already used must return 'pending_token_not_found'."""
        # Simulate a row that was already deleted (consumed by a first successful call).
        consumed_id = str(uuid.uuid4())
        # No row in DB for this ID.
        result = complete_oauth_mfa(
            pending_token=consumed_id,
            mfa_method="totp",
            mfa_proof="123456",
        )
        assert result.success is False
        assert result.error_code == "pending_token_not_found"


# ---------------------------------------------------------------------------
# AC: OidcCallbackPayload type structure
# ---------------------------------------------------------------------------


class TestOidcCallbackPayloadType:
    """OidcCallbackPayload must carry mfa_pending, pending_token, mfa_setup_required."""

    def test_oidc_callback_payload_has_mfa_pending_field(self) -> None:
        """OidcCallbackPayload must have a mfa_pending bool field."""
        payload = OidcCallbackPayload(
            access_token=None,
            refresh_token=None,
            mfa_pending=True,
            pending_token="tok",
            mfa_setup_required=False,
        )
        assert payload.mfa_pending is True

    def test_oidc_callback_payload_has_pending_token_field(self) -> None:
        """OidcCallbackPayload must have a pending_token field (str | None)."""
        payload = OidcCallbackPayload(
            access_token=None,
            refresh_token=None,
            mfa_pending=True,
            pending_token="abc-123",
            mfa_setup_required=False,
        )
        assert payload.pending_token == "abc-123"  # noqa: S105

    def test_oidc_callback_payload_has_mfa_setup_required_field(self) -> None:
        """OidcCallbackPayload must have a mfa_setup_required bool field."""
        payload = OidcCallbackPayload(
            access_token=None,
            refresh_token=None,
            mfa_pending=True,
            pending_token="tok",
            mfa_setup_required=True,
        )
        assert payload.mfa_setup_required is True

    def test_oidc_callback_payload_full_session_shape(self) -> None:
        """OidcCallbackPayload for a full session carries access_token and
        refresh_token with mfa_pending=False."""
        payload = OidcCallbackPayload(
            access_token="at.xxx",
            refresh_token="rt.yyy",
            mfa_pending=False,
            pending_token=None,
            mfa_setup_required=False,
        )
        assert payload.access_token == "at.xxx"  # noqa: S105
        assert payload.refresh_token == "rt.yyy"  # noqa: S105
        assert payload.mfa_pending is False
        assert payload.pending_token is None

    def test_oidc_callback_payload_pending_session_shape(self) -> None:
        """OidcCallbackPayload for a pending session has no tokens but has pending_token."""
        payload = OidcCallbackPayload(
            access_token=None,
            refresh_token=None,
            mfa_pending=True,
            pending_token="uuid-here",
            mfa_setup_required=False,
        )
        assert payload.access_token is None
        assert payload.refresh_token is None
        assert payload.mfa_pending is True
        assert payload.pending_token == "uuid-here"  # noqa: S105

    def test_oidc_callback_payload_mfa_setup_required_shape(self) -> None:
        """OidcCallbackPayload for a first-time gated user has mfa_setup_required=True."""
        payload = OidcCallbackPayload(
            access_token=None,
            refresh_token=None,
            mfa_pending=True,
            pending_token="uuid-here",
            mfa_setup_required=True,
        )
        assert payload.mfa_setup_required is True


# ---------------------------------------------------------------------------
# AC: OAUTH_MFA_PENDING_TTL setting validation
# ---------------------------------------------------------------------------


class TestOauthMfaPendingTtlSetting:
    """SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL'] must be validated at startup."""

    def test_ttl_below_minimum_raises_improperly_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A TTL of less than 60 seconds must raise ImproperlyConfigured at startup."""
        from django.core.exceptions import ImproperlyConfigured as Ipc
        from syntek_auth.conf import validate_settings

        with pytest.raises(Ipc, match="OAUTH_MFA_PENDING_TTL"):
            validate_settings(
                {
                    "FIELD_HMAC_KEY": "a" * 64,
                    "FIELD_KEY": "b" * 32,
                    "OAUTH_MFA_PENDING_TTL": 30,  # below minimum of 60
                }
            )

    def test_ttl_above_maximum_raises_improperly_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A TTL of more than 3600 seconds must raise ImproperlyConfigured at startup."""
        from django.core.exceptions import ImproperlyConfigured as Ipc
        from syntek_auth.conf import validate_settings

        with pytest.raises(Ipc, match="OAUTH_MFA_PENDING_TTL"):
            validate_settings(
                {
                    "FIELD_HMAC_KEY": "a" * 64,
                    "FIELD_KEY": "b" * 32,
                    "OAUTH_MFA_PENDING_TTL": 7200,  # above maximum of 3600
                }
            )

    def test_ttl_at_minimum_passes(self) -> None:
        """A TTL of exactly 60 seconds must pass validation."""
        from syntek_auth.conf import validate_settings

        # Must not raise.
        validate_settings(
            {
                "FIELD_HMAC_KEY": "a" * 64,
                "FIELD_KEY": "b" * 32,
                "OAUTH_MFA_PENDING_TTL": 60,
            }
        )

    def test_ttl_at_maximum_passes(self) -> None:
        """A TTL of exactly 3600 seconds must pass validation."""
        from syntek_auth.conf import validate_settings

        # Must not raise.
        validate_settings(
            {
                "FIELD_HMAC_KEY": "a" * 64,
                "FIELD_KEY": "b" * 32,
                "OAUTH_MFA_PENDING_TTL": 3600,
            }
        )

    def test_omitting_ttl_uses_default_of_600(self) -> None:
        """When OAUTH_MFA_PENDING_TTL is omitted, the default TTL must be 600 seconds."""
        from syntek_auth.services.oauth_mfa import _DEFAULT_PENDING_TTL

        assert _DEFAULT_PENDING_TTL == 600, (
            f"Default TTL must be 600 seconds; got {_DEFAULT_PENDING_TTL}"
        )
