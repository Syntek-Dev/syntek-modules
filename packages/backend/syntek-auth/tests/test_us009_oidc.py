"""US009 — OIDC service tests for ``syntek-auth``.

Tests cover the full OIDC client implementation in ``syntek_auth.services.oidc``:

- Provider discovery (``discover_provider``) — success and failure cases
- Auth URL construction (``build_auth_url``)
- Random token generation (``generate_state``, ``generate_nonce``)
- Authorisation code exchange (``exchange_code``)
- JWT decoding helpers (``_b64url_decode``, ``_decode_jwt_unverified``)
- HS256 JWT verification (``_verify_hs256``)
- JWKS fetching and JWK selection (``_fetch_jwks``, ``_find_jwk``)
- RS256 JWT verification (``_verify_rs256``) — uses a real RSA key pair
- Full ID token validation (``validate_id_token``)
- Provider config lookup (``get_provider_config``)

All HTTP calls in the OIDC module use ``urllib.request.urlopen``.  Tests mock
it at the module level to avoid network traffic.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from syntek_auth.services.oidc import (
    OidcProviderConfig,
    OidcTokenClaims,
    _b64url_decode,
    _decode_jwt_unverified,
    _fetch_jwks,
    _find_jwk,
    _verify_es256,
    _verify_hs256,
    _verify_rs256,
    build_auth_url,
    discover_provider,
    exchange_code,
    generate_nonce,
    generate_state,
    get_provider_config,
    validate_id_token,
)

# ---------------------------------------------------------------------------
# Helpers — JWT construction
# ---------------------------------------------------------------------------


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_hs256_jwt(
    payload: dict[str, Any],
    secret: bytes,
    header: dict[str, Any] | None = None,
) -> str:
    """Construct a minimal HS256-signed JWT."""
    if header is None:
        header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header).encode())
    body_b64 = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header_b64}.{body_b64}".encode()
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{body_b64}.{sig_b64}"


def _make_rs256_jwt(
    payload: dict[str, Any],
    private_key: object,
    kid: str | None = None,
) -> str:
    """Construct a real RS256-signed JWT using the cryptography library."""
    from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
    from cryptography.hazmat.primitives.hashes import SHA256

    header: dict[str, Any] = {"alg": "RS256", "typ": "JWT"}
    if kid is not None:
        header["kid"] = kid

    header_b64 = _b64url_encode(json.dumps(header).encode())
    body_b64 = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header_b64}.{body_b64}".encode("ascii")

    sig = private_key.sign(signing_input, PKCS1v15(), SHA256())  # type: ignore[union-attr]
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{body_b64}.{sig_b64}"


def _jwk_from_public_key(public_key: object, kid: str | None = None) -> dict[str, Any]:
    """Build a minimal JWK dict from an RSA public key."""
    pub_numbers = public_key.public_numbers()  # type: ignore[union-attr]

    def _int_to_b64url(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        return _b64url_encode(value.to_bytes(length, "big"))

    jwk: dict[str, Any] = {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": _int_to_b64url(pub_numbers.n),
        "e": _int_to_b64url(pub_numbers.e),
    }
    if kid is not None:
        jwk["kid"] = kid
    return jwk


def _make_urlopen_mock(response_body: bytes, status: int = 200) -> MagicMock:
    """Return a mock ``urlopen`` context manager that yields the given bytes."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.status = status
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_resp)
    mock_cm.__exit__ = MagicMock(return_value=False)
    return mock_cm


def _generate_rsa_key_pair():
    """Generate a 2048-bit RSA key pair for testing."""
    from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


# ---------------------------------------------------------------------------
# _b64url_decode
# ---------------------------------------------------------------------------


class TestB64urlDecode:
    """Tests for the internal ``_b64url_decode`` helper."""

    def test_decodes_string_without_padding(self) -> None:
        """URL-safe base64 without padding must decode correctly."""
        original = b"hello world"
        encoded = base64.urlsafe_b64encode(original).rstrip(b"=").decode()
        assert _b64url_decode(encoded) == original

    def test_decodes_string_with_one_missing_pad(self) -> None:
        """Input missing one padding character must still decode correctly."""
        original = b"test"
        encoded = base64.urlsafe_b64encode(original).rstrip(b"=").decode()
        assert _b64url_decode(encoded) == original

    def test_decodes_empty_string(self) -> None:
        """An empty string must decode to empty bytes."""
        assert _b64url_decode("") == b""

    def test_decodes_url_safe_chars(self) -> None:
        """URL-safe characters ('-' and '_') must be handled correctly."""
        data = bytes(range(256))
        encoded = base64.urlsafe_b64encode(data).rstrip(b"=").decode()
        assert _b64url_decode(encoded) == data


