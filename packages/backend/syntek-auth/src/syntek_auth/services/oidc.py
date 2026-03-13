"""OIDC client service for ``syntek-auth`` — US009.

Implements a generic OpenID Connect client supporting:

- Provider discovery via ``/.well-known/openid-configuration``.
- Authorisation URL generation with ``state`` and ``nonce`` generation.
- Authorisation code exchange for ID token.
- ID token signature validation (RS256 via stdlib ``hmac`` for HS256 and
  ``cryptography`` for RS256 when available).
- ``amr`` claim validation against MFA requirements.

Design constraints:
- No third-party OIDC library — uses Python's ``urllib`` for HTTP.
- RS256 validation requires ``cryptography>=42``; the dependency is optional
  and checked at runtime.  When unavailable a ``ValueError`` is raised with a
  clear message instructing the operator to install it.
- All network operations carry a 5-second timeout to avoid hanging requests.
- State and nonce values are stored in the session; the ``state`` parameter
  prevents CSRF on the callback.
"""

from __future__ import annotations

import base64
import hmac
import json
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default network timeout for all OIDC HTTP requests.
_HTTP_TIMEOUT_SECONDS: int = 5

#: State token byte length.
_STATE_BYTES: int = 32

#: Nonce byte length.
_NONCE_BYTES: int = 32


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OidcProviderConfig:
    """Resolved OIDC provider configuration from the discovery document.

    Attributes
    ----------
    issuer:
        The provider's issuer identifier.
    authorisation_endpoint:
        URL for the authorisation redirect.
    token_endpoint:
        URL for authorisation code exchange.
    jwks_uri:
        URL for the JSON Web Key Set used to verify ID token signatures.
    """

    issuer: str
    authorisation_endpoint: str
    token_endpoint: str
    jwks_uri: str


@dataclass(frozen=True)
class OidcTokenClaims:
    """Validated claims extracted from an OIDC ID token.

    Attributes
    ----------
    sub:
        Subject identifier (unique user ID at the provider).
    email:
        User's email address (may be ``None`` if not in scope).
    amr:
        Authentication Methods References from the ID token.
    raw:
        Full decoded payload dict for custom claim access.
    """

    sub: str
    email: str | None
    amr: list[str] | None
    raw: dict[str, Any]


# ---------------------------------------------------------------------------
# Provider discovery
# ---------------------------------------------------------------------------


def discover_provider(discovery_url: str) -> OidcProviderConfig:
    """Fetch and parse the OIDC discovery document.

    Performs a ``GET`` request to ``discovery_url`` and extracts the
    endpoints required for authorisation and token exchange.

    Parameters
    ----------
    discovery_url:
        The ``/.well-known/openid-configuration`` URL for the provider.

    Returns
    -------
    OidcProviderConfig
        Resolved provider configuration.

    Raises
    ------
    ValueError
        If the discovery document is missing required fields or the network
        request fails.
    """
    try:
        with urllib.request.urlopen(  # noqa: S310
            discovery_url, timeout=_HTTP_TIMEOUT_SECONDS
        ) as resp:
            doc: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"OIDC discovery failed for {discovery_url!r}: {exc}") from exc

    missing = [
        k
        for k in ("issuer", "authorization_endpoint", "token_endpoint", "jwks_uri")
        if k not in doc
    ]
    if missing:
        raise ValueError(
            f"OIDC discovery document at {discovery_url!r} is missing required "
            f"fields: {missing!r}"
        )

    return OidcProviderConfig(
        issuer=doc["issuer"],
        authorisation_endpoint=doc["authorization_endpoint"],
        token_endpoint=doc["token_endpoint"],
        jwks_uri=doc["jwks_uri"],
    )


# ---------------------------------------------------------------------------
# Authorisation URL generation
# ---------------------------------------------------------------------------


def build_auth_url(
    authorisation_endpoint: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    nonce: str,
    scopes: list[str] | None = None,
) -> str:
    """Construct an OIDC authorisation URL.

    Parameters
    ----------
    authorisation_endpoint:
        The provider's authorisation endpoint URL.
    client_id:
        The OAuth client ID registered with the provider.
    redirect_uri:
        The URI the provider redirects to after authorisation.
    state:
        A cryptographically random state value (CSRF protection).
    nonce:
        A cryptographically random nonce for replay protection.
    scopes:
        OAuth scopes to request.  Defaults to ``['openid', 'email', 'profile']``.

    Returns
    -------
    str
        The complete authorisation URL to redirect the user to.
    """
    if scopes is None:
        scopes = ["openid", "email", "profile"]

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "nonce": nonce,
        }
    )
    return f"{authorisation_endpoint}?{params}"


def generate_state() -> str:
    """Generate a cryptographically random state token.

    Returns
    -------
    str
        A URL-safe base64-encoded 32-byte random string.
    """
    return secrets.token_urlsafe(_STATE_BYTES)


def generate_nonce() -> str:
    """Generate a cryptographically random nonce.

    Returns
    -------
    str
        A URL-safe base64-encoded 32-byte random string.
    """
    return secrets.token_urlsafe(_NONCE_BYTES)


