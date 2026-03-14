"""OAuth MFA gating service for ``syntek-auth`` — US009 / US076.

Handles the two-step flow for MFA-gated OAuth providers:

1. ``issue_oauth_pending_session`` — called at the OIDC callback for a
   MFA-gated provider.  Creates a ``PendingOAuthSession`` row and returns a
   ``pending_token`` (the UUID primary key) plus a flag indicating whether
   the user still needs to configure MFA.

2. ``complete_oauth_mfa`` — called when the user submits an MFA proof.
   Validates the proof, deletes the pending row (single-use), and issues a
   full ``TokenPair``.  Returns structured error codes on failure so that the
   client can display a meaningful message without raising exceptions.

Error codes returned by ``complete_oauth_mfa``
----------------------------------------------
``pending_token_not_found``
    No ``PendingOAuthSession`` row exists for the supplied UUID (invalid,
    already consumed, or never created).
``pending_token_expired``
    A row was found but ``expires_at`` is in the past.  The row is deleted.
``invalid_mfa_code``
    The pending session is valid but the MFA proof failed.  The row is
    NOT deleted so the user can retry.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default TTL for a PendingOAuthSession in seconds.
_DEFAULT_PENDING_TTL: int = 600


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OAuthMfaPendingResult:
    """Result returned by ``issue_oauth_pending_session``.

    Attributes
    ----------
    pending_token:
        The UUID string of the created ``PendingOAuthSession`` row.
        Returned to the client to identify the pending challenge.
    mfa_setup_required:
        ``True`` when the user has no MFA method configured and must
        complete MFA setup before the challenge can be satisfied.
    """

    pending_token: str
    mfa_setup_required: bool


@dataclass(frozen=True)
class OAuthMfaCompleteResult:
    """Result returned by ``complete_oauth_mfa``.

    Attributes
    ----------
    success:
        ``True`` when MFA was verified and a ``TokenPair`` was issued.
    token_pair:
        The issued ``TokenPair`` on success; ``None`` on failure.
    error_code:
        Machine-readable failure code; ``None`` on success.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    token_pair: object  # TokenPair | None
    error_code: str | None
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_pending_ttl() -> int:
    """Return the configured pending session TTL in seconds.

    Reads ``SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL']`` from Django settings.
    Falls back to ``_DEFAULT_PENDING_TTL`` (600 s) when the key is absent.
    """
    from django.conf import settings as _settings

    cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    return int(cfg.get("OAUTH_MFA_PENDING_TTL", _DEFAULT_PENDING_TTL))


def _user_has_mfa_configured(user_id: int) -> bool:
    """Return ``True`` when the user has at least one MFA method set up.

    Checks for a stored TOTP secret on the ``TotpDevice`` related model when
    available.  Suppresses all lookup errors — any exception is treated as
    "no MFA configured" so that callers can always proceed safely.

    Parameters
    ----------
    user_id:
        Primary key of the user to inspect.
    """
    UserModel = get_user_model()  # noqa: N806

    # Check for a TOTP device / secret linked to this user.
    with contextlib.suppress(Exception):
        user = UserModel.objects.get(pk=user_id)
        # TotpDevice may not exist in all installations — suppress AttributeError.
        with contextlib.suppress(Exception):
            if user.totp_devices.filter(confirmed=True).exists():  # type: ignore[attr-defined]
                return True

    # Check for backup codes — presence implies MFA was set up at some point.
    with contextlib.suppress(Exception):
        from syntek_auth.models.tokens import BackupCode

        if BackupCode.objects.filter(user_id=user_id).exists():
            return True

    return False