# ---------------------------------------------------------------------------
# _decode_jwt_unverified
# ---------------------------------------------------------------------------


class TestDecodeJwtUnverified:
    """Tests for the internal ``_decode_jwt_unverified`` helper."""

    def test_decodes_valid_jwt(self) -> None:
        """A well-formed JWT must return header, payload, and signing input."""
        payload = {"sub": "1234", "exp": int(time.time()) + 3600}
        token = _make_hs256_jwt(payload, b"secret")
        header, decoded_payload, signing_input = _decode_jwt_unverified(token)
        assert header["alg"] == "HS256"
        assert decoded_payload["sub"] == "1234"
        assert "." in signing_input

    def test_raises_on_malformed_token(self) -> None:
        """A token that does not have three dot-separated parts must raise ValueError."""
        with pytest.raises(ValueError, match="Malformed JWT"):
            _decode_jwt_unverified("only.two")

    def test_raises_on_invalid_base64(self) -> None:
        """A token with corrupt base64 in the header or body must raise ValueError."""
        with pytest.raises(ValueError, match=r"base64|decode|Malformed"):
            _decode_jwt_unverified("!!!.!!.!!")

    def test_signing_input_format(self) -> None:
        """The signing input must be ``header_b64.body_b64`` without the signature."""
        payload = {"sub": "abc"}
        token = _make_hs256_jwt(payload, b"secret")
        parts = token.split(".")
        _, _, signing_input = _decode_jwt_unverified(token)
        assert signing_input == f"{parts[0]}.{parts[1]}"


# ---------------------------------------------------------------------------
# _verify_hs256
# ---------------------------------------------------------------------------


class TestVerifyHs256:
    """Tests for the internal ``_verify_hs256`` function."""

    def test_valid_token_returns_payload(self) -> None:
        """A correctly signed HS256 token must return the payload dict."""
        payload = {"sub": "user1", "exp": int(time.time()) + 3600}
        secret = b"my-secret-key"
        token = _make_hs256_jwt(payload, secret)
        result = _verify_hs256(token, secret)
        assert result["sub"] == "user1"

    def test_wrong_secret_raises(self) -> None:
        """A token signed with a different secret must raise ValueError."""
        payload = {"sub": "user1"}
        token = _make_hs256_jwt(payload, b"correct-secret")
        with pytest.raises(ValueError, match="HS256 signature verification failed"):
            _verify_hs256(token, b"wrong-secret")

    def test_expired_token_raises(self) -> None:
        """A token whose ``exp`` claim is in the past must raise ValueError."""
        payload = {"sub": "user1", "exp": int(time.time()) - 60}
        secret = b"my-secret-key"
        token = _make_hs256_jwt(payload, secret)
        with pytest.raises(ValueError, match="expired"):
            _verify_hs256(token, secret)

    def test_token_without_exp_is_accepted(self) -> None:
        """A token with no ``exp`` claim must not raise an expiry error."""
        payload = {"sub": "no_expiry"}
        secret = b"key"
        token = _make_hs256_jwt(payload, secret)
        result = _verify_hs256(token, secret)
        assert result["sub"] == "no_expiry"

    def test_malformed_token_raises(self) -> None:
        """A token without three dot-separated parts must raise ValueError."""
        with pytest.raises(ValueError, match=r"Malformed|malformed|parts"):
            _verify_hs256("not.a.jwt.with.toomany.parts", b"key")


# ---------------------------------------------------------------------------
# discover_provider
# ---------------------------------------------------------------------------