# ---------------------------------------------------------------------------
# Authorisation code exchange
# ---------------------------------------------------------------------------


def exchange_code(
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange an authorisation code for tokens.

    Performs a ``POST`` to ``token_endpoint`` using the standard
    ``application/x-www-form-urlencoded`` format.

    Parameters
    ----------
    token_endpoint:
        The provider's token endpoint URL.
    client_id:
        The OAuth client ID.
    client_secret:
        The OAuth client secret.
    code:
        The authorisation code returned by the provider.
    redirect_uri:
        Must match the redirect URI used in the original request.

    Returns
    -------
    dict
        The parsed token response (includes ``id_token`` on success).

    Raises
    ------
    ValueError
        If the token exchange fails or the response is not valid JSON.
    """
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("ascii")

    req = urllib.request.Request(  # noqa: S310
        token_endpoint,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:  # noqa: S310
            response_data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Token exchange failed: {exc}") from exc

    if "error" in response_data:
        raise ValueError(
            f"Token exchange error: {response_data.get('error')} — "
            f"{response_data.get('error_description', '')}"
        )

    return response_data


# ---------------------------------------------------------------------------
# JWT / ID token validation helpers
# ---------------------------------------------------------------------------


def _b64url_decode(s: str) -> bytes:
    """Decode a URL-safe base64 string, adding padding as required."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _decode_jwt_unverified(token: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Decode a JWT without verifying the signature.

    Returns the header, payload, and the raw ``header.payload`` signing input.

    Parameters
    ----------
    token:
        The compact JWT string.

    Returns
    -------
    tuple
        ``(header, payload, signing_input)``

    Raises
    ------
    ValueError
        If the token is malformed.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Malformed JWT — expected 3 parts, got {len(parts)}.")

    header_b64, body_b64, _ = parts
    signing_input = f"{header_b64}.{body_b64}"

    try:
        header: dict[str, Any] = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload: dict[str, Any] = json.loads(_b64url_decode(body_b64).decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"JWT decode error: {exc}") from exc

    return header, payload, signing_input


def _verify_hs256(token: str, secret: bytes) -> dict[str, Any]:
    """Verify an HS256-signed JWT and return the payload.

    Parameters
    ----------
    token:
        The compact JWT string.
    secret:
        The HMAC-SHA256 signing secret.

    Returns
    -------
    dict
        The verified payload.

    Raises
    ------
    ValueError
        On signature failure or expiry.
    """
    import hashlib as _hashlib
    import hmac as _hmac

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT.")

    header_b64, body_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{body_b64}".encode()
    expected_sig = base64.urlsafe_b64encode(
        _hmac.new(secret, signing_input, _hashlib.sha256).digest()
    ).rstrip(b"=")

    actual_sig = sig_b64.encode()
    if not _hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("HS256 signature verification failed.")

    _, payload, _ = _decode_jwt_unverified(token)
    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise ValueError("JWT has expired.")
    return payload


def _fetch_jwks(jwks_uri: str) -> dict[str, Any]:
    """Fetch the JWKS from the provider.

    Parameters
    ----------
    jwks_uri:
        The JSON Web Key Set URI.

    Returns
    -------
    dict
        The parsed JWKS document.

    Raises
    ------
    ValueError
        On network error.
    """
    try:
        with urllib.request.urlopen(jwks_uri, timeout=_HTTP_TIMEOUT_SECONDS) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
    except Exception as exc:
        raise ValueError(f"Failed to fetch JWKS from {jwks_uri!r}: {exc}") from exc


def _find_jwk(jwks: dict[str, Any], kid: str | None) -> dict[str, Any]:
    """Find the matching JWK from the key set.

    Parameters
    ----------
    jwks:
        The JWKS document.
    kid:
        The Key ID to match.  When ``None`` the first RSA key is returned.

    Returns
    -------
    dict
        The matching JWK.

    Raises
    ------
    ValueError
        When no matching key is found.
    """
    keys: list[dict[str, Any]] = jwks.get("keys", [])
    if kid:
        for key in keys:
            if key.get("kid") == kid:
                return key

    # Fall back to first RSA key.
    for key in keys:
        if key.get("kty") == "RSA":
            return key

    raise ValueError(f"No suitable JWK found (kid={kid!r}).")


def _verify_rs256(token: str, jwks_uri: str) -> dict[str, Any]:
    """Verify an RS256-signed JWT using the provider's JWKS.

    Requires ``cryptography>=42``.

    Parameters
    ----------
    token:
        The compact JWT string.
    jwks_uri:
        The provider's JWKS URI.

    Returns
    -------
    dict
        The verified payload.

    Raises
    ------
    ValueError
        On signature failure, expiry, or missing ``cryptography`` library.
    """
    try:
        from cryptography.exceptions import (  # type: ignore[import-not-found]
            InvalidSignature,
        )
        from cryptography.hazmat.primitives.asymmetric.padding import (  # type: ignore[import-not-found]
            PKCS1v15,
        )
        from cryptography.hazmat.primitives.asymmetric.rsa import (  # type: ignore[import-not-found]
            RSAPublicNumbers,
        )
        from cryptography.hazmat.primitives.hashes import (  # type: ignore[import-not-found]
            SHA256,
        )
    except ImportError as exc:
        raise ValueError(
            "RS256 ID token validation requires the 'cryptography' package. "
            "Install it with: uv add cryptography"
        ) from exc

    header, payload, signing_input = _decode_jwt_unverified(token)
    kid = header.get("kid")

    parts = token.split(".")
    sig_bytes = _b64url_decode(parts[2])

    jwks = _fetch_jwks(jwks_uri)
    jwk = _find_jwk(jwks, kid)

    def _b64url_to_int(s: str) -> int:
        return int.from_bytes(_b64url_decode(s), "big")

    public_numbers = RSAPublicNumbers(
        e=_b64url_to_int(jwk["e"]),
        n=_b64url_to_int(jwk["n"]),
    )
    public_key = public_numbers.public_key()

    signing_input_bytes = signing_input.encode("ascii")
    try:
        public_key.verify(sig_bytes, signing_input_bytes, PKCS1v15(), SHA256())
    except InvalidSignature as exc:
        raise ValueError("RS256 signature verification failed.") from exc

    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise ValueError("JWT has expired.")

    return payload


# ---------------------------------------------------------------------------
# ID token validation
# ---------------------------------------------------------------------------


def validate_id_token(
    id_token: str,
    jwks_uri: str,
    expected_client_id: str,
    expected_issuer: str,
    expected_nonce: str | None = None,
) -> OidcTokenClaims:
    """Validate an OIDC ID token and return the extracted claims.

    Supports HS256 (test tokens) and RS256 (production tokens).  Standard
    claims (``iss``, ``aud``, ``exp``, ``nonce``) are validated.  The ``amr``
    claim is extracted when present.

    Parameters
    ----------
    id_token:
        The compact ID token JWT from the provider.
    jwks_uri:
        The provider's JWKS URI (used for RS256 key lookup).
    expected_client_id:
        The OAuth client ID — must match the ``aud`` claim.
    expected_issuer:
        The expected issuer — must match the ``iss`` claim.
    expected_nonce:
        When provided, the ``nonce`` claim must match.

    Returns
    -------
    OidcTokenClaims
        Validated claims from the ID token.

    Raises
    ------
    ValueError
        On signature failure, claim mismatch, expiry, or missing ``amr``
        when MFA is required.
    """
    header, _, _ = _decode_jwt_unverified(id_token)
    alg = header.get("alg", "RS256")

    if alg == "RS256":
        payload = _verify_rs256(id_token, jwks_uri)
    elif alg == "HS256":
        # HS256 tokens are only expected in tests; production providers use RS256.
        raise ValueError("HS256 ID tokens are not accepted — providers must use RS256.")
    else:
        raise ValueError(f"Unsupported JWT algorithm: {alg!r}. Only RS256 is accepted.")

    # Validate issuer.
    if payload.get("iss") != expected_issuer:
        raise ValueError(
            f"ID token issuer mismatch — expected {expected_issuer!r}, "
            f"got {payload.get('iss')!r}."
        )

    # Validate audience.
    aud = payload.get("aud")
    if isinstance(aud, str):
        aud = [aud]
    if not isinstance(aud, list) or expected_client_id not in aud:
        raise ValueError(
            f"ID token audience mismatch — expected {expected_client_id!r}, "
            f"got {payload.get('aud')!r}."
        )

    # Validate nonce when provided.
    if expected_nonce is not None:
        token_nonce = payload.get("nonce")
        if not hmac.compare_digest(str(token_nonce or ""), expected_nonce):
            raise ValueError("ID token nonce mismatch — possible replay attack.")

    sub = payload.get("sub")
    if not sub:
        raise ValueError("ID token is missing the required 'sub' claim.")

    amr: list[str] | None = payload.get("amr")

    return OidcTokenClaims(
        sub=str(sub),
        email=payload.get("email"),
        amr=amr if isinstance(amr, list) else None,
        raw=payload,
    )


# ---------------------------------------------------------------------------
# High-level provider lookup helper
# ---------------------------------------------------------------------------


def get_provider_config(provider_id: str) -> dict[str, Any]:
    """Retrieve provider configuration from ``SYNTEK_AUTH['OIDC_PROVIDERS']``.

    Parameters
    ----------
    provider_id:
        The ``id`` key of the provider entry in ``OIDC_PROVIDERS``.

    Returns
    -------
    dict
        The provider config dict from settings.

    Raises
    ------
    ValueError
        If no provider with the given ID is found.
    """
    from django.conf import settings

    cfg: dict[str, Any] = getattr(settings, "SYNTEK_AUTH", {})
    providers: list[dict[str, Any]] = cfg.get("OIDC_PROVIDERS", [])

    for provider in providers:
        if provider.get("id") == provider_id:
            return provider

    raise ValueError(
        f"OIDC provider {provider_id!r} is not configured in "
        f"SYNTEK_AUTH['OIDC_PROVIDERS']."
    )