def _verify_mfa_proof(user_id: int, mfa_method: str, mfa_proof: str) -> bool:
    """Verify an MFA proof for ``user_id`` using the specified method.

    Supported methods
    -----------------
    ``email_otp``
        Delegates to ``verify_email_token`` from the email-verification
        service.  Returns ``True`` only when the token is valid and unused.
    ``totp``
        Checks whether the user has a TOTP secret and verifies the code.
        Returns ``False`` when no secret is configured or the code is wrong.
    Any other method
        Returns ``False`` — unsupported proofs are never accepted.

    Parameters
    ----------
    user_id:
        Primary key of the user whose MFA proof is being verified.
    mfa_method:
        The MFA method identifier (``'email_otp'``, ``'totp'``, etc.).
    mfa_proof:
        The proof string submitted by the client (token, code, etc.).
    """
    if mfa_method == "email_otp":
        from syntek_auth.services.email_verification import verify_email_token

        result = verify_email_token(token=mfa_proof)
        return result.success

    if mfa_method == "totp":
        with contextlib.suppress(Exception):
            from syntek_auth.services.totp import verify_totp_code

            return verify_totp_code(user_id=user_id, code=mfa_proof)  # type: ignore[call-arg]

    # Passkey and SMS proofs are not implemented in this iteration — deny.
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def issue_oauth_pending_session(user_id: int, provider: str) -> OAuthMfaPendingResult:
    """Create a ``PendingOAuthSession`` and return the pending token.

    TTL is read from ``SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL']``; defaults to
    ``_DEFAULT_PENDING_TTL`` (600 s) when not configured.

    ``mfa_setup_required`` is set to ``True`` when the user has no MFA method
    configured, indicating they must enrol before the challenge can be
    satisfied.

    Parameters
    ----------
    user_id:
        Primary key of the authenticated user.
    provider:
        The OAuth provider identifier (e.g. ``'google'``, ``'facebook'``).

    Returns
    -------
    OAuthMfaPendingResult
        Contains ``pending_token`` (UUID string) and ``mfa_setup_required``.
    """
    from django.conf import settings as _settings

    from syntek_auth.models.oauth_pending import PendingOAuthSession
    from syntek_auth.services.lookup_tokens import make_provider_token

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    ttl = _get_pending_ttl()
    expires_at = timezone.now() + timedelta(seconds=ttl)

    # Encrypt the provider identifier before storing.
    provider_normalised = provider.strip().lower()
    _cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    _raw_key = _cfg.get("FIELD_KEY", "")
    _field_key: bytes = (
        _raw_key.encode("utf-8") if isinstance(_raw_key, str) else bytes(_raw_key)
    )
    try:
        from syntek_pyo3 import KeyRing, encrypt_field

        _ring = KeyRing()
        _ring.add(1, _field_key)
        encrypted_provider: str = encrypt_field(
            provider_normalised, _ring, "PendingOAuthSession", "provider"
        )
    except ImportError:
        encrypted_provider = provider_normalised  # fallback: tests without pyo3

    session = PendingOAuthSession.objects.create(
        user=user,
        provider=encrypted_provider,
        provider_token=make_provider_token(provider),
        expires_at=expires_at,
    )

    mfa_setup_required = not _user_has_mfa_configured(user_id)

    return OAuthMfaPendingResult(
        pending_token=str(session.id),
        mfa_setup_required=mfa_setup_required,
    )


def complete_oauth_mfa(
    pending_token: str,
    mfa_method: str,
    mfa_proof: str,
) -> OAuthMfaCompleteResult:
    """Validate an MFA proof and exchange the pending token for a full ``TokenPair``.

    Looks up the ``PendingOAuthSession`` by UUID, checks expiry, verifies the
    MFA proof, then deletes the row and issues a ``TokenPair`` on success.

    On a wrong proof the row is NOT deleted so the user may retry.
    On an expired row the row IS deleted.

    Parameters
    ----------
    pending_token:
        The UUID string of the ``PendingOAuthSession`` to consume.
    mfa_method:
        The MFA method identifier (``'email_otp'``, ``'totp'``, etc.).
    mfa_proof:
        The proof string submitted by the client.

    Returns
    -------
    OAuthMfaCompleteResult
        ``success=True`` with a populated ``token_pair`` on success.
        ``success=False`` with an ``error_code`` on any failure.
    """
    import uuid as _uuid

    from syntek_auth.models.oauth_pending import PendingOAuthSession

    # Validate UUID format before touching the DB.
    try:
        _uuid.UUID(pending_token)
    except ValueError, AttributeError:
        return OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="pending_token_not_found",
            message="The pending session token is not valid.",
        )

    # Look up the row.
    try:
        session = PendingOAuthSession.objects.select_related("user").get(
            id=pending_token
        )
    except PendingOAuthSession.DoesNotExist:
        return OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="pending_token_not_found",
            message="The pending session token was not found or has already been used.",
        )

    # Check expiry — delete the row and return expired error.
    if session.expires_at <= timezone.now():
        session.delete()
        return OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="pending_token_expired",
            message=(
                "The pending session has expired. Please restart the OAuth login flow."
            ),
        )

    # Verify the MFA proof.
    user_id: int = session.user_id  # type: ignore[attr-defined]
    if not _verify_mfa_proof(user_id, mfa_method, mfa_proof):
        return OAuthMfaCompleteResult(
            success=False,
            token_pair=None,
            error_code="invalid_mfa_code",
            message="The MFA code is incorrect. Please try again.",
        )

    # MFA verified — consume the pending session and issue a full token pair.
    session.delete()

    from django.conf import settings as _settings

    from syntek_auth.services.tokens import issue_token_pair

    cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    access_lifetime: int = int(cfg.get("ACCESS_TOKEN_LIFETIME", 900))
    refresh_lifetime: int = int(cfg.get("REFRESH_TOKEN_LIFETIME", 604800))
    pair = issue_token_pair(user_id, access_lifetime, refresh_lifetime)

    return OAuthMfaCompleteResult(
        success=True,
        token_pair=pair,
        error_code=None,
        message="MFA verified. Full session issued.",
    )
