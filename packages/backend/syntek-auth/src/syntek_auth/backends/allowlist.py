"""SSO provider allowlist enforcement — US076 / US009.

Defines the set of OAuth providers that Syntek permits for SSO and exposes the
validation function called by ``SyntekAuthConfig.ready()``.

Policy
------
Providers where MFA cannot be guaranteed by the provider platform are
**MFA-gated**: they are permitted at startup but the OAuth callback layer
issues a ``PendingOAuthSession`` instead of a full token pair.  The user must
complete a local MFA challenge via ``completeSocialMfa`` before receiving
tokens.

Providers where MFA is either enforced by the platform with no opt-out
(e.g. Defguard) **or** enforceable at the organisation/application level before
the OAuth flow completes (e.g. GitHub, Okta, Microsoft Entra ID) are in
:data:`BUILTIN_ALLOWED_PROVIDERS` and pass directly to a full session.

Operators may add self-hosted OIDC providers via
``SYNTEK_AUTH['OAUTH_PROVIDERS']`` by supplying a list of dicts with
the key ``mfa_enforced: True``.  This places legal and operational
responsibility on the operator.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

# ---------------------------------------------------------------------------
# Built-in MFA-gated providers
# ---------------------------------------------------------------------------

#: Providers that are permitted but require local MFA gating at the callback
#: layer.  These are case-normalised lowercase strings matched against the
#: ``provider`` key in ``SYNTEK_AUTH['OAUTH_PROVIDERS']``.
MFA_GATED_PROVIDERS: frozenset[str] = frozenset(
    {
        "google",
        "facebook",
        "instagram",
        "linkedin",
        "twitter",
        "x",
        "apple",
        "discord",
        "microsoft",  # consumer MSA only — Entra ID / Azure AD is in BUILTIN_ALLOWED
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
# Helper
# ---------------------------------------------------------------------------


def is_mfa_gated_provider(provider_id: str) -> bool:
    """Return ``True`` when ``provider_id`` is in :data:`MFA_GATED_PROVIDERS`.

    Comparison is case-insensitive — ``provider_id`` is lowercased before
    the lookup.

    Parameters
    ----------
    provider_id:
        The provider identifier string to check.

    Returns
    -------
    bool
        ``True`` if the provider requires local MFA gating at the callback
        layer; ``False`` otherwise.
    """
    return provider_id.lower() in MFA_GATED_PROVIDERS


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_oauth_providers(syntek_auth_settings: dict) -> None:  # type: ignore[type-arg]
    """Validate the ``OAUTH_PROVIDERS`` list in ``SYNTEK_AUTH``.

    Raises ``ImproperlyConfigured`` only when:

    - A provider identifier is not in :data:`BUILTIN_ALLOWED_PROVIDERS` and
      not in :data:`MFA_GATED_PROVIDERS` and the provider dict does not carry
      ``mfa_enforced: True``.

    MFA-gated providers are permitted at startup — their gating happens at
    the OAuth callback layer via ``PendingOAuthSession``.

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

        # MFA-gated providers pass startup validation — gating is deferred to
        # the OAuth callback layer.
        if provider_id in MFA_GATED_PROVIDERS:
            continue

        # Built-in allowed providers pass without any extra flag.
        if provider_id in BUILTIN_ALLOWED_PROVIDERS:
            continue

        # Custom / self-hosted providers must declare mfa_enforced: True.
        if not entry.get("mfa_enforced", False):
            raise ImproperlyConfigured(
                f"'{provider_id}' is not a recognised built-in provider and does not"
                f" carry 'mfa_enforced: True'. Only providers that enforce MFA at the"
                f" platform level are permitted."
                f" See SYNTEK_AUTH['OAUTH_PROVIDERS'] documentation."
            )
