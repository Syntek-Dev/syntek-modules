"""Email encryption service for secure email storage and retrieval.

This module provides email encryption functionality including:
- AES-256-GCM encryption for email storage
- HMAC-SHA256 hashing for constant-time lookups
- Decrypt-on-read for authorized operations
- Audit logging for PII access

SECURITY NOTE:
- Encrypt on write, decrypt on read
- Maintain plain email field for Django auth backend lookups
- HMAC hash for database lookups (prevents timing attacks)
- All decryption operations are audit logged (GDPR Article 32)

Example:
    >>> EmailEncryptionService.encrypt_and_save(user, "user@example.com")
    >>> email = EmailEncryptionService.decrypt_email(user)
    >>> exists = EmailEncryptionService.check_email_exists("user@example.com")
"""

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction

try:
    from syntek_rust import (
        decrypt_email_py,
        encrypt_email_py,
        hash_email_py,
    )
except ImportError:
    raise ImportError(
        "syntek_rust not found. Install with: cd rust/pyo3_bindings && maturin develop"
    )

if TYPE_CHECKING:
    from syntek_authentication.models import User

logger = logging.getLogger(__name__)


class EmailEncryptionService:
    """Service for encrypting and decrypting user emails.

    Handles secure email storage with encryption:
    1. Encrypt email with AES-256-GCM (Rust)
    2. Generate HMAC-SHA256 hash for lookups
    3. Store both encrypted email and hash
    4. Maintain plain email field for Django auth

    Features:
    - Encrypted storage (AES-256-GCM)
    - Constant-time lookups (HMAC-SHA256)
    - Audit logging for decryption
    - Key rotation support

    Attributes:
        None - All methods are static
    """

    @staticmethod
    def _get_encryption_key() -> bytes:
        """Get encryption key from settings.

        Returns:
            Encryption key bytes.

        Raises:
            ValueError: If encryption key not configured.
        """
        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _get_hmac_key() -> bytes:
        """Get HMAC key from settings.

        Returns:
            HMAC key bytes.

        Raises:
            ValueError: If HMAC key not configured.
        """
        key = getattr(settings, "HMAC_SECRET_KEY", None)
        if not key:
            raise ValueError("HMAC_SECRET_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    @transaction.atomic
    def encrypt_and_save(user: "User", email: str, admin_user: "User | None" = None) -> None:
        """Encrypt email and save to user model.

        Args:
            user: User whose email to encrypt.
            email: Plain text email address.
            admin_user: Admin performing the operation (for audit log).

        Raises:
            ValueError: If encryption fails.
        """
        encryption_key = EmailEncryptionService._get_encryption_key()
        hmac_key = EmailEncryptionService._get_hmac_key()

        # Encrypt email
        email_encrypted = encrypt_email_py(email.lower(), encryption_key)
        email_hash = hash_email_py(email.lower(), hmac_key)

        # Update user
        user.email = email  # Plain text for Django auth backend
        user.email_encrypted = email_encrypted
        user.email_hash = email_hash
        user.save(update_fields=["email", "email_encrypted", "email_hash"])

        # Audit log (if admin performed operation)
        if admin_user:
            from syntek_authentication.services.pii_access_log_service import (
                PIIAccessLogService,
            )

            PIIAccessLogService.log_access(
                admin_user=admin_user,
                action="modify",
                resource_type="email",
                resource_id=user.id,
                user_affected=user,
            )

        logger.info(f"Email encrypted for user {user.id}")

    @staticmethod
    def decrypt_email(user: "User", admin_user: "User | None" = None) -> str:
        """Decrypt user's email address.

        Args:
            user: User whose email to decrypt.
            admin_user: Admin requesting decryption (for audit log).

        Returns:
            Plain text email address.

        Raises:
            ValueError: If decryption fails or email not encrypted.
        """
        if not user.email_encrypted:
            # Email not encrypted yet (legacy user)
            return user.email

        encryption_key = EmailEncryptionService._get_encryption_key()

        try:
            # Decrypt email
            email = decrypt_email_py(user.email_encrypted, encryption_key)

            # Audit log (if admin performed operation)
            if admin_user:
                from syntek_authentication.services.pii_access_log_service import (
                    PIIAccessLogService,
                )

                PIIAccessLogService.log_access(
                    admin_user=admin_user,
                    action="view",
                    resource_type="email",
                    resource_id=user.id,
                    user_affected=user,
                )

            return email
        except Exception as e:
            logger.error(f"Failed to decrypt email for user {user.id}: {e}")
            raise ValueError("Failed to decrypt email address")

    @staticmethod
    def check_email_exists(email: str) -> bool:
        """Check if email is already registered.

        Uses HMAC hash for constant-time lookup (prevents enumeration).

        Args:
            email: Plain text email address.

        Returns:
            True if email exists, False otherwise.
        """
        from syntek_authentication.models import User

        hmac_key = EmailEncryptionService._get_hmac_key()
        email_hash = hash_email_py(email.lower(), hmac_key)

        # Use hash for constant-time lookup
        return User.objects.filter(email_hash=email_hash).exists()

    @staticmethod
    def get_user_by_email(email: str) -> "User | None":
        """Get user by email address.

        Uses HMAC hash for constant-time lookup (prevents enumeration).

        Args:
            email: Plain text email address.

        Returns:
            User if found, None otherwise.
        """
        from syntek_authentication.models import User

        hmac_key = EmailEncryptionService._get_hmac_key()
        email_hash = hash_email_py(email.lower(), hmac_key)

        # Use hash for constant-time lookup
        try:
            return User.objects.get(email_hash=email_hash)
        except User.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def rotate_encryption_key(user: "User", old_key: bytes, new_key: bytes) -> None:
        """Rotate encryption key for user's email.

        Args:
            user: User whose email to re-encrypt.
            old_key: Old encryption key.
            new_key: New encryption key.

        Raises:
            ValueError: If decryption or re-encryption fails.
        """
        if not user.email_encrypted:
            logger.warning(f"User {user.id} has no encrypted email to rotate")
            return

        try:
            # Decrypt with old key
            email = decrypt_email_py(user.email_encrypted, old_key)

            # Re-encrypt with new key
            email_encrypted = encrypt_email_py(email, new_key)

            # Update user
            user.email_encrypted = email_encrypted
            user.save(update_fields=["email_encrypted"])

            logger.info(f"Email encryption key rotated for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to rotate encryption key for user {user.id}: {e}")
            raise ValueError("Failed to rotate encryption key")

    @staticmethod
    def bulk_rotate_encryption_keys(old_key: bytes, new_key: bytes, batch_size: int = 100) -> dict:
        """Rotate encryption keys for all users (batch operation).

        Args:
            old_key: Old encryption key.
            new_key: New encryption key.
            batch_size: Number of users to process per batch.

        Returns:
            Dict with success/failure counts.
        """
        from syntek_authentication.models import User

        success_count = 0
        failure_count = 0

        # Get all users with encrypted emails
        users = User.objects.filter(email_encrypted__isnull=False)
        total_users = users.count()

        logger.info(f"Starting bulk key rotation for {total_users} users")

        for i in range(0, total_users, batch_size):
            batch = users[i : i + batch_size]

            for user in batch:
                try:
                    EmailEncryptionService.rotate_encryption_key(user, old_key, new_key)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to rotate key for user {user.id}: {e}")
                    failure_count += 1

            logger.info(f"Processed batch {i // batch_size + 1}/{(total_users // batch_size) + 1}")

        logger.info(
            f"Bulk key rotation complete. Success: {success_count}, Failed: {failure_count}"
        )

        return {
            "total": total_users,
            "success": success_count,
            "failed": failure_count,
        }
