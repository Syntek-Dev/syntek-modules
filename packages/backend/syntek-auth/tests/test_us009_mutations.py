"""US009 — Mutation layer tests for ``syntek-auth``.

Tests cover the GraphQL mutation resolver methods by calling them directly
with mocked Strawberry ``info`` context objects.  This avoids spinning up a
full GraphQL server while still exercising every resolver branch.

Files covered:
- ``syntek_auth.mutations.auth``   (AuthMutations)
- ``syntek_auth.mutations.mfa``    (MfaMutations)
- ``syntek_auth.mutations.oidc``   (OidcMutations, _constant_time_eq, _get_or_create_oidc_user)
- ``syntek_auth.mutations.password`` (PasswordMutations)

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from syntek_auth.mutations.auth import AuthMutations
from syntek_auth.mutations.mfa import MfaMutations
from syntek_auth.mutations.oidc import (
    OidcMutations,
    _constant_time_eq,
    _get_or_create_oidc_user,
)
from syntek_auth.mutations.password import PasswordMutations
from syntek_auth.types.auth import (
    ChangePasswordInput,
    LoginInput,
    OidcAuthUrlInput,
    OidcCallbackInput,
    RegisterInput,
    ResetPasswordConfirmInput,
    ResetPasswordRequestInput,
    VerifyEmailInput,
    VerifyMfaInput,
    VerifyPhoneInput,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_info(user: object = None, session: dict | None = None) -> MagicMock:
    """Build a minimal Strawberry info mock with a request context."""
    mock_request = MagicMock()
    mock_request.session = session if session is not None else {}
    if user is not None:
        mock_request.user = user
    else:
        anon = MagicMock()
        anon.is_authenticated = False
        mock_request.user = anon

    info = MagicMock()
    info.context.request = mock_request
    return info


def _make_authenticated_info(user: Any, session: dict | None = None) -> MagicMock:
    """Build an info mock with an authenticated user.

    Wraps the real user in a MagicMock so that the ``is_authenticated``
    property can be set freely without the Django model's read-only property
    raising ``AttributeError``.
    """
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    # Proxy .pk to the real user's pk so resolvers that call user.pk work.
    if hasattr(user, "pk"):
        mock_user.pk = user.pk
    info = _make_info(user=mock_user, session=session)
    return info


# ---------------------------------------------------------------------------
# AuthMutations
# ---------------------------------------------------------------------------


class TestAuthMutationsRegister:
    """Tests for ``AuthMutations.register``."""

    @pytest.mark.django_db
    def test_register_creates_user_and_returns_tokens(self, settings: Any) -> None:
        """Valid registration must return an ``AuthPayload`` with both tokens."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "REGISTRATION_ENABLED": True,
            "PASSWORD_MIN_LENGTH": 8,
        }
        mutation: Any = AuthMutations()
        info = _make_info()
        input_data = RegisterInput(email="newuser@example.com", password="StrongP@ss1!")

        payload = mutation.register(info, input_data)

        assert payload.access_token
        assert payload.refresh_token

    @pytest.mark.django_db
    def test_register_raises_when_registration_disabled(self, settings: Any) -> None:
        """When ``REGISTRATION_ENABLED=False``, registration must raise ValueError."""
        settings.SYNTEK_AUTH = {**settings.SYNTEK_AUTH, "REGISTRATION_ENABLED": False}
        mutation: Any = AuthMutations()
        info = _make_info()
        input_data = RegisterInput(email="blocked@example.com", password="Pass123!")

        with pytest.raises(ValueError, match="disabled"):
            mutation.register(info, input_data)

    @pytest.mark.django_db
    def test_register_raises_on_weak_password(self, settings: Any) -> None:
        """A password that violates policy must raise ValueError."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "REGISTRATION_ENABLED": True,
            "PASSWORD_MIN_LENGTH": 20,
        }
        mutation: Any = AuthMutations()
        info = _make_info()
        input_data = RegisterInput(email="weak@example.com", password="short")

        with pytest.raises(ValueError, match="Password"):
            mutation.register(info, input_data)


class TestAuthMutationsLogin:
    """Tests for ``AuthMutations.login``."""

    @pytest.mark.django_db
    def test_login_returns_tokens_on_valid_credentials(self, settings: Any) -> None:
        """Valid credentials must return an ``AuthPayload`` with both tokens."""
        settings.SYNTEK_AUTH = {**settings.SYNTEK_AUTH, "LOGIN_FIELD": "email"}
        from syntek_auth.factories.user import UserFactory

        UserFactory.create(email="logintest@example.com", password="ValidPass99!")

        mutation: Any = AuthMutations()
        info = _make_info()
        input_data = LoginInput(
            identifier="logintest@example.com", password="ValidPass99!"
        )

        payload = mutation.login(info, input_data)

        assert payload.access_token
        assert payload.refresh_token

    @pytest.mark.django_db
    def test_login_raises_on_invalid_credentials(self, settings: Any) -> None:
        """Invalid credentials must raise ValueError."""
        settings.SYNTEK_AUTH = {**settings.SYNTEK_AUTH, "LOGIN_FIELD": "email"}
        mutation: Any = AuthMutations()
        info = _make_info()
        input_data = LoginInput(identifier="nobody@example.com", password="wrong")

        with pytest.raises(ValueError, match="Invalid credentials"):
            mutation.login(info, input_data)


class TestAuthMutationsLogout:
    """Tests for ``AuthMutations.logout``."""

    @pytest.mark.django_db
    def test_logout_returns_false_for_unknown_token(self) -> None:
        """``logout`` with an unknown token must return False (not raise)."""
        mutation: Any = AuthMutations()
        info = _make_info()

        # Passing an invalid token returns False without raising.
        result = mutation.logout(info, "not_a_real_token")
        assert result is False


class TestAuthMutationsRefreshToken:
    """Tests for ``AuthMutations.refresh_token``."""

    @pytest.mark.django_db
    def test_refresh_token_raises_on_invalid_token(self) -> None:
        """An invalid refresh token must raise ValueError."""
        mutation: Any = AuthMutations()
        info = _make_info()

        with pytest.raises(ValueError, match="Invalid"):
            mutation.refresh_token(info, "not_a_valid_token")


# ---------------------------------------------------------------------------
# MfaMutations
# ---------------------------------------------------------------------------


class TestMfaMutationsEnableMfa:
    """Tests for ``MfaMutations.enable_mfa``."""

    @pytest.mark.django_db
    def test_enable_mfa_returns_setup_payload(self, settings: Any) -> None:
        """An authenticated user must receive a valid ``MfaSetupPayload``."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "MFA_BACKUP_CODES_COUNT": 5,
            "SITE_NAME": "TestSite",
        }
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        info = _make_authenticated_info(user)
        info.context.request.user.pk = user.pk

        mutation: Any = MfaMutations()
        payload = mutation.enable_mfa(info)

        assert payload.provisioning_uri.startswith("otpauth://totp/")
        assert len(payload.backup_codes) == 5

    def test_enable_mfa_raises_when_unauthenticated(self) -> None:
        """An unauthenticated request must raise ValueError."""
        info = _make_info()  # anonymous
        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="Authentication required"):
            mutation.enable_mfa(info)


