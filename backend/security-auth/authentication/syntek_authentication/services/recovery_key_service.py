"""Recovery key service for account recovery when MFA is unavailable.

This module provides recovery key functionality including:
- Cryptographically secure key generation
- Algorithm versioning for future upgrades
- Database locking to prevent race conditions
- One-time use enforcement

SECURITY NOTE:
- Uses Rust CSPRNG for key generation
- HMAC-SHA256 hashing (constant-time verification)
- Algorithm versioning (support future algorithm upgrades)
- PostgreSQL SELECT FOR UPDATE (prevent race conditions)
- One-time use only

Example:
    >>> keys = RecoveryKeyService.generate_recovery_keys(user, count=10)
    >>> RecoveryKeyService.verify_and_use_key(user, recovery_key)
    >>> RecoveryKeyService.rotate_keys(user)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

try:
    from syntek_rust import generate_token_py, hash_token_py
except ImportError:
    raise ImportError(
        "syntek_rust not found. Install with: cd rust/pyo3_bindings && maturin develop"
    )

if TYPE_CHECKING:
    from syntek_authentication.models import User

logger = logging.getLogger(__name__)


class RecoveryKeyService:
    """Service for generating and validating recovery keys.

    Handles recovery key lifecycle:
    1. Generate cryptographically secure keys (Rust CSPRNG)
    2. Hash with HMAC-SHA256 (constant-time verification)
    3. Store with algorithm versioning
    4. Verify with database locking (prevent race conditions)
    5. One-time use enforcement

    Features:
    - Algorithm versioning (future-proof)
    - Database locking (PostgreSQL SELECT FOR UPDATE)
    - One-time use enforcement
    - Automatic expiry (1 year default)
    - Key rotation support

    Attributes:
        DEFAULT_KEY_COUNT: Number of recovery keys to generate
        KEY_LENGTH: Length of recovery key in bytes
        KEY_EXPIRY_DAYS: Recovery key validity period
        ALGORITHM_VERSION: Current hashing algorithm version
    """

    DEFAULT_KEY_COUNT = 10
    KEY_LENGTH = 32  # 32 bytes = 256 bits
    KEY_EXPIRY_DAYS = 365  # 1 year
    ALGORITHM_VERSION = "hmac-sha256-v1"

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
    def generate_recovery_keys(user: "User", count: int | None = None) -> list[str]:
        """Generate recovery keys for user.

        Args:
            user: User to generate keys for.
            count: Number of keys to generate (default: DEFAULT_KEY_COUNT).

        Returns:
            List of plain text recovery keys (user must save these).

        Raises:
            ValueError: If key generation fails.
        """
        from syntek_authentication.models import RecoveryKey

        if count is None:
            count = RecoveryKeyService.DEFAULT_KEY_COUNT

        if count < 1 or count > 50:
            raise ValueError("Recovery key count must be between 1 and 50")

        hmac_key = RecoveryKeyService._get_hmac_key()
        expires_at = timezone.now() + timedelta(days=RecoveryKeyService.KEY_EXPIRY_DAYS)

        recovery_keys = []
        created_keys = []

        try:
            for _ in range(count):
                # Generate cryptographically secure key
                key = generate_token_py(RecoveryKeyService.KEY_LENGTH)

                # Hash key for storage
                key_hash = hash_token_py(key, hmac_key)

                # Create algorithm metadata
                algorithm_metadata = {
                    "version": RecoveryKeyService.ALGORITHM_VERSION,
                    "created_at": timezone.now().isoformat(),
                    "key_length": RecoveryKeyService.KEY_LENGTH,
                }

                # Create recovery key record
                recovery_key_obj = RecoveryKey.objects.create(
                    user=user,
                    key_hash=key_hash,
                    algorithm_version=RecoveryKeyService.ALGORITHM_VERSION,
                    algorithm_metadata=algorithm_metadata,
                    expires_at=expires_at,
                )

                recovery_keys.append(key)
                created_keys.append(recovery_key_obj)

            logger.info(f"Generated {count} recovery keys for user {user.id}")

            return recovery_keys

        except Exception as e:
            logger.error(f"Failed to generate recovery keys for user {user.id}: {e}")
            # Rollback will happen automatically due to transaction.atomic
            raise ValueError("Failed to generate recovery keys")

    @staticmethod
    @transaction.atomic
    def verify_and_use_key(user: "User", recovery_key: str) -> bool:
        """Verify and mark recovery key as used (one-time use).

        Uses database locking to prevent race conditions.

        Args:
            user: User attempting to use recovery key.
            recovery_key: Plain text recovery key.

        Returns:
            True if key valid and marked as used, False otherwise.

        Raises:
            ValueError: If no valid keys found.
        """
        from syntek_authentication.models import RecoveryKey

        hmac_key = RecoveryKeyService._get_hmac_key()
        key_hash = hash_token_py(recovery_key, hmac_key)

        # Use SELECT FOR UPDATE to prevent race conditions
        # This locks the row until the transaction commits
        try:
            recovery_key_obj = (
                RecoveryKey.objects.select_for_update()
                .filter(
                    user=user,
                    key_hash=key_hash,
                    used=False,
                )
                .first()
            )

            if not recovery_key_obj:
                logger.warning(f"Invalid or already used recovery key for user {user.id}")
                return False

            # Check if expired
            if recovery_key_obj.is_expired():
                logger.warning(f"Expired recovery key used by user {user.id}")
                return False

            # Mark as used (atomic operation with lock)
            recovery_key_obj.mark_as_used()

            logger.info(f"Recovery key used successfully for user {user.id}")

            return True

        except Exception as e:
            logger.error(f"Failed to verify recovery key for user {user.id}: {e}")
            return False

    @staticmethod
    def get_active_keys_count(user: "User") -> int:
        """Get count of active (unused, unexpired) recovery keys.

        Args:
            user: User to check.

        Returns:
            Number of active recovery keys.
        """
        from syntek_authentication.models import RecoveryKey

        return RecoveryKey.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now(),
        ).count()

    @staticmethod
    @transaction.atomic
    def revoke_all_keys(user: "User") -> int:
        """Revoke all unused recovery keys for user.

        Args:
            user: User whose keys to revoke.

        Returns:
            Number of keys revoked.
        """
        from syntek_authentication.models import RecoveryKey

        revoked_count = RecoveryKey.objects.filter(
            user=user,
            used=False,
        ).update(
            used=True,
            used_at=timezone.now(),
        )

        logger.info(f"Revoked {revoked_count} recovery keys for user {user.id}")

        return revoked_count

    @staticmethod
    @transaction.atomic
    def rotate_keys(user: "User", count: int | None = None) -> list[str]:
        """Rotate recovery keys (revoke old, generate new).

        Args:
            user: User whose keys to rotate.
            count: Number of new keys to generate.

        Returns:
            List of new plain text recovery keys.
        """
        # Revoke all existing keys
        RecoveryKeyService.revoke_all_keys(user)

        # Generate new keys
        new_keys = RecoveryKeyService.generate_recovery_keys(user, count)

        logger.info(f"Rotated recovery keys for user {user.id}, generated {len(new_keys)} new keys")

        return new_keys

    @staticmethod
    def cleanup_expired_keys() -> int:
        """Clean up expired recovery keys (background task).

        Returns:
            Number of keys cleaned up.
        """
        from syntek_authentication.models import RecoveryKey

        deleted_count, _ = RecoveryKey.objects.filter(
            expires_at__lt=timezone.now(),
        ).delete()

        logger.info(f"Cleaned up {deleted_count} expired recovery keys")

        return deleted_count

    @staticmethod
    def validate_key_format(recovery_key: str) -> bool:
        """Validate recovery key format.

        Args:
            recovery_key: Plain text recovery key.

        Returns:
            True if format valid, False otherwise.
        """
        # Check if key is URL-safe base64 and reasonable length
        # 32 bytes = ~43 characters in base64
        if not recovery_key or len(recovery_key) < 40:
            return False

        # Check if contains only valid base64url characters
        import re

        if not re.match(r"^[A-Za-z0-9_-]+$", recovery_key):
            return False

        return True
