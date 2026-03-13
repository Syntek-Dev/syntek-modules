"""Strawberry input/output types for ``syntek-auth`` — US009.

Defines the GraphQL input and output types used by the auth mutation and
query resolvers.  All fields are required (no ``UNSET`` defaults) unless
explicitly marked optional with ``| None``.
"""

from __future__ import annotations

import strawberry


@strawberry.input
class RegisterInput:
    """Input type for the ``register`` mutation.

    Attributes
    ----------
    email:
        The new user's email address.
    password:
        The desired plaintext password (validated against policy server-side).
    username:
        Optional username.  When ``None``, the model stores ``NULL`` for
        the username column.
    """

    email: str
    password: str
    username: str | None = None


@strawberry.input
class LoginInput:
    """Input type for the ``login`` mutation.

    Attributes
    ----------
    identifier:
        The login identifier — interpreted as email, username, or phone
        depending on ``SYNTEK_AUTH['LOGIN_FIELD']``.
    password:
        The plaintext password to verify.
    """

    identifier: str
    password: str


@strawberry.type
class AuthPayload:
    """Output type carrying the token pair returned after authentication.

    Attributes
    ----------
    access_token:
        Short-lived JWT access token.
    refresh_token:
        Long-lived JWT refresh token.  Rotate on every use.
    """

    access_token: str
    refresh_token: str


@strawberry.input
class ChangePasswordInput:
    """Input type for the ``changePassword`` mutation.

    Attributes
    ----------
    current_password:
        The user's current plaintext password for verification.
    new_password:
        The desired new plaintext password (validated against policy).
    """

    current_password: str
    new_password: str


@strawberry.input
class ResetPasswordRequestInput:
    """Input type for the ``resetPasswordRequest`` mutation.

    Attributes
    ----------
    email:
        The email address associated with the account for which a reset
        link should be sent.
    """

    email: str


@strawberry.input
class ResetPasswordConfirmInput:
    """Input type for the ``resetPasswordConfirm`` mutation.

    Attributes
    ----------
    token:
        The single-use reset token delivered via email.
    new_password:
        The desired new plaintext password (validated against policy).
    """

    token: str
    new_password: str


@strawberry.input
class VerifyEmailInput:
    """Input type for the ``verifyEmail`` mutation.

    Attributes
    ----------
    token:
        The single-use email verification token delivered via email link.
    """

    token: str


@strawberry.input
class VerifyPhoneInput:
    """Input type for the ``verifyPhone`` mutation.

    Attributes
    ----------
    user_id:
        Primary key of the user whose phone is being verified.
    otp:
        The 6-character OTP submitted by the user.
    """

    user_id: int
    otp: str


@strawberry.type
class MfaSetupPayload:
    """Output type carrying MFA setup data (e.g. TOTP provisioning URI).

    Attributes
    ----------
    provisioning_uri:
        The ``otpauth://`` URI used to populate an authenticator app QR code.
    backup_codes:
        Single-use backup codes generated at TOTP setup.
    """

    provisioning_uri: str
    backup_codes: list[str]


@strawberry.input
class VerifyMfaInput:
    """Input type for the ``verifyMfa`` mutation.

    Attributes
    ----------
    code:
        The 6-digit TOTP code or backup code to verify.
    """

    code: str


@strawberry.input
class OidcAuthUrlInput:
    """Input type for the ``oidcAuthUrl`` mutation.

    Attributes
    ----------
    provider_id:
        Identifier of the OIDC provider (e.g. ``'github'``, ``'okta'``).
    redirect_uri:
        The URI the provider should redirect to after authorisation.
    """

    provider_id: str
    redirect_uri: str


@strawberry.type
class OidcCallbackPayload:
    """Output type for ``oidcCallback`` and ``completeSocialMfa``.

    Carries either a full session (access + refresh tokens) or a pending MFA
    token depending on whether the provider requires local MFA gating.

    Attributes
    ----------
    access_token:
        Short-lived JWT access token.  ``None`` when ``mfa_pending=True``.
    refresh_token:
        Long-lived JWT refresh token.  ``None`` when ``mfa_pending=True``.
    mfa_pending:
        ``True`` when the user must still complete a local MFA challenge.
    pending_token:
        UUID string identifying the ``PendingOAuthSession`` row.  ``None``
        when ``mfa_pending=False``.
    mfa_setup_required:
        ``True`` when the user has no MFA method configured and must enrol
        before completing the challenge.
    error_code:
        Machine-readable error identifier on failure; ``None`` on success.
    message:
        Human-readable description of the outcome on failure; empty on success.
    """

    access_token: str | None = None
    refresh_token: str | None = None
    mfa_pending: bool = False
    pending_token: str | None = None
    mfa_setup_required: bool = False
    error_code: str | None = None
    message: str | None = None


@strawberry.input
class OidcCallbackInput:
    """Input type for the ``oidcCallback`` mutation.

    Attributes
    ----------
    provider_id:
        Identifier of the OIDC provider that issued the callback.
    code:
        The authorisation code returned by the provider.
    state:
        The ``state`` parameter echoed back by the provider.
    redirect_uri:
        The redirect URI used in the original authorisation request.
    """

    provider_id: str
    code: str
    state: str
    redirect_uri: str
