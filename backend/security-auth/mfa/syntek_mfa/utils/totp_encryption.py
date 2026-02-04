"""TOTP secret encryption using Fernet symmetric encryption.

This module implements secure encryption for TOTP secrets to prevent 2FA bypass
if the database is compromised (C2 security requirement).

Uses Fernet encryption with a dedicated key separate from other secrets to limit
the blast radius if any single key is compromised.

SECURITY NOTE:
- TOTP secrets are encrypted at rest using Fernet (AES-128 CBC with HMAC-SHA256)
- The encryption key MUST be stored in environment variables, not in the codebase
- Key rotation is supported to migrate existing secrets to a new key
- The encryption key should be at least 32 bytes (256 bits) for strong security

Example:
    >>> from syntek_mfa.utils.totp_encryption import TOTPEncryption
    >>> encrypted = TOTPEncryption.encrypt_secret("JBSWY3DPEHPK3PXP")
    >>> decrypted = TOTPEncryption.decrypt_secret(encrypted)
    >>> decrypted == "JBSWY3DPEHPK3PXP"
    True
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cryptography.fernet import Fernet  # type: ignore[import]


class TOTPEncryption:
    """Fernet encryption for TOTP secrets.

    Implements secure encryption/decryption of TOTP secrets using Fernet
    symmetric encryption (C2 requirement). Uses a separate encryption key
    from other secrets to limit blast radius if compromised.

    The encryption key must be set in Django settings as TOTP_ENCRYPTION_KEY.
    Generate a key with: Fernet.generate_key().decode()

    Attributes:
        _cipher: Cached Fernet cipher instance (class-level cache).
    """

    _cipher = None

    @classmethod
    def _get_cipher(cls) -> Fernet:
        """Get or create the Fernet cipher instance.

        Retrieves the TOTP_ENCRYPTION_KEY from Django settings and creates
        a Fernet cipher. Caches the cipher for performance.

        Returns:
            Fernet cipher instance for encryption/decryption.

        Raises:
            ImproperlyConfigured: If TOTP_ENCRYPTION_KEY is not set in settings.

        Example:
            >>> cipher = TOTPEncryption._get_cipher()
            >>> isinstance(cipher, Fernet)
            True
        """
        if cls._cipher is None:
            key = getattr(settings, "TOTP_ENCRYPTION_KEY", None)
            if not key:
                raise ImproperlyConfigured(
                    "TOTP_ENCRYPTION_KEY must be set in Django settings. "
                    "Generate one with: python -c 'from cryptography.fernet "
                    "import Fernet; print(Fernet.generate_key().decode())'"
                )
            # Handle both string and bytes keys
            key_bytes = key.encode() if isinstance(key, str) else key
            cls._cipher = Fernet(key_bytes)
        return cls._cipher

    @classmethod
    def encrypt_secret(cls, secret: str) -> bytes:
        """Encrypt a TOTP secret using Fernet (C2).

        Encrypts the plain text TOTP secret before storage in the database.
        The encrypted value can only be decrypted with the same key.

        Args:
            secret: Plain text TOTP secret (base32 encoded string).

        Returns:
            Encrypted secret as bytes suitable for database storage.

        Example:
            >>> encrypted = TOTPEncryption.encrypt_secret("JBSWY3DPEHPK3PXP")
            >>> isinstance(encrypted, bytes)
            True
            >>> len(encrypted) > 0
            True
        """
        cipher = cls._get_cipher()
        return cipher.encrypt(secret.encode())

    @classmethod
    def decrypt_secret(cls, encrypted_secret: bytes) -> str:
        """Decrypt a TOTP secret using Fernet (C2).

        Decrypts an encrypted TOTP secret for verification operations.
        Should only be called when actually verifying a token, not for display.

        Args:
            encrypted_secret: Encrypted TOTP secret from database.

        Returns:
            Plain text TOTP secret (base32 encoded string).

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails due to
                wrong key, corrupted data, or tampered ciphertext.

        Example:
            >>> secret = "JBSWY3DPEHPK3PXP"
            >>> encrypted = TOTPEncryption.encrypt_secret(secret)
            >>> decrypted = TOTPEncryption.decrypt_secret(encrypted)
            >>> decrypted == secret
            True
        """
        cipher = cls._get_cipher()
        return cipher.decrypt(encrypted_secret).decode()

    @classmethod
    def rotate_key(cls, old_key: str, new_key: str, encrypted_secret: bytes) -> bytes:
        """Re-encrypt a secret with a new encryption key.

        Used during key rotation to migrate existing encrypted secrets
        to a new encryption key without requiring users to re-enroll.

        Args:
            old_key: Previous Fernet encryption key.
            new_key: New Fernet encryption key.
            encrypted_secret: Secret encrypted with the old key.

        Returns:
            Secret re-encrypted with the new key.

        Raises:
            cryptography.fernet.InvalidToken: If old_key cannot decrypt
                the encrypted_secret.

        Example:
            >>> old_key = Fernet.generate_key().decode()
            >>> new_key = Fernet.generate_key().decode()
            >>> secret = "JBSWY3DPEHPK3PXP"
            >>> old_cipher = Fernet(old_key.encode())
            >>> encrypted = old_cipher.encrypt(secret.encode())
            >>> rotated = TOTPEncryption.rotate_key(old_key, new_key, encrypted)
            >>> new_cipher = Fernet(new_key.encode())
            >>> new_cipher.decrypt(rotated).decode() == secret
            True
        """
        # Decrypt with old key
        old_cipher = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        plain_secret = old_cipher.decrypt(encrypted_secret).decode()

        # Encrypt with new key
        new_cipher = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
        return new_cipher.encrypt(plain_secret.encode())

    @classmethod
    def clear_cipher_cache(cls) -> None:
        """Clear the cached cipher instance.

        Useful for testing or when the encryption key changes.
        Forces the next encryption/decryption to reload the key from settings.

        Example:
            >>> TOTPEncryption.clear_cipher_cache()
            >>> TOTPEncryption._cipher is None
            True
        """
        cls._cipher = None