class TestDiscoverProvider:
    """Tests for ``discover_provider``."""

    _VALID_DOCUMENT: dict[str, str] = {  # noqa: RUF012
        "issuer": "https://accounts.example.com",
        "authorization_endpoint": "https://accounts.example.com/auth",
        "token_endpoint": "https://accounts.example.com/token",
        "jwks_uri": "https://accounts.example.com/jwks",
    }

    def test_returns_oidc_provider_config(self) -> None:
        """A valid discovery document must return an ``OidcProviderConfig``."""
        mock_cm = _make_urlopen_mock(json.dumps(self._VALID_DOCUMENT).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = discover_provider(
                "https://accounts.example.com/.well-known/openid-configuration"
            )
        assert isinstance(result, OidcProviderConfig)

    def test_maps_fields_correctly(self) -> None:
        """All fields from the discovery document must be mapped to the dataclass."""
        mock_cm = _make_urlopen_mock(json.dumps(self._VALID_DOCUMENT).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = discover_provider(
                "https://accounts.example.com/.well-known/openid-configuration"
            )
        assert result.issuer == "https://accounts.example.com"
        assert result.authorisation_endpoint == "https://accounts.example.com/auth"
        assert result.token_endpoint == "https://accounts.example.com/token"  # noqa: S105
        assert result.jwks_uri == "https://accounts.example.com/jwks"

    def test_raises_on_missing_field(self) -> None:
        """A discovery document missing ``jwks_uri`` must raise ValueError."""
        doc = {k: v for k, v in self._VALID_DOCUMENT.items() if k != "jwks_uri"}
        mock_cm = _make_urlopen_mock(json.dumps(doc).encode())
        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="missing required fields"),
        ):
            discover_provider(
                "https://accounts.example.com/.well-known/openid-configuration"
            )

    def test_raises_on_missing_multiple_fields(self) -> None:
        """A discovery document missing several required fields must raise ValueError."""
        doc = {"issuer": "https://accounts.example.com"}
        mock_cm = _make_urlopen_mock(json.dumps(doc).encode())
        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="missing required fields"),
        ):
            discover_provider(
                "https://accounts.example.com/.well-known/openid-configuration"
            )

    def test_raises_on_network_error(self) -> None:
        """A network error during discovery must raise ValueError."""
        with (
            patch("urllib.request.urlopen", side_effect=OSError("connection refused")),
            pytest.raises(ValueError, match="OIDC discovery failed"),
        ):
            discover_provider(
                "https://accounts.example.com/.well-known/openid-configuration"
            )


# ---------------------------------------------------------------------------
# build_auth_url
# ---------------------------------------------------------------------------


class TestBuildAuthUrl:
    """Tests for ``build_auth_url``."""

    def test_returns_string_starting_with_endpoint(self) -> None:
        """The auth URL must start with the authorisation endpoint."""
        url = build_auth_url(
            "https://accounts.example.com/auth",
            "client123",
            "https://app.example.com/callback",
            "state_value",
            "nonce_value",
        )
        assert url.startswith("https://accounts.example.com/auth?")

    def test_contains_required_params(self) -> None:
        """The URL must include ``response_type``, ``client_id``, ``state``, and ``nonce``."""
        url = build_auth_url(
            "https://accounts.example.com/auth",
            "my_client",
            "https://app.example.com/callback",
            "my_state",
            "my_nonce",
        )
        assert "response_type=code" in url
        assert "client_id=my_client" in url
        assert "state=my_state" in url
        assert "nonce=my_nonce" in url

    def test_default_scopes_include_openid(self) -> None:
        """Default scopes must include ``openid``."""
        url = build_auth_url(
            "https://accounts.example.com/auth",
            "client",
            "https://app.example.com/callback",
            "state",
            "nonce",
        )
        assert "openid" in url

    def test_custom_scopes_used_when_provided(self) -> None:
        """Custom scopes must appear in the URL instead of the defaults."""
        url = build_auth_url(
            "https://accounts.example.com/auth",
            "client",
            "https://app.example.com/callback",
            "state",
            "nonce",
            scopes=["openid", "custom_scope"],
        )
        assert "custom_scope" in url


# ---------------------------------------------------------------------------
# generate_state / generate_nonce
# ---------------------------------------------------------------------------


class TestGenerateStateAndNonce:
    """Tests for ``generate_state`` and ``generate_nonce``."""

    def test_generate_state_returns_string(self) -> None:
        """``generate_state`` must return a string."""
        assert isinstance(generate_state(), str)

    def test_generate_state_is_unique(self) -> None:
        """Two successive calls must return different values."""
        assert generate_state() != generate_state()

    def test_generate_state_minimum_length(self) -> None:
        """The state token must be at least 32 characters (URL-safe base64 of 32 bytes)."""
        assert len(generate_state()) >= 32

    def test_generate_nonce_returns_string(self) -> None:
        """``generate_nonce`` must return a string."""
        assert isinstance(generate_nonce(), str)

    def test_generate_nonce_is_unique(self) -> None:
        """Two successive calls must return different values."""
        assert generate_nonce() != generate_nonce()

    def test_generate_nonce_minimum_length(self) -> None:
        """The nonce must be at least 32 characters."""
        assert len(generate_nonce()) >= 32


