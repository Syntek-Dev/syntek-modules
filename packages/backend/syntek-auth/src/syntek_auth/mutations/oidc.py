"""GraphQL OIDC mutations for ``syntek-auth`` — US009.

Strawberry mutations for OIDC authorisation URL generation and callback
handling.  Each resolver delegates to the OIDC service layer.

``oidcAuthUrl`` performs provider discovery, generates state and nonce
values (stored in the session), and returns the authorisation URL.

``oidcCallback`` exchanges the authorisation code for tokens, validates the
ID token (including ``amr`` claim when ``MFA_REQUIRED`` is ``True``), and
issues a Syntek session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

from syntek_auth.types.auth import (
    OidcAuthUrlInput,
    OidcCallbackInput,
    OidcCallbackPayload,
)

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class OidcMutations:
    """Strawberry mutation type for OIDC operations."""

    @strawberry.mutation
    def oidc_auth_url(
        self,
        info: Info,
        input: OidcAuthUrlInput,  # noqa: A002
    ) -> str:
        """Generate the OIDC provider authorisation URL.

        Performs OIDC discovery for the requested provider, generates
        cryptographically random ``state`` and ``nonce`` values, and
        constructs the authorisation redirect URL.  State and nonce are
        stored in the Django session for validation on callback.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            Provider ID and redirect URI.

        Returns
        -------
        str
            The full authorisation URL to redirect the user to.

        Raises
        ------
        ValueError
            If the provider is not configured or discovery fails.
        """
        from syntek_auth.services.oidc import (
            build_auth_url,
            discover_provider,
            generate_nonce,
            generate_state,
            get_provider_config,
        )

        provider_cfg = get_provider_config(input.provider_id)
        discovery_url: str = provider_cfg["discovery_url"]
        client_id: str = provider_cfg["client_id"]

        provider = discover_provider(discovery_url)

        state = generate_state()
        nonce = generate_nonce()

        # Store state and nonce in the session for callback validation.
        request = getattr(info.context, "request", None)
        if request is not None and hasattr(request, "session"):
            request.session["oidc_state"] = state
            request.session["oidc_nonce"] = nonce
            request.session["oidc_provider_id"] = input.provider_id

        return build_auth_url(
            authorisation_endpoint=provider.authorisation_endpoint,
            client_id=client_id,
            redirect_uri=input.redirect_uri,
            state=state,
            nonce=nonce,
        )

    @strawberry.mutation
    def oidc_callback(
        self,
        info: Info,
        input: OidcCallbackInput,  # noqa: A002
    ) -> OidcCallbackPayload:
        """Handle the OIDC provider callback and issue a Syntek session.

        Validates the ``state`` parameter against the session, exchanges the
        authorisation code for tokens, validates the ID token (including
        ``amr`` claim when ``MFA_REQUIRED=True``), and issues a token pair.

        When ``MFA_REQUIRED=True`` and the provider is on the built-in
        allowlist, the ``amr`` claim satisfying MFA is treated as equivalent
        to local MFA and a full session is issued.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            Provider ID, authorisation code, state, and redirect URI.

        Returns
        -------
        AuthPayload
            Access and refresh tokens for the authenticated session.

        Raises
        ------
        ValueError
            If the state is invalid, token exchange fails, the ID token is
            invalid, or the ``amr`` claim is missing/invalid when required.
        """
        from django.conf import settings
        from django.contrib.auth import get_user_model

        from syntek_auth.backends.allowlist import is_mfa_gated_provider
        from syntek_auth.services.mfa import oidc_amr_satisfies_mfa
        from syntek_auth.services.oauth_mfa import issue_oauth_pending_session
        from syntek_auth.services.oidc import (
            discover_provider,
            exchange_code,
            get_provider_config,
            validate_id_token,
        )
        from syntek_auth.services.tokens import issue_token_pair

        request = getattr(info.context, "request", None)
        session = getattr(request, "session", {}) if request else {}

        # Validate state to prevent CSRF.
        expected_state: str | None = session.get("oidc_state")
        if not expected_state or not _constant_time_eq(input.state, expected_state):
            raise ValueError(
                "Invalid OIDC state parameter — possible CSRF attack. "
                "Please restart the login flow."
            )

        expected_nonce: str | None = session.get("oidc_nonce")

        provider_cfg = get_provider_config(input.provider_id)
        discovery_url: str = provider_cfg["discovery_url"]
        client_id: str = provider_cfg["client_id"]
        client_secret: str = provider_cfg["client_secret"]

        provider = discover_provider(discovery_url)

        token_response = exchange_code(
            token_endpoint=provider.token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            code=input.code,
            redirect_uri=input.redirect_uri,
        )

        id_token: str | None = token_response.get("id_token")
        if not id_token:
            raise ValueError("Token response did not include an ID token.")

        claims = validate_id_token(
            id_token=id_token,
            jwks_uri=provider.jwks_uri,
            expected_client_id=client_id,
            expected_issuer=provider.issuer,
            expected_nonce=expected_nonce,
        )

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        mfa_required: bool = bool(cfg.get("MFA_REQUIRED", False))

        if mfa_required and not oidc_amr_satisfies_mfa(claims.amr):
            raise ValueError(
                "The OIDC provider's ID token does not include a valid MFA "
                "authentication method reference. "
                "Please configure MFA at the provider level."
            )

        # Resolve or create a local user for this OIDC subject.
        UserModel = get_user_model()  # noqa: N806
        user = _get_or_create_oidc_user(
            user_model=UserModel,
            provider_id=input.provider_id,
            sub=claims.sub,
            email=claims.email,
        )

        # Clear session OIDC state after successful callback.
        if request is not None and hasattr(request, "session"):
            request.session.pop("oidc_state", None)
            request.session.pop("oidc_nonce", None)
            request.session.pop("oidc_provider_id", None)

        # MFA-gated providers issue a pending session instead of a full token pair.
        if is_mfa_gated_provider(input.provider_id):
            pending = issue_oauth_pending_session(
                user_id=user.pk,  # type: ignore[attr-defined]
                provider=input.provider_id,
            )
            return OidcCallbackPayload(
                mfa_pending=True,
                pending_token=pending.pending_token,
                mfa_setup_required=pending.mfa_setup_required,
            )

        access_lifetime: int = int(cfg.get("ACCESS_TOKEN_LIFETIME", 900))
        refresh_lifetime: int = int(cfg.get("REFRESH_TOKEN_LIFETIME", 604800))
        pair = issue_token_pair(user.pk, access_lifetime, refresh_lifetime)  # type: ignore[attr-defined]

        return OidcCallbackPayload(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            mfa_pending=False,
        )

    @strawberry.mutation
    def complete_social_mfa(
        self,
        _info: Info,
        pending_token: str,
        mfa_method: str,
        mfa_proof: str,
    ) -> OidcCallbackPayload:
        """Exchange a pending OAuth MFA token for a full session.

        Validates the MFA proof supplied for a ``PendingOAuthSession`` and,
        on success, issues a full ``TokenPair``.  Returns a structured error
        payload on any failure so the client can surface a clear message.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused; reserved for future auth checks).
        pending_token:
            The UUID string of the ``PendingOAuthSession`` to consume.
        mfa_method:
            The MFA method identifier (``'email_otp'``, ``'totp'``, etc.).
        mfa_proof:
            The proof string submitted by the client.

        Returns
        -------
        OidcCallbackPayload
            Full session payload on success; pending payload with error fields
            on failure.
        """
        from syntek_auth.services.oauth_mfa import complete_oauth_mfa

        result = complete_oauth_mfa(pending_token, mfa_method, mfa_proof)
        if result.success:
            pair = result.token_pair
            return OidcCallbackPayload(
                access_token=pair.access_token,  # type: ignore[union-attr]
                refresh_token=pair.refresh_token,  # type: ignore[union-attr]
                mfa_pending=False,
            )
        return OidcCallbackPayload(
            mfa_pending=True,
            error_code=result.error_code,
            message=result.message,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _constant_time_eq(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks.

    Parameters
    ----------
    a:
        First string.
    b:
        Second string.

    Returns
    -------
    bool
        ``True`` if the strings are equal.
    """
    import hmac as _hmac

    return _hmac.compare_digest(a, b)


