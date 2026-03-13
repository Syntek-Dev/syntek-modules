"""GraphQL auth mutations for ``syntek-auth`` — US009.

Strawberry mutations for register, login, logout, and token refresh.
All resolvers delegate to the service layer; no business logic lives
directly in mutation methods.

Service imports are placed inside each resolver body to avoid circular
imports between the mutation layer, the model layer, and the service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

from syntek_auth.types.auth import AuthPayload, LoginInput, RegisterInput

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class AuthMutations:
    """Strawberry mutation type for core auth operations."""

    @strawberry.mutation
    def register(self, info: Info, input: RegisterInput) -> AuthPayload:  # noqa: A002,ARG002
        """Register a new user account and return a token pair.

        Validates the password against ``SYNTEK_AUTH`` policy before creating
        the user.  Raises ``ValueError`` if registration is disabled or if
        the password violates policy.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            Registration fields — email, password, and optional username.

        Returns
        -------
        AuthPayload
            Access and refresh tokens for the newly created user.

        Raises
        ------
        ValueError
            If registration is disabled, the password is too weak, or the
            email address is already in use.
        """
        from django.conf import settings
        from django.contrib.auth import get_user_model

        from syntek_auth.services.password import validate_password_policy
        from syntek_auth.services.tokens import issue_token_pair

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]

        if not cfg.get("REGISTRATION_ENABLED", True):
            raise ValueError("Registration is disabled for this deployment.")

        result = validate_password_policy(input.password, cfg)
        if not result.valid:
            raise ValueError("; ".join(v.message for v in result.violations))

        UserModel = get_user_model()  # noqa: N806
        extra: dict = {} if input.username is None else {"username": input.username}  # type: ignore[type-arg]
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email=input.email,
            password=input.password,
            **extra,
        )

        access_lifetime: int = cfg.get("ACCESS_TOKEN_LIFETIME", 900)
        refresh_lifetime: int = cfg.get("REFRESH_TOKEN_LIFETIME", 604800)
        pair = issue_token_pair(user.pk, access_lifetime, refresh_lifetime)

        return AuthPayload(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
        )

    @strawberry.mutation
    def login(self, info: Info, input: LoginInput) -> AuthPayload:  # noqa: A002
        """Authenticate a user and issue a token pair.

        Delegates credential verification to ``SyntekAuthBackend``.  Returns
        ``ValueError`` on failure rather than a discriminated union so that
        GraphQL clients receive a clear error message.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            Login fields — identifier and password.

        Returns
        -------
        AuthPayload
            Access and refresh tokens for the authenticated user.

        Raises
        ------
        ValueError
            If the credentials are invalid or the account is inactive.
        """
        from django.conf import settings

        from syntek_auth.backends.auth_backend import SyntekAuthBackend
        from syntek_auth.services.tokens import issue_token_pair

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        request = getattr(info.context, "request", None)

        user = SyntekAuthBackend().authenticate(
            request=request,
            username=input.identifier,
            password=input.password,
        )

        if user is None:
            raise ValueError("Invalid credentials.")

        access_lifetime: int = cfg.get("ACCESS_TOKEN_LIFETIME", 900)
        refresh_lifetime: int = cfg.get("REFRESH_TOKEN_LIFETIME", 604800)
        pair = issue_token_pair(user.pk, access_lifetime, refresh_lifetime)

        return AuthPayload(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
        )

    @strawberry.mutation
    def logout(self, info: Info, refresh_token: str) -> bool:  # noqa: ARG002
        """Invalidate the supplied refresh token.

        Marks the refresh token's JTI as revoked in the in-process revocation
        store.  Returns ``True`` if the token was valid and has been revoked;
        returns ``False`` if the token was already invalid or malformed.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused but required by Strawberry).
        refresh_token:
            The refresh token string to revoke.

        Returns
        -------
        bool
            ``True`` on successful revocation, ``False`` otherwise.
        """
        from syntek_auth.services.tokens import revoke_refresh_token

        return revoke_refresh_token(refresh_token)

    @strawberry.mutation
    def refresh_token(self, info: Info, token: str) -> AuthPayload:  # noqa: ARG002
        """Rotate the refresh token and issue a new token pair.

        Consumes the supplied refresh token (marks it as revoked) and issues
        a fresh access + refresh token pair.  A reused or expired token raises
        ``ValueError``.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused but required by Strawberry).
        token:
            The current refresh token to consume.

        Returns
        -------
        AuthPayload
            A new access and refresh token pair.

        Raises
        ------
        ValueError
            If the refresh token is invalid, expired, or has already been used.
        """
        from django.conf import settings

        from syntek_auth.services.tokens import rotate_refresh_token

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        access_lifetime: int = cfg.get("ACCESS_TOKEN_LIFETIME", 900)
        refresh_lifetime: int = cfg.get("REFRESH_TOKEN_LIFETIME", 604800)
        pair = rotate_refresh_token(token, access_lifetime, refresh_lifetime)

        return AuthPayload(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
        )
