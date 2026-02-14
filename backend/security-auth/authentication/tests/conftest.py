"""
Pytest fixtures for authentication tests.

Provides reusable fixtures for users, sessions, keys, and test data.
"""

import os
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing PII access logging."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="AdminPassword123!"
    )


@pytest.fixture
def request_factory():
    """Provide Django RequestFactory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a mock HTTP request."""
    request = request_factory.get("/")
    request.META["REMOTE_ADDR"] = "192.168.1.100"
    request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    return request


@pytest.fixture
def encryption_key():
    """Generate a 32-byte encryption key for testing."""
    return os.urandom(32)


@pytest.fixture
def hmac_key():
    """Generate a 32-byte HMAC key for testing."""
    return os.urandom(32)


@pytest.fixture
def test_email():
    """Provide a valid test email address."""
    return "user@example.com"


@pytest.fixture
def test_phone():
    """Provide a valid test phone number (E.164 format)."""
    return "+15551234567"


@pytest.fixture
def test_ip():
    """Provide a valid test IP address."""
    return "192.168.1.1"


@pytest.fixture(autouse=True)
def set_test_encryption_keys(settings, encryption_key, hmac_key, tmp_path):
    """
    Automatically set test encryption keys for all tests.

    Uses temporary files to store keys for the duration of tests.
    """
    # Create temporary key files
    encryption_key_file = tmp_path / "test_encryption.key"
    hmac_key_file = tmp_path / "test_hmac.key"

    encryption_key_file.write_bytes(encryption_key)
    hmac_key_file.write_bytes(hmac_key)

    # Set Django settings
    settings.ENCRYPTION_KEY_PATH = str(encryption_key_file)
    settings.HMAC_KEY_PATH = str(hmac_key_file)

    return {
        "encryption_key": encryption_key,
        "hmac_key": hmac_key,
        "encryption_key_path": str(encryption_key_file),
        "hmac_key_path": str(hmac_key_file),
    }


@pytest.fixture
def past_datetime():
    """Provide a datetime in the past (30 days ago)."""
    return timezone.now() - timedelta(days=30)


@pytest.fixture
def future_datetime():
    """Provide a datetime in the future (30 days from now)."""
    return timezone.now() + timedelta(days=30)