class TestMfaMutationsVerifyMfa:
    """Tests for ``MfaMutations.verify_mfa``."""

    @pytest.mark.django_db
    def test_verify_mfa_raises_on_invalid_code(self, settings: Any) -> None:
        """An invalid MFA code must raise ValueError."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.pk = user.pk
        mock_user.totp_secret = None

        info = _make_authenticated_info(mock_user)
        info.context.request.user = mock_user

        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="Invalid MFA code"):
            mutation.verify_mfa(info, VerifyMfaInput(code="000000"))

    def test_verify_mfa_raises_when_unauthenticated(self) -> None:
        """An unauthenticated request must raise ValueError."""
        info = _make_info()
        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="Authentication required"):
            mutation.verify_mfa(info, VerifyMfaInput(code="123456"))


class TestMfaMutationsPasskey:
    """Tests for passkey mutations (stubbed)."""

    def test_register_passkey_raises_when_unauthenticated(self) -> None:
        """An unauthenticated request must raise ValueError before the stub error."""
        info = _make_info()
        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="Authentication required"):
            mutation.register_passkey(info)

    def test_register_passkey_raises_with_stub_error_when_authenticated(self) -> None:
        """An authenticated request must raise ValueError — passkey not yet available."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        info = _make_authenticated_info(mock_user)
        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="not yet available"):
            mutation.register_passkey(info)

    def test_authenticate_passkey_always_raises(self) -> None:
        """``authenticate_passkey`` must always raise ValueError."""
        info = _make_info()
        mutation: Any = MfaMutations()

        with pytest.raises(ValueError, match="not yet available"):
            mutation.authenticate_passkey(info)


