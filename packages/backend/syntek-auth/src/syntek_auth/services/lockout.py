"""Account lockout logic for ``syntek-auth`` — US009.

Implements fixed and progressive lockout strategies based on the
``SYNTEK_AUTH`` lockout settings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockoutState:
    """Result of a lockout check.

    Attributes
    ----------
    locked:
        ``True`` if the account is currently locked.
    lockout_count:
        How many times the account has been locked in total (used by the
        progressive strategy to calculate the next duration).
    duration_seconds:
        Seconds until the lockout expires.  ``0`` if the account is not locked.
    """

    locked: bool
    lockout_count: int
    duration_seconds: int


def compute_lockout_duration(
    base_duration: int,
    lockout_count: int,
    strategy: str,
) -> int:
    """Calculate the lockout duration for the given lockout occurrence.

    With ``'fixed'`` strategy the duration is always ``base_duration``.
    With ``'progressive'`` strategy the duration is
    ``base_duration * 2^(lockout_count - 1)``, doubling on each successive
    lockout.

    Parameters
    ----------
    base_duration:
        ``LOCKOUT_DURATION`` from settings (seconds).
    lockout_count:
        The 1-based ordinal of the lockout being applied (1 = first lockout,
        2 = second, etc.).
    strategy:
        ``'fixed'`` or ``'progressive'``.

    Returns
    -------
    int
        Duration in seconds for this lockout.
    """
    if strategy == "fixed":
        return base_duration
    # progressive: base_duration * 2^(lockout_count - 1)
    return base_duration * (2 ** (lockout_count - 1))


def should_lock_account(
    failed_attempt_count: int,
    threshold: int,
) -> bool:
    """Return ``True`` if ``failed_attempt_count`` has reached ``threshold``.

    Parameters
    ----------
    failed_attempt_count:
        Consecutive failed login attempts for this account.
    threshold:
        ``LOCKOUT_THRESHOLD`` from settings.

    Returns
    -------
    bool
        ``True`` when ``failed_attempt_count >= threshold``, ``False`` otherwise.
    """
    return failed_attempt_count >= threshold
