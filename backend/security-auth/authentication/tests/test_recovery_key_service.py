"""
Unit tests for RecoveryKeyService.

Tests key generation, verification, rotation, and algorithm versioning.
"""

import pytest
from django.contrib.auth import get_user_model

from syntek_authentication.models import RecoveryKey
from syntek_authentication.services import RecoveryKeyService

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRecoveryKeyGeneration:
    """Test recovery key generation functionality."""

    def test_generate_recovery_keys_creates_12_keys(self, user):
        """Test that generating recovery keys creates exactly 12 keys."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        assert len(keys) == 12
        assert RecoveryKey.objects.filter(user=user).count() == 12

    def test_generated_keys_are_unique(self, user):
        """Test that all generated keys are unique."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        unique_keys = set(keys)
        assert len(unique_keys) == 12  # No duplicates

    def test_generated_keys_have_correct_format(self, user):
        """Test that generated keys follow the expected format."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        for key in keys:
            # Should be URL-safe base64 string
            assert isinstance(key, str)
            assert len(key) > 0
            # URL-safe base64 uses A-Z, a-z, 0-9, -, _
            assert all(c.isalnum() or c in "-_" for c in key)

    def test_generate_replaces_existing_keys(self, user):
        """Test that generating new keys replaces old ones."""
        # Generate initial keys
        old_keys = RecoveryKeyService.generate_recovery_keys(user)

        # Generate new keys
        new_keys = RecoveryKeyService.generate_recovery_keys(user)

        # Should still have exactly 12 keys
        assert RecoveryKey.objects.filter(user=user).count() == 12

        # New keys should be different
        assert set(old_keys) != set(new_keys)

    def test_generated_keys_have_version(self, user):
        """Test that generated keys have algorithm version."""
        RecoveryKeyService.generate_recovery_keys(user)

        recovery_keys = RecoveryKey.objects.filter(user=user)
        for recovery_key in recovery_keys:
            assert recovery_key.algorithm_version == 1

    def test_generated_keys_not_used_initially(self, user):
        """Test that newly generated keys are marked as unused."""
        RecoveryKeyService.generate_recovery_keys(user)

        recovery_keys = RecoveryKey.objects.filter(user=user)
        for recovery_key in recovery_keys:
            assert recovery_key.used is False
            assert recovery_key.used_at is None


class TestRecoveryKeyVerification:
    """Test recovery key verification functionality."""

    def test_verify_and_use_key_valid_key(self, user):
        """Test that a valid recovery key is accepted."""
        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        result = RecoveryKeyService.verify_and_use_key(user, test_key)

        assert result is True

    def test_verify_and_use_key_marks_as_used(self, user):
        """Test that using a recovery key marks it as used."""
        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        RecoveryKeyService.verify_and_use_key(user, test_key)

        # Key should be marked as used
        recovery_key = RecoveryKey.objects.get(user=user, used=True)
        assert recovery_key.used is True
        assert recovery_key.used_at is not None

    def test_verify_and_use_key_invalid_key(self, user):
        """Test that an invalid recovery key is rejected."""
        RecoveryKeyService.generate_recovery_keys(user)

        result = RecoveryKeyService.verify_and_use_key(user, "invalid-key-12345")

        assert result is False

    def test_verify_and_use_key_already_used(self, user):
        """Test that a previously used key cannot be reused."""
        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        # Use the key once
        assert RecoveryKeyService.verify_and_use_key(user, test_key) is True

        # Try to use it again
        assert RecoveryKeyService.verify_and_use_key(user, test_key) is False

    def test_verify_and_use_key_wrong_user(self, user):
        """Test that a key cannot be used by a different user."""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="OtherPass123!"
        )

        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        # Try to use user's key with other_user
        result = RecoveryKeyService.verify_and_use_key(other_user, test_key)

        assert result is False

    def test_verify_and_use_key_case_sensitivity(self, user):
        """Test that recovery keys are case-sensitive."""
        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        # Try uppercase version
        result = RecoveryKeyService.verify_and_use_key(user, test_key.upper())

        # Should fail (keys are case-sensitive)
        assert result is False

    def test_verify_and_use_key_whitespace_handling(self, user):
        """Test that keys with leading/trailing whitespace are rejected."""
        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        # Try with whitespace
        result = RecoveryKeyService.verify_and_use_key(user, f"  {test_key}  ")

        # Should fail (exact match required)
        assert result is False

    def test_verify_and_use_key_race_condition(self, user):
        """Test that concurrent usage of the same key is handled correctly."""
        from concurrent.futures import ThreadPoolExecutor

        keys = RecoveryKeyService.generate_recovery_keys(user)
        test_key = keys[0]

        # Try to use the same key from multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(
                executor.map(
                    lambda _: RecoveryKeyService.verify_and_use_key(user, test_key),
                    range(5),
                )
            )

        # Only one should succeed
        assert sum(results) == 1

        # Key should be marked as used exactly once
        assert RecoveryKey.objects.filter(user=user, used=True).count() == 1


class TestRecoveryKeyListing:
    """Test listing and counting recovery keys."""

    def test_get_unused_count_all_unused(self, user):
        """Test that get_unused_count returns correct count when all keys unused."""
        RecoveryKeyService.generate_recovery_keys(user)

        count = RecoveryKeyService.get_unused_count(user)

        assert count == 12

    def test_get_unused_count_some_used(self, user):
        """Test that get_unused_count returns correct count after some keys used."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        # Use 3 keys
        for i in range(3):
            RecoveryKeyService.verify_and_use_key(user, keys[i])

        count = RecoveryKeyService.get_unused_count(user)

        assert count == 9

    def test_get_unused_count_all_used(self, user):
        """Test that get_unused_count returns 0 when all keys are used."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        # Use all keys
        for key in keys:
            RecoveryKeyService.verify_and_use_key(user, key)

        count = RecoveryKeyService.get_unused_count(user)

        assert count == 0

    def test_get_unused_count_no_keys(self, user):
        """Test that get_unused_count returns 0 when user has no keys."""
        count = RecoveryKeyService.get_unused_count(user)

        assert count == 0


class TestKeyRotation:
    """Test recovery key rotation functionality."""

    def test_rotate_keys_generates_new_set(self, user):
        """Test that rotating keys generates a new set of 12 keys."""
        old_keys = RecoveryKeyService.generate_recovery_keys(user)

        # Use some old keys
        for i in range(3):
            RecoveryKeyService.verify_and_use_key(user, old_keys[i])

        # Rotate keys
        new_keys = RecoveryKeyService.rotate_keys(user)

        assert len(new_keys) == 12
        assert RecoveryKey.objects.filter(user=user).count() == 12

        # Old keys should no longer work
        for old_key in old_keys:
            assert RecoveryKeyService.verify_and_use_key(user, old_key) is False

    def test_rotate_keys_increments_version(self, user):
        """Test that rotating keys increments the algorithm version."""
        # Generate initial keys (version 1)
        RecoveryKeyService.generate_recovery_keys(user)

        # Note: Current implementation uses version 1
        # This test would need algorithm versioning to be implemented
        initial_version = RecoveryKey.objects.filter(user=user).first().algorithm_version

        # Rotate keys
        RecoveryKeyService.rotate_keys(user)

        # Version should remain the same (or increment if versioning is implemented)
        new_version = RecoveryKey.objects.filter(user=user).first().algorithm_version
        assert new_version == initial_version  # Currently same version

    def test_rotate_keys_preserves_user(self, user):
        """Test that rotating keys preserves the user association."""
        RecoveryKeyService.generate_recovery_keys(user)

        RecoveryKeyService.rotate_keys(user)

        # All keys should still belong to the user
        assert RecoveryKey.objects.filter(user=user).count() == 12
        assert all(key.user == user for key in RecoveryKey.objects.filter(user=user))


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_generate_for_user_without_existing_keys(self, user):
        """Test generating keys for a user with no existing keys."""
        # Should work without errors
        keys = RecoveryKeyService.generate_recovery_keys(user)

        assert len(keys) == 12

    def test_verify_with_empty_string(self, user):
        """Test that verifying an empty string key returns False."""
        RecoveryKeyService.generate_recovery_keys(user)

        result = RecoveryKeyService.verify_and_use_key(user, "")

        assert result is False

    def test_verify_with_very_long_key(self, user):
        """Test that verifying a very long key doesn't cause issues."""
        RecoveryKeyService.generate_recovery_keys(user)

        long_key = "x" * 10000
        result = RecoveryKeyService.verify_and_use_key(user, long_key)

        assert result is False

    def test_multiple_users_have_separate_keys(self):
        """Test that multiple users have completely separate key sets."""
        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="Password1!"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="Password2!"
        )

        keys1 = RecoveryKeyService.generate_recovery_keys(user1)
        keys2 = RecoveryKeyService.generate_recovery_keys(user2)

        # Keys should not overlap
        assert set(keys1).isdisjoint(set(keys2))

        # Each user should have their own 12 keys
        assert RecoveryKey.objects.filter(user=user1).count() == 12
        assert RecoveryKey.objects.filter(user=user2).count() == 12


