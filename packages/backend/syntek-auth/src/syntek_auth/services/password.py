"""Password policy enforcement for ``syntek-auth`` — US009.

Validates passwords against the ``SYNTEK_AUTH`` password policy settings and
provides helpers for history checks, expiry checks, and breach detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolicyViolation:
    """A single password policy violation.

    Attributes
    ----------
    code:
        Machine-readable violation identifier (e.g. ``'too_short'``,
        ``'no_symbols'``, ``'breach_detected'``).
    message:
        Human-readable description of the violation.
    """

    code: str
    message: str


@dataclass
class PasswordPolicyResult:
    """Result of validating a password against the configured policy.

    Attributes
    ----------
    valid:
        ``True`` if the password passes all active policy rules.
    violations:
        List of :class:`PolicyViolation` instances describing each failure.
    """

    valid: bool = True
    violations: list[PolicyViolation] = field(default_factory=list)


def validate_password_policy(
    password: str,
    policy: dict,  # type: ignore[type-arg]
) -> PasswordPolicyResult:
    """Validate ``password`` against the supplied policy dict.

    Checks minimum length, maximum length, and character class requirements.
    All failing rules are collected and returned together so the caller can
    surface every violation in a single response.

    Parameters
    ----------
    password:
        The plaintext password to validate.
    policy:
        A dict whose keys mirror the ``SYNTEK_AUTH`` password-policy subset:
        ``PASSWORD_MIN_LENGTH``, ``PASSWORD_MAX_LENGTH``,
        ``PASSWORD_REQUIRE_UPPERCASE``, ``PASSWORD_REQUIRE_LOWERCASE``,
        ``PASSWORD_REQUIRE_DIGITS``, ``PASSWORD_REQUIRE_SYMBOLS``.

    Returns
    -------
    PasswordPolicyResult
        Contains ``valid=True`` and an empty list when all rules pass, or
        ``valid=False`` and a non-empty list of violations otherwise.
    """
    violations: list[PolicyViolation] = []

    min_length: int = policy.get("PASSWORD_MIN_LENGTH", 0)
    max_length: int = policy.get("PASSWORD_MAX_LENGTH", 0)

    if min_length > 0 and len(password) < min_length:
        violations.append(
            PolicyViolation(
                code="too_short",
                message=(
                    f"Password must be at least {min_length} characters long; "
                    f"got {len(password)}."
                ),
            )
        )

    if max_length > 0 and len(password) > max_length:
        violations.append(
            PolicyViolation(
                code="too_long",
                message=(
                    f"Password must be no more than {max_length} characters long; "
                    f"got {len(password)}."
                ),
            )
        )

    if policy.get("PASSWORD_REQUIRE_UPPERCASE", False) and not re.search(
        r"[A-Z]", password
    ):
        violations.append(
            PolicyViolation(
                code="no_uppercase",
                message="Password must contain at least one uppercase letter.",
            )
        )

    if policy.get("PASSWORD_REQUIRE_LOWERCASE", False) and not re.search(
        r"[a-z]", password
    ):
        violations.append(
            PolicyViolation(
                code="no_lowercase",
                message="Password must contain at least one lowercase letter.",
            )
        )

    if policy.get("PASSWORD_REQUIRE_DIGITS", False) and not re.search(r"\d", password):
        violations.append(
            PolicyViolation(
                code="no_digits",
                message="Password must contain at least one digit.",
            )
        )

    if policy.get("PASSWORD_REQUIRE_SYMBOLS", False) and not re.search(
        r"[^A-Za-z0-9]", password
    ):
        violations.append(
            PolicyViolation(
                code="no_symbols",
                message="Password must contain at least one symbol character.",
            )
        )

    return PasswordPolicyResult(
        valid=len(violations) == 0,
        violations=violations,
    )


def check_password_history(
    password: str,
    previous_hashes: list[str],
    history_count: int,
) -> bool:
    """Return ``True`` if ``password`` matches any of the ``history_count`` most
    recent password hashes.

    Uses ``django.contrib.auth.hashers.check_password`` to verify the password
    against each stored hash.  Only the first ``history_count`` entries in
    ``previous_hashes`` are checked; entries beyond that window are ignored.

    When ``history_count`` is ``0``, history checking is disabled and the
    function always returns ``False``.

    Parameters
    ----------
    password:
        The plaintext password to test.
    previous_hashes:
        Ordered list of password hashes (most-recent first).
    history_count:
        Number of historical hashes to check (``PASSWORD_HISTORY`` setting).

    Returns
    -------
    bool
        ``True`` if the password matches any hash in the checked window.
    """
    if history_count == 0:
        return False

    from django.contrib.auth.hashers import check_password

    hashes_to_check = previous_hashes[:history_count]
    for stored_hash in hashes_to_check:
        try:
            if check_password(password, stored_hash):
                return True
        except ValueError, TypeError:
            # Unrecognised hash format — treat as non-match
            continue

    return False


def is_password_expired(last_changed_days_ago: int, expiry_days: int) -> bool:
    """Return ``True`` if the password has exceeded its configured expiry period.

    When ``expiry_days`` is ``0``, passwords never expire.  A password changed
    exactly ``expiry_days`` ago is considered expired (boundary-inclusive).

    Parameters
    ----------
    last_changed_days_ago:
        Number of days since the password was last changed.
    expiry_days:
        ``PASSWORD_EXPIRY_DAYS`` setting.  ``0`` means the password never expires.

    Returns
    -------
    bool
        ``True`` if the password should be treated as expired.
    """
    if expiry_days == 0:
        return False
    return last_changed_days_ago >= expiry_days


def is_password_breached(password: str) -> bool:
    """Return ``True`` if ``password`` appears in the HaveIBeenPwned database.

    Uses the k-anonymity API — only the first 5 hex characters of the SHA-1
    hash are transmitted to the HIBP API.  The full password and the full hash
    are never sent.

    The SHA-1 hash prefix (first 5 hex chars) is submitted to
    ``https://api.pwnedpasswords.com/range/{prefix}``.  The response body
    contains a newline-delimited list of ``SUFFIX:COUNT`` entries.  A
    case-insensitive suffix match indicates the password has been seen in a
    breach.

    On any network or HTTP error the function returns ``False`` so that a
    transient HIBP outage does not block registration.  No specific breach
    count is exposed to the caller.

    Parameters
    ----------
    password:
        The plaintext password to check.

    Returns
    -------
    bool
        ``True`` if the password hash suffix appears in the HIBP response;
        ``False`` on non-match or network error.
    """
    import hashlib
    import urllib.request

    sha1_hash = (
        hashlib.sha1(password.encode("utf-8"), usedforsecurity=False)
        .hexdigest()
        .upper()
    )
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310
            body: str = response.read().decode("utf-8")
    except Exception:
        # Network failure — fail open so a HIBP outage does not block users.
        return False

    for line in body.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2 and parts[0].upper() == suffix:
            return True

    return False