# ---------------------------------------------------------------------------
# exchange_code
# ---------------------------------------------------------------------------


class TestExchangeCode:
    """Tests for ``exchange_code``."""

    def test_successful_exchange_returns_dict(self) -> None:
        """A successful token exchange must return the parsed response dict."""
        response_body = json.dumps(
            {"id_token": "tok.en.here", "access_token": "access"}
        ).encode()
        mock_cm = _make_urlopen_mock(response_body)
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = exchange_code(
                "https://accounts.example.com/token",
                "client_id",
                "client_secret",
                "auth_code",
                "https://app.example.com/callback",
            )
        assert "id_token" in result

    def test_error_response_raises(self) -> None:
        """A response containing an ``error`` field must raise ValueError."""
        response_body = json.dumps(
            {"error": "invalid_grant", "error_description": "Code expired"}
        ).encode()
        mock_cm = _make_urlopen_mock(response_body)
        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="Token exchange error"),
        ):
            exchange_code(
                "https://accounts.example.com/token",
                "client_id",
                "client_secret",
                "expired_code",
                "https://app.example.com/callback",
            )

    def test_network_error_raises(self) -> None:
        """A network error during token exchange must raise ValueError."""
        with (
            patch("urllib.request.urlopen", side_effect=OSError("timeout")),
            pytest.raises(ValueError, match="Token exchange failed"),
        ):
            exchange_code(
                "https://accounts.example.com/token",
                "client_id",
                "client_secret",
                "code",
                "https://app.example.com/callback",
            )


# ---------------------------------------------------------------------------
# _fetch_jwks
# ---------------------------------------------------------------------------


class TestFetchJwks:
    """Tests for the internal ``_fetch_jwks`` helper."""

    def test_returns_parsed_dict(self) -> None:
        """A successful fetch must return the parsed JWKS document."""
        jwks = {"keys": [{"kty": "RSA", "kid": "key1"}]}
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = _fetch_jwks("https://accounts.example.com/jwks")
        assert result["keys"][0]["kid"] == "key1"

    def test_network_error_raises(self) -> None:
        """A network error must raise ValueError."""
        with (
            patch("urllib.request.urlopen", side_effect=OSError("timeout")),
            pytest.raises(ValueError, match="Failed to fetch JWKS"),
        ):
            _fetch_jwks("https://accounts.example.com/jwks")


# ---------------------------------------------------------------------------
# _find_jwk
# ---------------------------------------------------------------------------


class TestFindJwk:
    """Tests for the internal ``_find_jwk`` helper."""

    def _make_jwks(self) -> dict[str, Any]:
        return {
            "keys": [
                {"kty": "RSA", "kid": "key1", "alg": "RS256"},
                {"kty": "RSA", "kid": "key2", "alg": "RS256"},
            ]
        }

    def test_finds_key_by_kid(self) -> None:
        """When a matching ``kid`` exists, that key must be returned."""
        jwks = self._make_jwks()
        key = _find_jwk(jwks, "key2")
        assert key["kid"] == "key2"

    def test_falls_back_to_first_rsa_key_when_kid_none(self) -> None:
        """When ``kid`` is None, the first RSA key must be returned."""
        jwks = self._make_jwks()
        key = _find_jwk(jwks, None)
        assert key["kid"] == "key1"

    def test_falls_back_to_first_rsa_key_when_kid_not_found(self) -> None:
        """When the given ``kid`` is not found, the first RSA key must be returned."""
        jwks = self._make_jwks()
        key = _find_jwk(jwks, "nonexistent_kid")
        assert key["kty"] == "RSA"

    def test_raises_when_no_rsa_key_available(self) -> None:
        """When no RSA key exists in the JWKS, ``ValueError`` must be raised."""
        jwks: dict[str, Any] = {"keys": [{"kty": "EC", "kid": "ec_key"}]}
        with pytest.raises(ValueError, match="No suitable JWK found"):
            _find_jwk(jwks, None)

    def test_raises_when_keys_empty(self) -> None:
        """An empty ``keys`` list must raise ValueError."""
        with pytest.raises(ValueError, match="No suitable JWK found"):
            _find_jwk({"keys": []}, None)


# ---------------------------------------------------------------------------
# _verify_rs256
# ---------------------------------------------------------------------------


