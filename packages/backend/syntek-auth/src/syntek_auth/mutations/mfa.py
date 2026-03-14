"""GraphQL MFA mutations for ``syntek-auth`` — US009.

Strawberry mutations for TOTP setup, MFA code verification, and backup code
consumption.  Passkey (WebAuthn) mutations are stubbed with a clear
``ValueError`` indicating that the WebAuthn service layer is not yet wired.

All resolvers delegate to the service layer; no business logic lives directly
in mutation methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

from syntek_auth.types.auth import MfaSetupPayload, VerifyMfaInput

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class MfaMutations:
    """Strawberry mutation type for MFA operations."""

    @strawberry.mutation
    def enable_mfa(self, info: Info) -> MfaSetupPayload:
        """Initiate TOTP setup for the authenticated user.

        Generates a new TOTP secret, builds the ``otpauth://totp/`` provisioning
        URI, generates backup codes (count from ``MFA_BACKUP_CODES_COUNT``), and
        stores hashed backup codes in the database.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.

        Returns
        -------
        MfaSetupPayload
            The provisioning URI for QR code display and plaintext backup codes
            (shown once, never stored).

        Raises
        ------
        ValueError
            If the request is unauthenticated.
        """
        from django.conf import settings

        from syntek_auth.services.totp import enable_totp_for_user

        request = getattr(info.context, "request", None)
        if request is None or not request.user.is_authenticated:
            raise ValueError("Authentication required.")

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        backup_count: int = int(cfg.get("MFA_BACKUP_CODES_COUNT", 12))
        issuer: str = str(cfg.get("SITE_NAME", "Syntek"))

        setup_data = enable_totp_for_user(
            user_id=request.user.pk,
            issuer=issuer,
            backup_codes_count=backup_count,
        )

        return MfaSetupPayload(
            provisioning_uri=setup_data.provisioning_uri,
            backup_codes=setup_data.backup_codes,
        )

    @strawberry.mutation
    def verify_mfa(self, info: Info, input: VerifyMfaInput) -> bool:  # noqa: A002
        """Verify a TOTP code or backup code for the authenticated user.

        Attempts TOTP verification against the user's stored secret first.
        Falls back to backup code consumption when TOTP fails.  Returns
        ``True`` on success and raises ``ValueError`` on failure.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            The 6-digit TOTP code or 8-character backup code to verify.

        Returns
        -------
        bool
            ``True`` when the code is valid.

        Raises
        ------
        ValueError
            If the request is unauthenticated or the code is invalid.
        """
        from syntek_auth.services.totp import consume_backup_code, verify_totp_code

        request = getattr(info.context, "request", None)
        if request is None or not request.user.is_authenticated:
            raise ValueError("Authentication required.")

        user = request.user
        user_id: int = user.pk

        # Try TOTP first when a secret is stored on the model.
        stored_secret: str | None = user.totp_secret  # type: ignore[attr-defined]
        if stored_secret:
            # Decrypt the stored ciphertext; fall back to treating the value as
            # plaintext when syntek_pyo3 is not compiled (dev / CI).
            plaintext_secret: str = stored_secret
            try:
                from django.conf import settings as _settings
                from syntek_pyo3 import (  # type: ignore[import-not-found]
                    KeyRing,
                    decrypt_field,
                )

                _cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
                _raw_key = _cfg.get("FIELD_KEY", "")
                _field_key: bytes = (
                    _raw_key.encode("utf-8")
                    if isinstance(_raw_key, str)
                    else bytes(_raw_key)
                )
                _ring = KeyRing()
                _ring.add(1, _field_key)
                plaintext_secret = decrypt_field(
                    stored_secret, _ring, type(user).__name__, "totp_secret"
                )
            except ImportError:
                pass
            if verify_totp_code(plaintext_secret, input.code):
                return True

        # Fall back to backup code consumption.
        if consume_backup_code(user_id, input.code):
            return True

        raise ValueError("Invalid MFA code. Please try again.")

    @strawberry.mutation
    def register_passkey(self, info: Info) -> str:
        """Register a WebAuthn passkey for the authenticated user.

        Returns the WebAuthn credential creation options JSON.

        Raises
        ------
        ValueError
            WebAuthn service layer is not yet available.  Passkey
            registration requires the ``webauthn`` library and a configured
            relying party.
        """
        request = getattr(info.context, "request", None)
        if request is None or not request.user.is_authenticated:
            raise ValueError("Authentication required.")

        raise ValueError(
            "Passkey registration is not yet available in this deployment. "
            "Configure the WebAuthn relying party in SYNTEK_AUTH to enable passkeys."
        )

    @strawberry.mutation
    def authenticate_passkey(self, info: Info) -> str:  # noqa: ARG002
        """Authenticate using a previously registered passkey.

        Returns the WebAuthn assertion options JSON.

        Raises
        ------
        ValueError
            WebAuthn service layer is not yet available.  Passkey
            authentication requires the ``webauthn`` library and a configured
            relying party.
        """
        raise ValueError(
            "Passkey authentication is not yet available in this deployment. "
            "Configure the WebAuthn relying party in SYNTEK_AUTH to enable passkeys."
        )
