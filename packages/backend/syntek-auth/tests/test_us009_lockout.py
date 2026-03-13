"""US009 — Red phase: account lockout tests for ``syntek-auth``.

Tests cover the ``compute_lockout_duration`` and ``should_lock_account``
functions.

Acceptance criteria under test
-------------------------------
- An account is locked after ``LOCKOUT_THRESHOLD`` consecutive failed attempts.
- With ``LOCKOUT_STRATEGY='fixed'``, the lockout duration is always
  ``LOCKOUT_DURATION``.
- With ``LOCKOUT_STRATEGY='progressive'``, the duration doubles on each
  successive lockout.
- ``should_lock_account`` returns False when attempt count is below threshold.

All tests **fail** in the red phase because the stub functions raise
``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from syntek_auth.services.lockout import compute_lockout_duration, should_lock_account

# ---------------------------------------------------------------------------
# AC: should_lock_account
# ---------------------------------------------------------------------------


class TestShouldLockAccount:
    """should_lock_account threshold behaviour."""

    def test_at_threshold_returns_true(self) -> None:
        """Exactly 5 failed attempts with threshold=5 must return True."""
        assert should_lock_account(failed_attempt_count=5, threshold=5) is True

    def test_below_threshold_returns_false(self) -> None:
        """Fewer than threshold attempts must return False."""
        assert should_lock_account(failed_attempt_count=4, threshold=5) is False

    def test_above_threshold_returns_true(self) -> None:
        """More than threshold attempts must also return True."""
        assert should_lock_account(failed_attempt_count=10, threshold=5) is True

    def test_zero_attempts_returns_false(self) -> None:
        """Zero failed attempts must never trigger a lockout."""
        assert should_lock_account(failed_attempt_count=0, threshold=5) is False


# ---------------------------------------------------------------------------
# AC: Fixed lockout strategy
# ---------------------------------------------------------------------------


class TestFixedLockoutStrategy:
    """With LOCKOUT_STRATEGY='fixed', duration is always LOCKOUT_DURATION."""

    def test_first_lockout_fixed_returns_base_duration(self) -> None:
        """First lockout with 'fixed' strategy must return base_duration."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=1, strategy="fixed"
        )
        assert duration == 900

    def test_second_lockout_fixed_returns_base_duration(self) -> None:
        """Second lockout with 'fixed' strategy must still return base_duration."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=2, strategy="fixed"
        )
        assert duration == 900

    def test_tenth_lockout_fixed_does_not_increase(self) -> None:
        """Tenth lockout with 'fixed' strategy must return the same base_duration."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=10, strategy="fixed"
        )
        assert duration == 900


# ---------------------------------------------------------------------------
# AC: Progressive lockout strategy
# ---------------------------------------------------------------------------


class TestProgressiveLockoutStrategy:
    """With LOCKOUT_STRATEGY='progressive', duration doubles each time."""

    def test_first_lockout_progressive_returns_base_duration(self) -> None:
        """First progressive lockout must equal base_duration."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=1, strategy="progressive"
        )
        assert duration == 900

    def test_second_lockout_progressive_doubles_duration(self) -> None:
        """Second progressive lockout must be double the base."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=2, strategy="progressive"
        )
        assert duration == 1800

    def test_third_lockout_progressive_quadruples_duration(self) -> None:
        """Third progressive lockout must be four times the base."""
        duration = compute_lockout_duration(
            base_duration=900, lockout_count=3, strategy="progressive"
        )
        assert duration == 3600

    def test_progressive_duration_formula(self) -> None:
        """Progressive duration equals base_duration * 2^(lockout_count - 1)."""
        base = 60
        for count in range(1, 6):
            expected = base * (2 ** (count - 1))
            actual = compute_lockout_duration(
                base_duration=base, lockout_count=count, strategy="progressive"
            )
            assert actual == expected, (
                f"lockout_count={count}: expected {expected}, got {actual}"
            )

    def test_zero_base_duration_progressive_stays_zero(self) -> None:
        """A base_duration of 0 (manual unlock) should remain 0 under any strategy."""
        duration = compute_lockout_duration(
            base_duration=0, lockout_count=3, strategy="progressive"
        )
        assert duration == 0