class TestVerifyRs256:
    """Tests for the internal ``_verify_rs256`` function using a real RSA key pair."""

    def _make_valid_token_and_jwks(
        self,
        payload: dict[str, Any],
        kid: str = "test-key-1",
    ) -> tuple[str, dict[str, Any]]:
        """Return a signed RS256 token and the corresponding JWKS document."""
        private_key, public_key = _generate_rsa_key_pair()
        token = _make_rs256_jwt(payload, private_key, kid=kid)
        jwk = _jwk_from_public_key(public_key, kid=kid)
        jwks = {"keys": [jwk]}
        return token, jwks

    def test_valid_rs256_token_returns_payload(self) -> None:
        """A correctly signed RS256 token must return the payload."""
        payload = {"sub": "rs256user", "exp": int(time.time()) + 3600}
        token, jwks = self._make_valid_token_and_jwks(payload)

        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = _verify_rs256(token, "https://accounts.example.com/jwks")
        assert result["sub"] == "rs256user"

    def test_tampered_signature_raises(self) -> None:
        """A token with a tampered signature must raise ValueError."""
        payload = {"sub": "user1", "exp": int(time.time()) + 3600}
        token, jwks = self._make_valid_token_and_jwks(payload)

        # Tamper with the signature portion.
        parts = token.split(".")
        parts[2] = parts[2][:-4] + "XXXX"
        bad_token = ".".join(parts)

        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="RS256 signature verification failed"),
        ):
            _verify_rs256(bad_token, "https://accounts.example.com/jwks")

    def test_expired_token_raises(self) -> None:
        """A token with an expired ``exp`` claim must raise ValueError."""
        payload = {"sub": "user1", "exp": int(time.time()) - 60}
        token, jwks = self._make_valid_token_and_jwks(payload)

        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="expired"),
        ):
            _verify_rs256(token, "https://accounts.example.com/jwks")

    def test_token_without_exp_is_accepted(self) -> None:
        """A token with no ``exp`` claim must not raise an expiry error."""
        payload = {"sub": "no_expiry"}
        token, jwks = self._make_valid_token_and_jwks(payload)

        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = _verify_rs256(token, "https://accounts.example.com/jwks")
        assert result["sub"] == "no_expiry"

    def test_key_matched_by_kid(self) -> None:
        """The correct key must be selected from the JWKS when ``kid`` matches."""
        payload = {"sub": "kid_user", "exp": int(time.time()) + 3600}
        kid = "specific-key-id"
        token, jwks = self._make_valid_token_and_jwks(payload, kid=kid)

        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())
        with patch("urllib.request.urlopen", return_value=mock_cm):
            result = _verify_rs256(token, "https://accounts.example.com/jwks")
        assert result["sub"] == "kid_user"


# ---------------------------------------------------------------------------
# validate_id_token
# ---------------------------------------------------------------------------