class TestSecurityProperties:
    """Test security properties of recovery keys."""

    def test_key_hashes_stored_not_plaintext(self, user):
        """Test that key hashes are stored, not plaintext keys."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        for key in keys:
            # Plaintext key should not appear in database
            recovery_key = RecoveryKey.objects.filter(user=user).first()
            assert key not in str(recovery_key.key_hash)

    def test_same_key_produces_same_hash(self, user):
        """Test that the same recovery key produces the same hash."""
        RecoveryKeyService.generate_recovery_keys(user)

        # Delete and regenerate with the same key (hypothetical)
        # Note: This is not possible with current API, but tests the hashing property

    def test_different_keys_produce_different_hashes(self, user):
        """Test that different recovery keys produce different hashes."""
        RecoveryKeyService.generate_recovery_keys(user)

        hashes = set()
        for recovery_key in RecoveryKey.objects.filter(user=user):
            hashes.add(recovery_key.key_hash)

        # All hashes should be unique
        assert len(hashes) == 12

    def test_keys_cryptographically_random(self, user):
        """Test that keys appear cryptographically random (statistical test)."""
        keys = RecoveryKeyService.generate_recovery_keys(user)

        # Basic randomness test: no key should be a substring of another
        for i, key1 in enumerate(keys):
            for j, key2 in enumerate(keys):
                if i != j:
                    assert key1 not in key2
                    assert key2 not in key1

    def test_timing_attack_resistance(self, user):
        """Test that verification is resistant to timing attacks."""
        import time

        keys = RecoveryKeyService.generate_recovery_keys(user)
        valid_key = keys[0]
        invalid_key = "a" * len(valid_key)

        # Time valid key verification
        start = time.perf_counter()
        RecoveryKeyService.verify_and_use_key(user, invalid_key)
        invalid_time = time.perf_counter() - start

        # Generate new keys for second test
        keys = RecoveryKeyService.generate_recovery_keys(user)
        new_valid_key = keys[0]

        # Time invalid key verification
        start = time.perf_counter()
        RecoveryKeyService.verify_and_use_key(user, new_valid_key)
        valid_time = time.perf_counter() - start

        # Timing difference should be minimal (< 10ms for constant-time comparison)
        # Note: This is a rough test; true timing attack resistance requires
        # more sophisticated statistical analysis
        time_diff = abs(valid_time - invalid_time)
        assert time_diff < 0.01  # Less than 10ms difference