# ---------------------------------------------------------------------------
# OidcMutations — _constant_time_eq (internal helper)
# ---------------------------------------------------------------------------


class TestConstantTimeEq:
    """Tests for the internal ``_constant_time_eq`` helper."""

    def test_equal_strings_return_true(self) -> None:
        """Two identical strings must compare as equal."""
        assert _constant_time_eq("abc", "abc") is True

    def test_different_strings_return_false(self) -> None:
        """Two different strings must compare as not equal."""
        assert _constant_time_eq("abc", "xyz") is False

    def test_empty_strings_return_true(self) -> None:
        """Two empty strings must compare as equal."""
        assert _constant_time_eq("", "") is True


# ---------------------------------------------------------------------------
# OidcMutations — _get_or_create_oidc_user (internal helper)
# ---------------------------------------------------------------------------


class TestGetOrCreateOidcUser:
    """Tests for the internal ``_get_or_create_oidc_user`` helper."""

    @pytest.mark.django_db
    def test_creates_new_user_when_email_not_found(self) -> None:
        """When no user exists for the given email, a new one must be created."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = _get_or_create_oidc_user(
            user_model=UserModel,
            provider_id="google",
            sub="google_sub_999",
            email="oidcnewuser@example.com",
        )
        assert user is not None

    @pytest.mark.django_db
    def test_returns_existing_user_by_email(self) -> None:
        """When a user already exists with the given email, it must be returned."""
        from django.contrib.auth import get_user_model
        from syntek_auth.factories.user import UserFactory

        UserModel = get_user_model()  # noqa: N806
        existing = UserFactory.create(email="existingoidc@example.com")

        user = _get_or_create_oidc_user(
            user_model=UserModel,
            provider_id="google",
            sub="google_sub_existing",
            email="existingoidc@example.com",
        )
        assert user.pk == existing.pk  # type: ignore[union-attr]

    @pytest.mark.django_db
    def test_raises_when_no_email_provided(self) -> None:
        """When no email is supplied and no existing mapping, ValueError must be raised."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806

        with pytest.raises(ValueError, match="Cannot resolve"):
            _get_or_create_oidc_user(
                user_model=UserModel,
                provider_id="google",
                sub="google_sub_noemail",
                email=None,
            )