class TestValidateIdToken:
    """Tests for the public ``validate_id_token`` function."""

    def _make_rs256_token_and_jwks(
        self,
        payload: dict[str, Any],
        kid: str = "test-kid",
    ) -> tuple[str, dict[str, Any]]:
        """Return a real RS256 token and its corresponding JWKS."""
        private_key, public_key = _generate_rsa_key_pair()
        token = _make_rs256_jwt(payload, private_key, kid=kid)
        jwk = _jwk_from_public_key(public_key, kid=kid)
        return token, {"keys": [jwk]}

    def test_valid_rs256_token_returns_claims(self) -> None:
        """A valid RS256 ID token must return an ``OidcTokenClaims`` instance."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "sub": "user123",
            "email": "user@example.com",
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with patch("urllib.request.urlopen", return_value=mock_cm):
            claims = validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

        assert isinstance(claims, OidcTokenClaims)
        assert claims.sub == "user123"
        assert claims.email == "user@example.com"

    def test_issuer_mismatch_raises(self) -> None:
        """A token with a mismatched ``iss`` claim must raise ValueError."""
        payload = {
            "iss": "https://wrong-issuer.com",
            "aud": "my_client_id",
            "sub": "user123",
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="issuer mismatch"),
        ):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

    def test_audience_mismatch_raises(self) -> None:
        """A token with a mismatched ``aud`` claim must raise ValueError."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "wrong_client_id",
            "sub": "user123",
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="audience mismatch"),
        ):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

    def test_nonce_mismatch_raises(self) -> None:
        """A token with a mismatched ``nonce`` claim must raise ValueError."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "sub": "user123",
            "nonce": "correct_nonce",
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="nonce mismatch"),
        ):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
                expected_nonce="wrong_nonce",
            )

    def test_nonce_matches_when_correct(self) -> None:
        """A token with a matching ``nonce`` must be accepted."""
        nonce = "correct_nonce_value"
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "sub": "user123",
            "nonce": nonce,
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with patch("urllib.request.urlopen", return_value=mock_cm):
            claims = validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
                expected_nonce=nonce,
            )
        assert claims.sub == "user123"

    def test_missing_sub_claim_raises(self) -> None:
        """A token without a ``sub`` claim must raise ValueError."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "exp": int(time.time()) + 3600,
            # No "sub"
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with (
            patch("urllib.request.urlopen", return_value=mock_cm),
            pytest.raises(ValueError, match="'sub' claim"),
        ):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

    def test_hs256_token_rejected(self) -> None:
        """An HS256 ID token must be rejected at the public API level."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "sub": "user123",
            "exp": int(time.time()) + 3600,
        }
        token = _make_hs256_jwt(payload, b"shared-secret")

        with pytest.raises(ValueError, match="HS256"):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

    def test_unsupported_algorithm_rejected(self) -> None:
        """A token using an unsupported algorithm must raise ValueError."""
        payload = {"sub": "user1"}
        header = {"alg": "none", "typ": "JWT"}
        header_b64 = _b64url_encode(json.dumps(header).encode())
        body_b64 = _b64url_encode(json.dumps(payload).encode())
        token = f"{header_b64}.{body_b64}."

        with pytest.raises(ValueError, match="Unsupported JWT algorithm"):
            validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )

    def test_amr_claim_extracted_when_present(self) -> None:
        """When ``amr`` is present as a list, it must be returned in claims."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": "my_client_id",
            "sub": "user123",
            "amr": ["mfa", "pwd"],
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with patch("urllib.request.urlopen", return_value=mock_cm):
            claims = validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )
        assert claims.amr == ["mfa", "pwd"]

    def test_audience_as_list_accepted(self) -> None:
        """A token with ``aud`` as a list containing the client ID must be accepted."""
        payload = {
            "iss": "https://accounts.example.com",
            "aud": ["my_client_id", "other_client"],
            "sub": "user123",
            "exp": int(time.time()) + 3600,
        }
        token, jwks = self._make_rs256_token_and_jwks(payload)
        mock_cm = _make_urlopen_mock(json.dumps(jwks).encode())

        with patch("urllib.request.urlopen", return_value=mock_cm):
            claims = validate_id_token(
                token,
                "https://accounts.example.com/jwks",
                expected_client_id="my_client_id",
                expected_issuer="https://accounts.example.com",
            )
        assert claims.sub == "user123"


# ---------------------------------------------------------------------------
# get_provider_config
# ---------------------------------------------------------------------------