def _get_or_create_oidc_user(
    user_model: object,
    provider_id: str,
    sub: str,
    email: str | None,
) -> object:
    """Resolve or create a local user for the given OIDC subject.

    Attempts to look up an existing user by email when ``email`` is provided.
    When no matching user is found and email is available, creates a new
    unactivated user with an unusable password.

    Parameters
    ----------
    user_model:
        The active user model class.
    provider_id:
        The OIDC provider identifier (stored for future reference).
    sub:
        The subject identifier from the OIDC provider.
    email:
        The user's email address from the ID token (may be ``None``).

    Returns
    -------
    object
        The resolved or newly created user instance.

    Raises
    ------
    ValueError
        If the ID token provides no email and no existing user can be
        resolved via the subject identifier.
    """
    import hashlib

    # Use a deterministic lookup key: sha256(provider_id + ":" + sub).
    lookup_key = hashlib.sha256(
        f"{provider_id}:{sub}".encode(), usedforsecurity=False
    ).hexdigest()

    # Check for existing user by oidc_sub_hash attribute when present.
    if hasattr(user_model, "objects"):
        manager = user_model.objects  # type: ignore[union-attr]

        # Try matching via oidc_sub_hash field when available on the model.
        # The field may not exist — treat absence as a miss and continue.
        import contextlib

        existing = None
        with contextlib.suppress(Exception):
            existing = manager.get(oidc_sub_hash=lookup_key)  # type: ignore[attr-defined]
        if existing is not None:
            return existing

        # Fall back to email lookup.
        if email:
            found = None
            with contextlib.suppress(Exception):
                from syntek_auth.services.lookup_tokens import make_email_token

                found = manager.filter(email_token=make_email_token(email)).first()
            if found is not None:
                return found

            # Create a new user.
            try:
                return manager.create_user(  # type: ignore[attr-defined]
                    email=email, password=None
                )
            except Exception as exc:
                raise ValueError(
                    f"Failed to create OIDC user "
                    f"(provider={provider_id!r}, email={email!r}): {exc}"
                ) from exc

    raise ValueError(
        "Cannot resolve a local user for this OIDC login — "
        "the ID token provided no email address and no subject mapping exists."
    )