class TestOidcMutationsAuthUrl:
    """Tests for ``OidcMutations.oidc_auth_url``."""

    def test_oidc_auth_url_returns_url_string(self, settings: Any) -> None:
        """A configured provider must return a full authorisation URL."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [
                {
                    "id": "test_provider",
                    "discovery_url": "https://accounts.example.com/.well-known/openid-configuration",
                    "client_id": "test_client_id",
                }
            ],
        }

        discovery_doc = {
            "issuer": "https://accounts.example.com",
            "authorization_endpoint": "https://accounts.example.com/auth",
            "token_endpoint": "https://accounts.example.com/token",
            "jwks_uri": "https://accounts.example.com/jwks",
        }

        import json
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(discovery_doc).encode()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_resp)
        mock_cm.__exit__ = MagicMock(return_value=False)

        info = _make_info(session={})
        input_data = OidcAuthUrlInput(
            provider_id="test_provider",
            redirect_uri="https://app.example.com/callback",
        )

        mutation: Any = OidcMutations()
        with patch("urllib.request.urlopen", return_value=mock_cm):
            url = mutation.oidc_auth_url(info, input_data)

        assert url.startswith("https://accounts.example.com/auth")

    def test_oidc_auth_url_raises_for_unknown_provider(self, settings: Any) -> None:
        """An unknown provider ID must raise ValueError."""
        settings.SYNTEK_AUTH = {**settings.SYNTEK_AUTH, "OIDC_PROVIDERS": []}
        info = _make_info()
        mutation: Any = OidcMutations()

        with pytest.raises(ValueError, match="not configured"):
            mutation.oidc_auth_url(
                info,
                OidcAuthUrlInput(
                    provider_id="ghost", redirect_uri="https://app.example.com/callback"
                ),
            )


class TestOidcMutationsCallback:
    """Tests for ``OidcMutations.oidc_callback``."""

    def test_oidc_callback_raises_on_invalid_state(self, settings: Any) -> None:
        """A mismatched CSRF state must raise ValueError."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [
                {
                    "id": "google",
                    "discovery_url": "...",
                    "client_id": "c",
                    "client_secret": "s",
                }
            ],
        }
        info = _make_info(session={"oidc_state": "correct_state"})
        input_data = OidcCallbackInput(
            provider_id="google",
            code="auth_code",
            state="wrong_state",  # CSRF mismatch
            redirect_uri="https://app.example.com/callback",
        )
        mutation: Any = OidcMutations()

        with pytest.raises(ValueError, match="CSRF"):
            mutation.oidc_callback(info, input_data)

    def test_oidc_callback_raises_when_no_state_in_session(self, settings: Any) -> None:
        """When no OIDC state is in the session, the callback must raise ValueError."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [
                {
                    "id": "google",
                    "discovery_url": "...",
                    "client_id": "c",
                    "client_secret": "s",
                }
            ],
        }
        info = _make_info(session={})  # no oidc_state
        input_data = OidcCallbackInput(
            provider_id="google",
            code="auth_code",
            state="some_state",
            redirect_uri="https://app.example.com/callback",
        )
        mutation: Any = OidcMutations()

        with pytest.raises(ValueError, match="CSRF"):
            mutation.oidc_callback(info, input_data)


class TestOidcMutationsCompleteSocialMfa:
    """Tests for ``OidcMutations.complete_social_mfa``."""

    def test_complete_social_mfa_success_path(self) -> None:
        """A successful MFA completion must return an ``OidcCallbackPayload`` with tokens."""
        from syntek_auth.services.oauth_mfa import OAuthMfaCompleteResult
        from syntek_auth.types.auth import OidcCallbackPayload  # noqa: F401

        mock_pair = MagicMock()
        mock_pair.access_token = "access_tok"  # noqa: S105
        mock_pair.refresh_token = "refresh_tok"  # noqa: S105
        mock_result = OAuthMfaCompleteResult(
            success=True,
            token_pair=mock_pair,
            error_code=None,
            message="",
        )

        info = _make_info()
        mutation: Any = OidcMutations()

        with patch(
            "syntek_auth.services.oauth_mfa.complete_oauth_mfa",
            return_value=mock_result,
        ):
            payload = mutation.complete_social_mfa(
                info, "pending_uuid", "totp", "123456"
            )

        assert payload.access_token == "access_tok"  # noqa: S105
        assert payload.mfa_pending is False

    def test_complete_social_mfa_failure_path(self) -> None:
        """A failed MFA completion must return a pending payload with error fields."""
        from syntek_auth.services.oauth_mfa import OAuthMfaCompleteResult

        mock_result = OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="invalid_code",
            message="The code you entered is incorrect.",
        )

        info = _make_info()
        mutation: Any = OidcMutations()

        with patch(
            "syntek_auth.services.oauth_mfa.complete_oauth_mfa",
            return_value=mock_result,
        ):
            payload = mutation.complete_social_mfa(
                info, "pending_uuid", "totp", "000000"
            )

        assert payload.mfa_pending is True
        assert payload.error_code == "invalid_code"


# ---------------------------------------------------------------------------
# PasswordMutations
# ---------------------------------------------------------------------------


class TestPasswordMutationsChangePassword:
    """Tests for ``PasswordMutations.change_password``."""

    def test_change_password_raises_when_unauthenticated(self) -> None:
        """An unauthenticated request must raise ValueError."""
        info = _make_info()
        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match="Authentication required"):
            mutation.change_password(
                info, ChangePasswordInput(current_password="old", new_password="new")
            )

    @pytest.mark.django_db
    def test_change_password_raises_when_current_password_wrong(self) -> None:
        """An incorrect current password must cause ValueError."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(password="CorrectPass99!")
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.pk = user.pk
        info = _make_authenticated_info(mock_user)

        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match="incorrect"):
            mutation.change_password(
                info,
                ChangePasswordInput(
                    current_password="WrongPassword!", new_password="NewStrongPass99!"
                ),
            )


