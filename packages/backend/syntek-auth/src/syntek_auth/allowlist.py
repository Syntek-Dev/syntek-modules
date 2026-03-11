"""SSO provider allowlist enforcement — US076.

Defines the set of OAuth providers that Syntek permits for SSO and exposes the
validation function called by ``SyntekAuthConfig.ready()``.

Policy
------
Only providers where MFA is either enforced by the platform with no opt-out
(e.g. Defguard) **or** enforceable at the organisation/application level before
the OAuth flow completes (e.g. GitHub, Okta, Microsoft Entra ID) are permitted.

Providers where MFA is an optional per-user setting are blocked regardless of
whether individual users have it enabled — the platform cannot guarantee
enforcement and has no way to verify it at login time.

Operators may add self-hosted OIDC providers via
``SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS']`` by supplying a list of dicts with
the key ``mfa_enforced: True``.  This places legal and operational
responsibility on the operator.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

# ---------------------------------------------------------------------------
# Built-in blocked providers
# ---------------------------------------------------------------------------

#: Identifiers that are unconditionally blocked.  These are case-normalised
#: lowercase strings matched against the ``provider`` key in
#: ``SYNTEK_AUTH['OAUTH_PROVIDERS']``.
BLOCKED_PROVIDERS: frozenset[str] = frozenset(
    {
        "google",
        "facebook",
        "instagram",
        "linkedin",
        "twitter",
        "x",
        "apple",
        "discord",
        "microsoft",  # consumer MSA only — Entra ID / Azure AD is allowed
    }
)

#: Built-in allowed provider identifiers (MFA enforced at platform level).
BUILTIN_ALLOWED_PROVIDERS: frozenset[str] = frozenset(
    {
        "github",
        "gitlab",
        "okta",
        "entra",  # Microsoft Entra ID / Azure AD
        "azure_ad",  # alternate identifier
        "authentik",
        "keycloak",
        "defguard",
    }
)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_oauth_providers(syntek_auth_settings: dict) -> None:  # type: ignore[type-arg]
    """Validate the ``OAUTH_PROVIDERS`` list in ``SYNTEK_AUTH``.

    Raises ``ImproperlyConfigured`` for any of these conditions:

    - A provider identifier is in :data:`BLOCKED_PROVIDERS`.
    - A provider identifier is not in :data:`BUILTIN_ALLOWED_PROVIDERS` and
      the provider dict does not carry ``mfa_enforced: True``.

    Parameters
    ----------
    syntek_auth_settings:
        The full ``SYNTEK_AUTH`` settings dict as configured in
        ``settings.py``.

    Raises
    ------
    ImproperlyConfigured
        With a message that names the offending provider and explains why
        it was rejected.
    """
    providers: list[dict] = syntek_auth_settings.get("OAUTH_PROVIDERS", [])  # type: ignore[type-arg]

    for entry in providers:
        provider_id: str = str(entry.get("provider", "")).lower()

        if provider_id in BLOCKED_PROVIDERS:
            raise ImproperlyConfigured(
                f"'{provider_id}' is not permitted — does not enforce MFA at the"
                " platform level. See SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS'] docs."
            )

        if provider_id not in BUILTIN_ALLOWED_PROVIDERS and not entry.get(
            "mfa_enforced", False
        ):
            raise ImproperlyConfigured(
                f"'{provider_id}' is not a recognised built-in provider and does not"
                f" carry 'mfa_enforced: True'. Only providers that enforce MFA at the"
                f" platform level are permitted."
                f" See SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS'] documentation."
            )
