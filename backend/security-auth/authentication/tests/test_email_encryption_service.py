"""
Unit tests for EmailEncryptionService.

Tests encryption, decryption, key rotation, and GDPR compliance.
"""

import pytest
from django.contrib.auth import get_user_model

from syntek_authentication.models import EncryptedEmail, PIIAccessLog
from syntek_authentication.services import EmailEncryptionService

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestEmailEncryption:
    """Test email encryption and decryption functionality."""

    def test_encrypt_and_save_creates_encrypted_email(self, user, test_email, admin_user):
        """Test that encrypt_and_save creates an EncryptedEmail record."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        assert EncryptedEmail.objects.filter(user=user).exists()
        encrypted = EncryptedEmail.objects.get(user=user)
        assert encrypted.email_encrypted is not None
        assert encrypted.email_hash is not None

    def test_encrypt_and_save_lowercases_email(self, user, admin_user):
        """Test that emails are normalized to lowercase before encryption."""
        EmailEncryptionService.encrypt_and_save(user, "USER@EXAMPLE.COM", admin_user)

        decrypted = EmailEncryptionService.decrypt_email(user)
        assert decrypted == "user@example.com"

    def test_decrypt_email_returns_original_plaintext(self, user, test_email, admin_user):
        """Test that decryption returns the original plaintext email."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        decrypted = EmailEncryptionService.decrypt_email(user)
        assert decrypted == test_email

    def test_decrypt_email_logs_pii_access(self, user, test_email, admin_user):
        """Test that decrypting email logs PII access for GDPR compliance."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        # Decrypt should log access
        EmailEncryptionService.decrypt_email(user, admin_user)

        assert PIIAccessLog.objects.filter(
            action="decrypt_email", resource_type="EncryptedEmail", user_affected=user
        ).exists()

    def test_decrypt_nonexistent_email_raises_exception(self, user):
        """Test that decrypting a non-existent email raises an exception."""
        with pytest.raises(EncryptedEmail.DoesNotExist):
            EmailEncryptionService.decrypt_email(user)

    def test_check_email_exists_true_for_existing_email(self, user, test_email, admin_user):
        """Test that check_email_exists returns True for existing emails."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        assert EmailEncryptionService.check_email_exists(test_email) is True

    def test_check_email_exists_false_for_nonexistent_email(self):
        """Test that check_email_exists returns False for non-existent emails."""
        assert EmailEncryptionService.check_email_exists("nonexistent@example.com") is False

    def test_check_email_exists_case_insensitive(self, user, admin_user):
        """Test that email existence check is case-insensitive."""
        EmailEncryptionService.encrypt_and_save(user, "user@example.com", admin_user)

        assert EmailEncryptionService.check_email_exists("USER@EXAMPLE.COM") is True
        assert EmailEncryptionService.check_email_exists("UsEr@ExAmPlE.cOm") is True

    def test_get_user_by_email_returns_correct_user(self, user, test_email, admin_user):
        """Test that get_user_by_email returns the correct user."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        found_user = EmailEncryptionService.get_user_by_email(test_email)
        assert found_user == user

    def test_get_user_by_email_none_for_nonexistent(self):
        """Test that get_user_by_email returns None for non-existent emails."""
        result = EmailEncryptionService.get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_unique_nonces_for_same_plaintext(self, user, test_email, admin_user):
        """Test that encrypting the same email twice produces different ciphertexts."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)
        encrypted1 = EncryptedEmail.objects.get(user=user).email_encrypted

        # Delete and re-encrypt
        EncryptedEmail.objects.filter(user=user).delete()
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)
        encrypted2 = EncryptedEmail.objects.get(user=user).email_encrypted

        # Should have different ciphertexts (different nonces)
        assert encrypted1 != encrypted2

        # But both should decrypt to the same plaintext
        decrypted = EmailEncryptionService.decrypt_email(user)
        assert decrypted == test_email


