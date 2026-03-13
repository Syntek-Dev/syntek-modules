"""MFA method gating and session state for ``syntek-auth`` — US009.

Provides helpers for determining which MFA methods are available, whether a
user must complete MFA setup, and whether an OIDC ``amr`` claim satisfies the
MFA requirement.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Canonical ordering for MFA method identifiers.
_CANONICAL_ORDER: list[str] = ["totp", "sms", "email_otp", "passkey"]

#: Recognised MFA method identifiers.
_VALID_MFA_METHODS: frozenset[str] = frozenset(_CANONICAL_ORDER)

#: OIDC ``amr`` claim values that satisfy the MFA requirement individually.
_MFA_AMR_VALUES: frozenset[str] = frozenset({"mfa", "swk", "hwk"})

#: ``amr`` value combinations that together satisfy the MFA requirement.
#: The combination ``{'otp', 'pwd'}`` is treated as MFA-compliant.
_MFA_AMR_COMBOS: list[frozenset[str]] = [frozenset({"otp", "pwd"})]


@dataclass(frozen=True)
class MfaSessionState:
    """Describes the MFA status of a session.

    Attributes
    ----------
    full_session:
        ``True`` if the user has a fully authenticated session.
    mfa_setup_required:
        ``True`` if the user must configure MFA before accessing protected
        resources.
    """

    full_session: bool
    mfa_setup_required: bool


def enabled_mfa_methods(configured_methods: list[str]) -> list[str]:
    """Return the list of enabled MFA method identifiers.

    Filters ``configured_methods`` to only include recognised identifiers and
    returns them in canonical order: totp, sms, email_otp, passkey.

    Parameters
    ----------
    configured_methods:
        The ``MFA_METHODS`` list from ``SYNTEK_AUTH``.

    Returns
    -------
    list[str]
        Recognised methods in canonical order.
    """
    active = frozenset(configured_methods) & _VALID_MFA_METHODS
    return [m for m in _CANONICAL_ORDER if m in active]


def resolve_session_state(
    user_has_mfa_configured: bool,
    mfa_required: bool,
) -> MfaSessionState:
    """Determine the session state after credential verification.

    When ``mfa_required`` is ``False``, a full session is always issued.
    When ``mfa_required`` is ``True`` and the user has MFA configured, a full
    session is issued.  When ``mfa_required`` is ``True`` and the user has no
    MFA configured, a partial session is issued and ``mfa_setup_required`` is
    set to ``True``.

    Parameters
    ----------
    user_has_mfa_configured:
        Whether the user has at least one MFA method set up.
    mfa_required:
        ``SYNTEK_AUTH['MFA_REQUIRED']`` value.

    Returns
    -------
    MfaSessionState
        The appropriate session state for this user.
    """
    if not mfa_required:
        return MfaSessionState(full_session=True, mfa_setup_required=False)

    if user_has_mfa_configured:
        return MfaSessionState(full_session=True, mfa_setup_required=False)

    return MfaSessionState(full_session=False, mfa_setup_required=True)


def oidc_amr_satisfies_mfa(amr_claim: list[str] | None) -> bool:
    """Return ``True`` if the ``amr`` claim from an OIDC ID token includes MFA.

    A claim containing ``'mfa'``, ``'swk'``, or ``'hwk'`` is considered
    satisfactory.  The combination ``['otp', 'pwd']`` is also treated as
    MFA-compliant.  ``None`` or an empty list returns ``False``.

    Parameters
    ----------
    amr_claim:
        The ``amr`` claim from the validated OIDC ID token.

    Returns
    -------
    bool
        ``True`` if the claim satisfies the MFA requirement.
    """
    if not amr_claim:
        return False

    claim_set = frozenset(amr_claim)

    # Direct MFA-indicator values
    if claim_set & _MFA_AMR_VALUES:
        return True

    # Recognised multi-factor combinations
    return any(combo <= claim_set for combo in _MFA_AMR_COMBOS)
