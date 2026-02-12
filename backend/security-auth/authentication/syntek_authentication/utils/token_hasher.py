"""Token hashing utilities using HMAC-SHA256.

This module provides secure token hashing using HMAC-SHA256 with a dedicated
signing key. Implements C1 security requirement for HMAC-based token hashing
instead of plain SHA-256.

SECURITY NOTE (C1):
- Uses HMAC-SHA256 with TOKEN_SIGNING_KEY (NOT SECRET_KEY)
- Prevents rainbow table attacks on token hashes
- Dedicated key prevents cross-contamination with Django SECRET_KEY
- Hash-then-store pattern for all tokens (session, reset, verification)

SECURITY NOTE (C3):
- Password reset tokens use hash-then-store pattern
- Only hash stored in database, plain token never persisted
- Token comparison uses constant-time comparison

Example:
    >>> token = "abcd1234"
    >>> token_hash = TokenHasher.hash_token(token)
    >>> is_valid = TokenHasher.verify_token(token, token_hash)
    >>> print(is_valid)
    True
"""

import base64
import hashlib
import hmac
import secrets

from django.conf import settings


class TokenHasher:
    """Utility class for secure token hashing using HMAC-SHA256.

    Implements HMAC-SHA256 hashing for all authentication tokens including
    JWT access tokens, refresh tokens, password reset tokens, and email
    verification tokens.

    Security Features:
    - HMAC-SHA256 with dedicated TOKEN_SIGNING_KEY
    - Constant-time comparison to prevent timing attacks
    - Base64 encoding for database storage
    - Separate from Django SECRET_KEY

    Attributes:
        None - All methods are static
    """

    @staticmethod
    def hash_token(token: str, key: bytes | None = None) -> str:
        """Hash a token using HMAC-SHA256.

        Args:
            token: Plain token string to hash
            key: Optional signing key (defaults to TOKEN_SIGNING_KEY from settings)

        Returns:
            Base64-encoded HMAC-SHA256 hash as string

        Raises:
            ValueError: If token is empty
        """
        if not token:
            raise ValueError("Token cannot be empty")

        # Get signing key from settings if not provided
        if key is None:
            key = (
                settings.TOKEN_SIGNING_KEY.encode()
                if isinstance(settings.TOKEN_SIGNING_KEY, str)
                else settings.TOKEN_SIGNING_KEY
            )

        # Create HMAC-SHA256 hash
        assert key is not None  # Type narrowing for Pylance
        token_bytes = token.encode("utf-8")
        hmac_hash = hmac.new(key, token_bytes, hashlib.sha256).digest()

        # Base64 encode for storage
        return base64.b64encode(hmac_hash).decode("utf-8")

    @staticmethod
    def verify_token(token: str, token_hash: str, key: bytes | None = None) -> bool:
        """Verify a token against its hash using constant-time comparison.

        Args:
            token: Plain token string to verify
            token_hash: Base64-encoded hash to compare against
            key: Optional signing key (defaults to TOKEN_SIGNING_KEY from settings)

        Returns:
            True if token matches hash, False otherwise
        """
        # Hash the provided token
        computed_hash = TokenHasher.hash_token(token, key)

        # Use constant-time comparison
        return TokenHasher.constant_time_compare(computed_hash, token_hash)

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token.

        Uses secrets module for cryptographic randomness. Default length
        provides 256 bits of entropy (32 bytes hex = 64 characters).

        Args:
            length: Number of random bytes (default: 32 bytes = 256 bits)

        Returns:
            Hex-encoded random token string

        Raises:
            ValueError: If length < 16 (insufficient entropy)
        """
        if length < 16:
            raise ValueError("Token length must be at least 16 bytes for sufficient entropy")

        # Generate cryptographically secure random bytes
        return secrets.token_hex(length)

    @staticmethod
    def constant_time_compare(val1: str, val2: str) -> bool:
        """Compare two strings in constant time to prevent timing attacks.

        Args:
            val1: First string to compare
            val2: Second string to compare

        Returns:
            True if strings are equal, False otherwise
        """
        # Use hmac.compare_digest for constant-time comparison
        return hmac.compare_digest(val1, val2)