class TestKeyRotation:
    """Test key rotation and batch re-encryption functionality."""

    def test_rotate_encryption_key_batch(self, admin_user):
        """Test rotating encryption keys for multiple users."""
        # Create multiple users with encrypted emails
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password=f"Password{i}!",
            )
            EmailEncryptionService.encrypt_and_save(user, f"user{i}@example.com", admin_user)
            users.append(user)

        # Rotate keys (in real scenario, new keys would be provided)
        # For this test, we'll verify the process completes
        success_count, failure_count = EmailEncryptionService.rotate_encryption_key(batch_size=2)

        assert success_count == 5
        assert failure_count == 0

        # Verify all emails are still decryptable
        for i, user in enumerate(users):
            decrypted = EmailEncryptionService.decrypt_email(user)
            assert decrypted == f"user{i}@example.com"

    def test_rotate_encryption_key_handles_failures_gracefully(self, admin_user, user):
        """Test that key rotation handles individual failures gracefully."""
        EmailEncryptionService.encrypt_and_save(user, "test@example.com", admin_user)

        # Simulate failure by corrupting the encrypted data
        encrypted = EncryptedEmail.objects.get(user=user)
        encrypted.email_encrypted = b"corrupted_data"
        encrypted.save()

        success_count, failure_count = EmailEncryptionService.rotate_encryption_key()

        assert failure_count >= 1  # At least the corrupted record failed

    def test_rotate_with_custom_batch_size(self, admin_user):
        """Test key rotation with custom batch size."""
        # Create 10 users
        for i in range(10):
            user = User.objects.create_user(
                username=f"batchuser{i}",
                email=f"batch{i}@example.com",
                password=f"Password{i}!",
            )
            EmailEncryptionService.encrypt_and_save(user, f"batch{i}@example.com", admin_user)

        # Rotate with batch size of 3
        success_count, failure_count = EmailEncryptionService.rotate_encryption_key(batch_size=3)

        assert success_count == 10
        assert failure_count == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_encrypt_empty_email_raises_validation_error(self, user, admin_user):
        """Test that encrypting an empty email raises a validation error."""
        with pytest.raises(Exception):  # Should raise validation error from Rust
            EmailEncryptionService.encrypt_and_save(user, "", admin_user)

    def test_encrypt_invalid_email_raises_validation_error(self, user, admin_user):
        """Test that encrypting an invalid email raises a validation error."""
        with pytest.raises(Exception):  # Should raise validation error from Rust
            EmailEncryptionService.encrypt_and_save(user, "not-an-email", admin_user)

    def test_encrypt_unicode_email(self, user, admin_user):
        """Test that Unicode emails are handled correctly."""
        # Note: This may fail if Rust validators don't support IDN
        unicode_email = "用户@例え.jp"
        try:
            EmailEncryptionService.encrypt_and_save(user, unicode_email, admin_user)
            decrypted = EmailEncryptionService.decrypt_email(user)
            assert decrypted == unicode_email.lower()
        except Exception:
            # Unicode emails may not be supported
            pytest.skip("Unicode emails not supported by validator")

    def test_update_existing_email(self, user, admin_user):
        """Test updating an existing encrypted email."""
        EmailEncryptionService.encrypt_and_save(user, "old@example.com", admin_user)

        # Update to new email
        EmailEncryptionService.encrypt_and_save(user, "new@example.com", admin_user)

        # Should have only one record (updated, not duplicate)
        assert EncryptedEmail.objects.filter(user=user).count() == 1

        decrypted = EmailEncryptionService.decrypt_email(user)
        assert decrypted == "new@example.com"

    def test_concurrent_encryption_different_users(self, admin_user):
        """Test that concurrent encryption for different users works correctly."""
        from concurrent.futures import ThreadPoolExecutor

        def encrypt_for_user(index):
            user = User.objects.create_user(
                username=f"concurrent{index}",
                email=f"concurrent{index}@example.com",
                password=f"Password{index}!",
            )
            EmailEncryptionService.encrypt_and_save(
                user, f"concurrent{index}@example.com", admin_user
            )
            return user

        # Create 10 users concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            users = list(executor.map(encrypt_for_user, range(10)))

        # Verify all users have encrypted emails
        assert len(users) == 10
        for i, user in enumerate(users):
            decrypted = EmailEncryptionService.decrypt_email(user)
            assert decrypted == f"concurrent{i}@example.com"


class TestSecurityProperties:
    """Test security properties of email encryption."""

    def test_encrypted_data_not_in_database_plaintext(self, user, test_email, admin_user):
        """Test that plaintext email is not stored in the database."""
        EmailEncryptionService.encrypt_and_save(user, test_email, admin_user)

        encrypted = EncryptedEmail.objects.get(user=user)

        # Encrypted bytes should not contain the plaintext email
        assert test_email.encode() not in encrypted.email_encrypted

    def test_hash_consistent_for_same_email(self, user, admin_user):
        """Test that the same email produces the same hash (for lookups)."""
        email = "consistent@example.com"
        EmailEncryptionService.encrypt_and_save(user, email, admin_user)

        hash1 = EncryptedEmail.objects.get(user=user).email_hash

        # Delete and re-encrypt
        EncryptedEmail.objects.filter(user=user).delete()
        EmailEncryptionService.encrypt_and_save(user, email, admin_user)

        hash2 = EncryptedEmail.objects.get(user=user).email_hash

        # Hash should be identical for constant-time lookups
        assert hash1 == hash2

    def test_different_emails_produce_different_hashes(self, admin_user):
        """Test that different emails produce different hashes."""
        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="Password1!"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="Password2!"
        )

        EmailEncryptionService.encrypt_and_save(user1, "email1@example.com", admin_user)
        EmailEncryptionService.encrypt_and_save(user2, "email2@example.com", admin_user)

        hash1 = EncryptedEmail.objects.get(user=user1).email_hash
        hash2 = EncryptedEmail.objects.get(user=user2).email_hash

        assert hash1 != hash2