class TestPasswordMutationsResetPasswordRequest:
    """Tests for ``PasswordMutations.reset_password_request``."""

    @pytest.mark.django_db
    def test_reset_password_request_always_returns_true(self) -> None:
        """Password reset request must always return True (anti-enumeration)."""
        info = _make_info()
        mutation: Any = PasswordMutations()

        result = mutation.reset_password_request(
            info, ResetPasswordRequestInput(email="anyone@example.com")
        )
        assert result is True


class TestPasswordMutationsResetPasswordConfirm:
    """Tests for ``PasswordMutations.reset_password_confirm``."""

    @pytest.mark.django_db
    def test_reset_password_confirm_raises_on_invalid_token(self) -> None:
        """An invalid reset token must cause ValueError."""
        info = _make_info()
        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match="token"):
            mutation.reset_password_confirm(
                info,
                ResetPasswordConfirmInput(
                    token="invalid_token", new_password="NewPass99!"
                ),
            )


class TestPasswordMutationsVerifyEmail:
    """Tests for ``PasswordMutations.verify_email``."""

    @pytest.mark.django_db
    def test_verify_email_raises_on_invalid_token(self) -> None:
        """An invalid email verification token must cause ValueError."""
        info = _make_info()
        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match="token"):
            mutation.verify_email(info, VerifyEmailInput(token="bad_token"))


class TestPasswordMutationsResendVerificationEmail:
    """Tests for ``PasswordMutations.resend_verification_email``."""

    @pytest.mark.django_db
    def test_resend_verification_email_raises_when_already_verified(self) -> None:
        """When the account is already verified, ValueError must be raised."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        info = _make_info()
        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match="already verified"):
            mutation.resend_verification_email(info, user.pk)

    @pytest.mark.django_db
    def test_resend_verification_email_returns_true_when_not_verified(self) -> None:
        """When the account is not yet verified, a new token is issued and True returned."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        # email_verified defaults to False

        info = _make_info()
        mutation: Any = PasswordMutations()

        result = mutation.resend_verification_email(info, user.pk)
        assert result is True


class TestPasswordMutationsVerifyPhone:
    """Tests for ``PasswordMutations.verify_phone``."""

    @pytest.mark.django_db
    def test_verify_phone_raises_on_invalid_otp(self) -> None:
        """An invalid phone OTP must cause ValueError."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        info = _make_info()
        mutation: Any = PasswordMutations()

        with pytest.raises(ValueError, match=r"OTP|otp|invalid|expired"):
            mutation.verify_phone(info, VerifyPhoneInput(user_id=user.pk, otp="BADOTP"))


class TestPasswordMutationsResendPhoneOtp:
    """Tests for ``PasswordMutations.resend_phone_otp``."""

    @pytest.mark.django_db
    def test_resend_phone_otp_returns_true(self) -> None:
        """Resending a phone OTP must return True."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        info = _make_info()
        mutation: Any = PasswordMutations()

        result = mutation.resend_phone_otp(info, user.pk)
        assert result is True


# ---------------------------------------------------------------------------
# OidcMutations.oidc_callback — success path (via service mocks)
# ---------------------------------------------------------------------------