class TestGetProviderConfig:
    """Tests for ``get_provider_config``."""

    def _settings_with_providers(
        self, providers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {"OIDC_PROVIDERS": providers}

    def test_returns_matching_provider(self, settings: Any) -> None:
        """The correct provider dict must be returned when the ID matches."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [
                {"id": "google", "client_id": "google-client-id"},
                {"id": "github", "client_id": "github-client-id"},
            ],
        }
        provider = get_provider_config("google")
        assert provider["client_id"] == "google-client-id"

    def test_raises_when_provider_not_found(self, settings: Any) -> None:
        """An unknown provider ID must raise ValueError."""
        settings.SYNTEK_AUTH = {
            **settings.SYNTEK_AUTH,
            "OIDC_PROVIDERS": [
                {"id": "google", "client_id": "google-client-id"},
            ],
        }
        with pytest.raises(ValueError, match="not configured"):
            get_provider_config("unknown_provider")

    def test_raises_when_no_providers_configured(self, settings: Any) -> None:
        """When ``OIDC_PROVIDERS`` is empty, ValueError must be raised."""
        settings.SYNTEK_AUTH = {**settings.SYNTEK_AUTH, "OIDC_PROVIDERS": []}
        with pytest.raises(ValueError, match="not configured"):
            get_provider_config("google")

    def test_raises_when_syntek_auth_has_no_oidc_providers(self, settings: Any) -> None:
        """When ``OIDC_PROVIDERS`` key is absent from settings, ValueError must be raised."""
        settings.SYNTEK_AUTH = {
            k: v for k, v in settings.SYNTEK_AUTH.items() if k != "OIDC_PROVIDERS"
        }
        with pytest.raises(ValueError, match="not configured"):
            get_provider_config("google")


# ---------------------------------------------------------------------------
# ES256 — ECDSA P-256 (Apple Sign In compatibility)
# ---------------------------------------------------------------------------


def _make_ec_key_pair() -> tuple[object, object]:
    """Generate a P-256 key pair for ES256 test tokens."""
    from cryptography.hazmat.primitives.asymmetric.ec import (
        SECP256R1,
        generate_private_key,
    )

    private_key = generate_private_key(SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


def _make_es256_jwt(
    payload: dict[str, Any],
    private_key: object,
    kid: str | None = None,
) -> str:
    """Construct a real ES256-signed JWT using the cryptography library."""
    from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
    from cryptography.hazmat.primitives.hashes import SHA256

    header: dict[str, Any] = {"alg": "ES256", "typ": "JWT"}
    if kid is not None:
        header["kid"] = kid

    header_b64 = _b64url_encode(json.dumps(header).encode())
    body_b64 = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header_b64}.{body_b64}".encode("ascii")

    sig = private_key.sign(signing_input, ECDSA(SHA256()))  # type: ignore[union-attr]
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{body_b64}.{sig_b64}"


def _ec_jwk_from_public_key(
    private_key: object, kid: str | None = None
) -> dict[str, Any]:
    """Build a minimal EC JWK dict from a P-256 private key."""
    pub_numbers = private_key.public_key().public_numbers()  # type: ignore[union-attr]

    def _int_to_b64url(value: int) -> str:
        return _b64url_encode(value.to_bytes(32, "big"))

    jwk: dict[str, Any] = {
        "kty": "EC",
        "alg": "ES256",
        "crv": "P-256",
        "use": "sig",
        "x": _int_to_b64url(pub_numbers.x),
        "y": _int_to_b64url(pub_numbers.y),
    }
    if kid is not None:
        jwk["kid"] = kid
    return jwk


class TestVerifyEs256:
    """Unit tests for ``_verify_es256`` — ECDSA P-256 JWT verification."""

    def _make_payload(self, **overrides: Any) -> dict[str, Any]:
        return {
            "sub": "apple-user-001",
            "iss": "https://appleid.apple.com",
            "aud": "com.example.app",
            "exp": int(time.time()) + 600,
            **overrides,
        }

    def test_valid_es256_token_returns_payload(self) -> None:
        """A correctly signed ES256 token is verified and the payload returned."""
        private_key, _ = _make_ec_key_pair()
        payload = self._make_payload()
        token = _make_es256_jwt(payload, private_key)
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with patch(
            "syntek_auth.services.oidc.urllib.request.urlopen",
            return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
        ):
            result = _verify_es256(token, "https://appleid.apple.com/auth/keys")

        assert result["sub"] == "apple-user-001"

    def test_valid_es256_token_matched_by_kid(self) -> None:
        """Key lookup succeeds when the token ``kid`` matches the JWK ``kid``."""
        private_key, _ = _make_ec_key_pair()
        other_private, _ = _make_ec_key_pair()
        token = _make_es256_jwt(self._make_payload(), private_key, kid="key-1")
        jwks = {
            "keys": [
                _ec_jwk_from_public_key(other_private, kid="key-2"),
                _ec_jwk_from_public_key(private_key, kid="key-1"),
            ]
        }

        with patch(
            "syntek_auth.services.oidc.urllib.request.urlopen",
            return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
        ):
            result = _verify_es256(token, "https://appleid.apple.com/auth/keys")

        assert result["sub"] == "apple-user-001"

    def test_tampered_signature_raises(self) -> None:
        """A token with a modified signature must raise ``ValueError``."""
        private_key, _ = _make_ec_key_pair()
        other_private, _ = _make_ec_key_pair()
        token = _make_es256_jwt(self._make_payload(), private_key)
        # Replace signature with one from a different key.
        header_b64, body_b64, _ = token.split(".")
        bad_sig = _make_es256_jwt(self._make_payload(), other_private).split(".")[2]
        bad_token = f"{header_b64}.{body_b64}.{bad_sig}"
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with (
            patch(
                "syntek_auth.services.oidc.urllib.request.urlopen",
                return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
            ),
            pytest.raises(ValueError, match="ES256 signature verification failed"),
        ):
            _verify_es256(bad_token, "https://appleid.apple.com/auth/keys")

    def test_expired_token_raises(self) -> None:
        """An expired ES256 token must raise ``ValueError``."""
        private_key, _ = _make_ec_key_pair()
        payload = self._make_payload(exp=int(time.time()) - 60)
        token = _make_es256_jwt(payload, private_key)
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with (
            patch(
                "syntek_auth.services.oidc.urllib.request.urlopen",
                return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
            ),
            pytest.raises(ValueError, match="expired"),
        ):
            _verify_es256(token, "https://appleid.apple.com/auth/keys")

    def test_no_matching_ec_key_raises(self) -> None:
        """When the JWKS contains no EC key, ``ValueError`` must be raised."""
        private_key, _ = _make_ec_key_pair()
        token = _make_es256_jwt(self._make_payload(), private_key)
        # JWKS contains only an RSA key — no EC key.
        _, rsa_public = _generate_rsa_key_pair()
        jwks = {"keys": [_jwk_from_public_key(rsa_public)]}

        with (
            patch(
                "syntek_auth.services.oidc.urllib.request.urlopen",
                return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
            ),
            pytest.raises(ValueError, match="No suitable JWK found"),
        ):
            _verify_es256(token, "https://appleid.apple.com/auth/keys")


class TestValidateIdTokenEs256:
    """Integration tests for ``validate_id_token`` dispatching ES256 tokens."""

    def _make_payload(self, **overrides: Any) -> dict[str, Any]:
        return {
            "sub": "apple-user-001",
            "iss": "https://appleid.apple.com",
            "aud": "com.example.app",
            "exp": int(time.time()) + 600,
            **overrides,
        }

    def test_es256_token_validated_end_to_end(self) -> None:
        """``validate_id_token`` accepts a valid ES256 token and returns claims."""
        private_key, _ = _make_ec_key_pair()
        payload = self._make_payload(email="user@icloud.com")
        token = _make_es256_jwt(payload, private_key)
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with patch(
            "syntek_auth.services.oidc.urllib.request.urlopen",
            return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
        ):
            claims = validate_id_token(
                token,
                jwks_uri="https://appleid.apple.com/auth/keys",
                expected_client_id="com.example.app",
                expected_issuer="https://appleid.apple.com",
            )

        assert isinstance(claims, OidcTokenClaims)
        assert claims.sub == "apple-user-001"
        assert claims.email == "user@icloud.com"

    def test_es256_with_nonce_validated(self) -> None:
        """ES256 token with a matching nonce is accepted."""
        private_key, _ = _make_ec_key_pair()
        nonce = "abc123nonce"
        payload = self._make_payload(nonce=nonce)
        token = _make_es256_jwt(payload, private_key)
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with patch(
            "syntek_auth.services.oidc.urllib.request.urlopen",
            return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
        ):
            claims = validate_id_token(
                token,
                jwks_uri="https://appleid.apple.com/auth/keys",
                expected_client_id="com.example.app",
                expected_issuer="https://appleid.apple.com",
                expected_nonce=nonce,
            )

        assert claims.sub == "apple-user-001"

    def test_es256_wrong_nonce_raises(self) -> None:
        """ES256 token with a mismatched nonce must raise ``ValueError``."""
        private_key, _ = _make_ec_key_pair()
        payload = self._make_payload(nonce="correct-nonce")
        token = _make_es256_jwt(payload, private_key)
        jwks = {"keys": [_ec_jwk_from_public_key(private_key)]}

        with (
            patch(
                "syntek_auth.services.oidc.urllib.request.urlopen",
                return_value=_make_urlopen_mock(json.dumps(jwks).encode()),
            ),
            pytest.raises(ValueError, match="nonce mismatch"),
        ):
            validate_id_token(
                token,
                jwks_uri="https://appleid.apple.com/auth/keys",
                expected_client_id="com.example.app",
                expected_issuer="https://appleid.apple.com",
                expected_nonce="wrong-nonce",
            )

    def test_unsupported_algorithm_raises(self) -> None:
        """An ID token using an unsupported algorithm must raise ``ValueError``."""
        # Craft a token with an unsupported alg header.
        header = {"alg": "PS256", "typ": "JWT"}
        payload = self._make_payload()
        header_b64 = _b64url_encode(json.dumps(header).encode())
        body_b64 = _b64url_encode(json.dumps(payload).encode())
        bad_token = f"{header_b64}.{body_b64}.fakesig"

        with pytest.raises(ValueError, match="Unsupported JWT algorithm"):
            validate_id_token(
                bad_token,
                jwks_uri="https://example.com/jwks",
                expected_client_id="com.example.app",
                expected_issuer="https://appleid.apple.com",
            )
