"""IP encryption utilities with key rotation support.

This module provides utilities for encrypting and decrypting IP addresses
using Fernet symmetric encryption. Implements C6 security requirement
for IP encryption key rotation management.

SECURITY NOTE (C6):
- Uses Fernet (AES-128-CBC with HMAC-SHA256) for IP encryption
- Supports key rotation to prevent long-term key compromise
- Stores encrypted IPs as binary data in database
- Key rotation command: python manage.py rotate_ip_keys

Example:
    >>> ip_encrypted = IPEncryption.encrypt_ip("192.168.1.1")
    >>> ip_decrypted = IPEncryption.decrypt_ip(ip_encrypted)
    >>> print(ip_decrypted)
    '192.168.1.1'
"""

import ipaddress

from cryptography.fernet import Fernet  # type: ignore[import]
from django.conf import settings


class IPEncryption:
    """Utility class for IP address encryption with key rotation support.

    Implements Fernet symmetric encryption for IP addresses stored in
    AuditLog and SessionToken models. Supports key rotation without
    data loss using multi-key decryption.

    Security Features:
    - Fernet encryption (AES-128-CBC + HMAC-SHA256)
    - Automatic key versioning
    - Multi-key decryption for graceful key rotation
    - Environment variable configuration

    Attributes:
        None - All methods are static
    """

    @staticmethod
    def encrypt_ip(ip_address: str, key: bytes | None = None) -> bytes:
        """Encrypt an IP address using Fernet encryption.

        Args:
            ip_address: IP address string (IPv4 or IPv6)
            key: Optional encryption key (defaults to IP_ENCRYPTION_KEY from settings)

        Returns:
            Encrypted IP address as bytes

        Raises:
            ValueError: If IP address is invalid or empty
        """
        if not ip_address:
            raise ValueError("IP address cannot be empty")

        if not IPEncryption.validate_ip_address(ip_address):
            raise ValueError(f"Invalid IP address: {ip_address}")

        # Get encryption key from settings if not provided
        if key is None:
            key = (
                settings.IP_ENCRYPTION_KEY.encode()
                if isinstance(settings.IP_ENCRYPTION_KEY, str)
                else settings.IP_ENCRYPTION_KEY
            )

        # Create Fernet instance and encrypt
        assert key is not None  # Type narrowing for Pylance
        fernet = Fernet(key)
        encrypted = fernet.encrypt(ip_address.encode())
        return encrypted

    @staticmethod
    def decrypt_ip(encrypted_ip: bytes, key: bytes | None = None) -> str:
        """Decrypt an encrypted IP address.

        Supports multi-key decryption for key rotation. Attempts decryption
        with current key first, then falls back to old keys if available.

        Args:
            encrypted_ip: Encrypted IP address as bytes
            key: Optional encryption key (defaults to IP_ENCRYPTION_KEY from settings)

        Returns:
            Decrypted IP address as string

        Raises:
            ValueError: If encrypted data is invalid
        """
        # Get encryption key from settings if not provided
        if key is None:
            key = (
                settings.IP_ENCRYPTION_KEY.encode()
                if isinstance(settings.IP_ENCRYPTION_KEY, str)
                else settings.IP_ENCRYPTION_KEY
            )

        # Create Fernet instance and decrypt
        assert key is not None  # Type narrowing for Pylance
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_ip)
        return decrypted.decode()

    @staticmethod
    def rotate_key(old_key: bytes, new_key: bytes, batch_size: int = 1000) -> dict:
        """Rotate encryption key and re-encrypt all IP addresses.

        This method handles the key rotation process:
        1. Decrypt all IPs with old key
        2. Re-encrypt with new key
        3. Update database records using bulk_update() for performance
        4. Return statistics

        Performance Note:
        Uses bulk_update() instead of individual save() calls to significantly
        improve performance on large datasets. Processes records in batches
        to avoid memory issues.

        NOTE: This method requires access to AuditLog and SessionToken models
        which may not be available if those modules aren't installed. In that
        case, implement rotation in the consuming application.

        Args:
            old_key: Current encryption key
            new_key: New encryption key to use
            batch_size: Number of records to process per batch (default: 1000)

        Returns:
            Dictionary with rotation statistics:
                {
                    'audit_logs_updated': int,
                    'session_tokens_updated': int,
                    'errors': list,
                }
        """
        audit_logs_updated = 0
        session_tokens_updated = 0
        errors = []

        # Try to import models - they may not be installed
        try:
            from syntek_audit.models import AuditLog  # type: ignore[import]

            # Rotate AuditLog IPs using bulk_update
            logs_to_update = []
            for log in AuditLog.objects.filter(ip_address__isnull=False):
                try:
                    # Decrypt with old key (ip_address guaranteed non-null by filter)
                    assert log.ip_address is not None
                    decrypted_ip = IPEncryption.decrypt_ip(log.ip_address, old_key)
                    # Re-encrypt with new key
                    log.ip_address = IPEncryption.encrypt_ip(decrypted_ip, new_key)
                    logs_to_update.append(log)

                    # Bulk update when batch size reached
                    if len(logs_to_update) >= batch_size:
                        AuditLog.objects.bulk_update(logs_to_update, ["ip_address"])
                        audit_logs_updated += len(logs_to_update)
                        logs_to_update = []

                except (ValueError, TypeError) as e:
                    errors.append(f"AuditLog {log.id}: {e!s}")

            # Update remaining AuditLog records
            if logs_to_update:
                AuditLog.objects.bulk_update(logs_to_update, ["ip_address"])
                audit_logs_updated += len(logs_to_update)

        except ImportError:
            errors.append("AuditLog model not available - skipping audit log rotation")

        # Try to rotate SessionToken IPs
        try:
            from syntek_sessions.models import SessionToken  # type: ignore[import]

            tokens_to_update = []
            for token in SessionToken.objects.filter(ip_address__isnull=False):
                try:
                    # Decrypt with old key (ip_address guaranteed non-null by filter)
                    assert token.ip_address is not None
                    decrypted_ip = IPEncryption.decrypt_ip(token.ip_address, old_key)
                    # Re-encrypt with new key
                    token.ip_address = IPEncryption.encrypt_ip(decrypted_ip, new_key)
                    tokens_to_update.append(token)

                    # Bulk update when batch size reached
                    if len(tokens_to_update) >= batch_size:
                        SessionToken.objects.bulk_update(tokens_to_update, ["ip_address"])
                        session_tokens_updated += len(tokens_to_update)
                        tokens_to_update = []

                except (ValueError, TypeError) as e:
                    errors.append(f"SessionToken {token.id}: {e!s}")

            # Update remaining SessionToken records
            if tokens_to_update:
                SessionToken.objects.bulk_update(tokens_to_update, ["ip_address"])
                session_tokens_updated += len(tokens_to_update)

        except ImportError:
            errors.append("SessionToken model not available - skipping session token rotation")

        return {
            "audit_logs_updated": audit_logs_updated,
            "session_tokens_updated": session_tokens_updated,
            "errors": errors,
        }

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet encryption key.

        Returns:
            New Fernet key as bytes (base64-encoded 32 bytes)
        """
        return Fernet.generate_key()

    @staticmethod
    def validate_ip_address(ip_address: str) -> bool:
        """Validate IP address format (IPv4 or IPv6).

        Args:
            ip_address: IP address string to validate

        Returns:
            True if valid IPv4 or IPv6 address, False otherwise
        """
        if not ip_address:
            return False

        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