class TestOidcMutationsCallbackSuccessPath:
    """Tests for ``OidcMutations.oidc_callback`` covering the success branches."""

    def _build_provider_settings(self) -> dict:
        return {
            "id": "testprovider",
            "discovery_url": "https://accounts.example.com/.well-known/openid-configuration",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        }

    @pytest.mark.django_db
    def test_oidc_callback_issues_token_pair_on_success(self, settings: Any) -> None:
        """A valid callback must issue an access + refresh token pair."""

        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [self._build_provider_settings()],
            "MFA_REQUIRED": False,
        }

        from syntek_auth.factories.user import UserFactory
        from syntek_auth.services.oidc import OidcProviderConfig, OidcTokenClaims

        UserFactory.create(email="oidcuser@example.com")

        mock_provider = OidcProviderConfig(
            issuer="https://accounts.example.com",
            authorisation_endpoint="https://accounts.example.com/auth",
            token_endpoint="https://accounts.example.com/token",
            jwks_uri="https://accounts.example.com/jwks",
        )
        mock_claims = OidcTokenClaims(
            sub="oidc_sub_001",
            email="oidcuser@example.com",
            amr=None,
            raw={},
        )
        mock_token_response = {
            "id_token": "mock.id.token",
            "access_token": "mock_access",
        }
        mock_pair = MagicMock()
        mock_pair.access_token = "syntek_access"  # noqa: S105
        mock_pair.refresh_token = "syntek_refresh"  # noqa: S105

        state = "valid_state_value"
        info = _make_info(session={"oidc_state": state, "oidc_nonce": "test_nonce"})
        input_data = OidcCallbackInput(
            provider_id="testprovider",
            code="auth_code",
            state=state,
            redirect_uri="https://app.example.com/callback",
        )

        mutation: Any = OidcMutations()
        with (
            patch(
                "syntek_auth.services.oidc.discover_provider",
                return_value=mock_provider,
            ),
            patch(
                "syntek_auth.services.oidc.exchange_code",
                return_value=mock_token_response,
            ),
            patch(
                "syntek_auth.services.oidc.validate_id_token", return_value=mock_claims
            ),
            patch(
                "syntek_auth.services.tokens.issue_token_pair", return_value=mock_pair
            ),
            patch(
                "syntek_auth.backends.allowlist.is_mfa_gated_provider",
                return_value=False,
            ),
        ):
            payload = mutation.oidc_callback(info, input_data)

        assert payload.mfa_pending is False
        assert payload.access_token == "syntek_access"  # noqa: S105

    @pytest.mark.django_db
    def test_oidc_callback_raises_when_no_id_token_in_response(
        self, settings: Any
    ) -> None:
        """When the token exchange response has no id_token, ValueError must be raised."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [self._build_provider_settings()],
            "MFA_REQUIRED": False,
        }

        from syntek_auth.services.oidc import OidcProviderConfig

        mock_provider = OidcProviderConfig(
            issuer="https://accounts.example.com",
            authorisation_endpoint="https://accounts.example.com/auth",
            token_endpoint="https://accounts.example.com/token",
            jwks_uri="https://accounts.example.com/jwks",
        )
        # Token response without id_token
        mock_token_response: dict = {"access_token": "only_access"}

        state = "valid_state_for_no_id_token"
        info = _make_info(session={"oidc_state": state})
        input_data = OidcCallbackInput(
            provider_id="testprovider",
            code="auth_code",
            state=state,
            redirect_uri="https://app.example.com/callback",
        )

        mutation: Any = OidcMutations()
        with (
            patch(
                "syntek_auth.services.oidc.discover_provider",
                return_value=mock_provider,
            ),
            patch(
                "syntek_auth.services.oidc.exchange_code",
                return_value=mock_token_response,
            ),
            pytest.raises(ValueError, match="ID token"),
        ):
            mutation.oidc_callback(info, input_data)

    @pytest.mark.django_db
    def test_oidc_callback_raises_when_mfa_required_but_amr_missing(
        self, settings: Any
    ) -> None:
        """When MFA_REQUIRED=True and amr does not satisfy MFA, ValueError must be raised."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [self._build_provider_settings()],
            "MFA_REQUIRED": True,
        }

        from syntek_auth.services.oidc import OidcProviderConfig, OidcTokenClaims

        mock_provider = OidcProviderConfig(
            issuer="https://accounts.example.com",
            authorisation_endpoint="https://accounts.example.com/auth",
            token_endpoint="https://accounts.example.com/token",
            jwks_uri="https://accounts.example.com/jwks",
        )
        # amr is None — MFA not satisfied
        mock_claims = OidcTokenClaims(sub="user_sub", email=None, amr=None, raw={})
        mock_token_response = {"id_token": "mock.id.token"}

        state = "state_mfa_required"
        info = _make_info(session={"oidc_state": state})
        input_data = OidcCallbackInput(
            provider_id="testprovider",
            code="auth_code",
            state=state,
            redirect_uri="https://app.example.com/callback",
        )

        mutation: Any = OidcMutations()
        with (
            patch(
                "syntek_auth.services.oidc.discover_provider",
                return_value=mock_provider,
            ),
            patch(
                "syntek_auth.services.oidc.exchange_code",
                return_value=mock_token_response,
            ),
            patch(
                "syntek_auth.services.oidc.validate_id_token", return_value=mock_claims
            ),
            pytest.raises(ValueError, match="MFA"),
        ):
            mutation.oidc_callback(info, input_data)

    @pytest.mark.django_db
    def test_oidc_callback_returns_pending_when_provider_is_mfa_gated(
        self, settings: Any
    ) -> None:
        """When the provider is MFA-gated, a pending session token must be returned."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [self._build_provider_settings()],
            "MFA_REQUIRED": False,
        }

        from syntek_auth.factories.user import UserFactory
        from syntek_auth.services.oauth_mfa import OAuthMfaPendingResult
        from syntek_auth.services.oidc import OidcProviderConfig, OidcTokenClaims

        UserFactory.create(email="gated@example.com")

        mock_provider = OidcProviderConfig(
            issuer="https://accounts.example.com",
            authorisation_endpoint="https://accounts.example.com/auth",
            token_endpoint="https://accounts.example.com/token",
            jwks_uri="https://accounts.example.com/jwks",
        )
        mock_claims = OidcTokenClaims(
            sub="gated_sub",
            email="gated@example.com",
            amr=None,
            raw={},
        )
        mock_pending = OAuthMfaPendingResult(
            pending_token="pending-uuid-123",
            mfa_setup_required=False,
        )
        mock_token_response = {"id_token": "mock.id.token"}
        state = "state_gated"

        info = _make_info(session={"oidc_state": state, "oidc_nonce": "nonce_gated"})
        input_data = OidcCallbackInput(
            provider_id="testprovider",
            code="auth_code",
            state=state,
            redirect_uri="https://app.example.com/callback",
        )

        mutation: Any = OidcMutations()
        with (
            patch(
                "syntek_auth.services.oidc.discover_provider",
                return_value=mock_provider,
            ),
            patch(
                "syntek_auth.services.oidc.exchange_code",
                return_value=mock_token_response,
            ),
            patch(
                "syntek_auth.services.oidc.validate_id_token", return_value=mock_claims
            ),
            patch(
                "syntek_auth.backends.allowlist.is_mfa_gated_provider",
                return_value=True,
            ),
            patch(
                "syntek_auth.services.oauth_mfa.issue_oauth_pending_session",
                return_value=mock_pending,
            ),
        ):
            payload = mutation.oidc_callback(info, input_data)

        assert payload.mfa_pending is True
        assert payload.pending_token == "pending-uuid-123"  # noqa: S105


# ---------------------------------------------------------------------------
# MfaMutations.verify_mfa — success via backup code
# ---------------------------------------------------------------------------


class TestMfaMutationsVerifyMfaSuccessPath:
    """Test the success branches of ``MfaMutations.verify_mfa``."""

    @pytest.mark.django_db
    def test_verify_mfa_accepts_valid_backup_code(self, settings: Any) -> None:
        """A valid backup code must return True via the backup code path."""
        from syntek_auth.factories.user import UserFactory
        from syntek_auth.services.totp import generate_backup_codes, store_backup_codes

        user = UserFactory.create()
        codes = generate_backup_codes(3)
        store_backup_codes(user.pk, codes)

        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.pk = user.pk
        mock_user.totp_secret = None  # no TOTP configured

        info = _make_authenticated_info(mock_user)
        info.context.request.user.totp_secret = None  # no TOTP secret on this user

        mutation: Any = MfaMutations()
        result = mutation.verify_mfa(info, VerifyMfaInput(code=codes[0]))
        assert result is True


# ---------------------------------------------------------------------------
# AuthMutations.refresh_token — success path
# ---------------------------------------------------------------------------


class TestAuthMutationsRefreshTokenSuccessPath:
    """Test the success path of ``AuthMutations.refresh_token``."""

    @pytest.mark.django_db
    def test_refresh_token_returns_new_pair(self, settings: Any) -> None:
        """A valid refresh token must return a new ``AuthPayload``."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "LOGIN_FIELD": "email",
        }
        from syntek_auth.factories.user import UserFactory
        from syntek_auth.services.tokens import issue_token_pair

        user = UserFactory.create()
        pair = issue_token_pair(user.pk, 900, 604800)

        mutation: Any = AuthMutations()
        info = _make_info()
        new_payload = mutation.refresh_token(info, pair.refresh_token)

        assert new_payload.access_token
        assert new_payload.refresh_token
