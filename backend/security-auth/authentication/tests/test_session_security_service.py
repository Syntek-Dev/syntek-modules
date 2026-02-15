"""
Unit tests for SessionSecurityService.

Tests session validation, device fingerprinting, and IP/UA change detection.
"""

import pytest
from django.contrib.auth import get_user_model

from syntek_authentication.models import SessionSecurity
from syntek_authentication.services import SessionSecurityService

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def session_key():
    """Provide a mock session key."""
    return "test_session_key_12345"


class TestSessionCreation:
    """Test session security record creation."""

    def test_create_session_security_creates_record(self, user, session_key, mock_request):
        """Test that creating session security creates a database record."""
        SessionSecurityService.create_session_security(session_key, user, mock_request)

        assert SessionSecurity.objects.filter(session_key=session_key, user=user).exists()

    def test_create_session_security_stores_ip_hash(self, user, session_key, mock_request):
        """Test that IP address is hashed and stored."""
        SessionSecurityService.create_session_security(session_key, user, mock_request)

        session_security = SessionSecurity.objects.get(session_key=session_key)
        assert session_security.ip_hash is not None
        # IP hash should not be the plaintext IP
        assert session_security.ip_hash != mock_request.META["REMOTE_ADDR"]

    def test_create_session_security_stores_user_agent_hash(self, user, session_key, mock_request):
        """Test that user agent is hashed and stored."""
        SessionSecurityService.create_session_security(session_key, user, mock_request)

        session_security = SessionSecurity.objects.get(session_key=session_key)
        assert session_security.user_agent_hash is not None

    def test_create_session_security_stores_device_fingerprint(
        self, user, session_key, mock_request
    ):
        """Test that device fingerprint is captured."""
        # Add device fingerprint to request
        mock_request.META["HTTP_X_DEVICE_FINGERPRINT"] = '{"screen":"1920x1080","timezone":"UTC"}'

        SessionSecurityService.create_session_security(session_key, user, mock_request)

        session_security = SessionSecurity.objects.get(session_key=session_key)
        assert session_security.device_fingerprint is not None


class TestSessionValidation:
    """Test session validation and suspicious activity detection."""

    def test_validate_session_valid_session(self, user, session_key, mock_request):
        """Test that a valid session passes validation."""
        SessionSecurityService.create_session_security(session_key, user, mock_request)

        is_valid, flags = SessionSecurityService.validate_session(session_key, mock_request)

        assert is_valid is True
        assert len(flags) == 0

    def test_validate_session_detects_ip_change(self, user, session_key, request_factory):
        """Test that IP address changes are detected."""
        # Create session with original IP
        original_request = request_factory.get("/")
        original_request.META["REMOTE_ADDR"] = "192.168.1.100"
        original_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        SessionSecurityService.create_session_security(session_key, user, original_request)

        # Validate with different IP
        new_request = request_factory.get("/")
        new_request.META["REMOTE_ADDR"] = "10.0.0.50"  # Different IP
        new_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"  # Same UA

        is_valid, flags = SessionSecurityService.validate_session(session_key, new_request)

        assert "ip_change" in flags

    def test_validate_session_detects_user_agent_change(self, user, session_key, request_factory):
        """Test that user agent changes are detected."""
        # Create session with original UA
        original_request = request_factory.get("/")
        original_request.META["REMOTE_ADDR"] = "192.168.1.100"
        original_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Windows)"

        SessionSecurityService.create_session_security(session_key, user, original_request)

        # Validate with different UA
        new_request = request_factory.get("/")
        new_request.META["REMOTE_ADDR"] = "192.168.1.100"  # Same IP
        new_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Linux)"  # Different UA

        is_valid, flags = SessionSecurityService.validate_session(session_key, new_request)

        assert "user_agent_change" in flags

    def test_validate_session_detects_device_fingerprint_change(
        self, user, session_key, request_factory
    ):
        """Test that device fingerprint changes are detected."""
        # Create session with original fingerprint
        original_request = request_factory.get("/")
        original_request.META["REMOTE_ADDR"] = "192.168.1.100"
        original_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"
        original_request.META["HTTP_X_DEVICE_FINGERPRINT"] = '{"screen":"1920x1080"}'

        SessionSecurityService.create_session_security(session_key, user, original_request)

        # Validate with different fingerprint
        new_request = request_factory.get("/")
        new_request.META["REMOTE_ADDR"] = "192.168.1.100"
        new_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"
        new_request.META["HTTP_X_DEVICE_FINGERPRINT"] = (
            '{"screen":"1024x768"}'  # Different screen resolution
        )

        is_valid, flags = SessionSecurityService.validate_session(session_key, new_request)

        assert "device_change" in flags

    def test_validate_session_nonexistent_session(self, mock_request):
        """Test that validating a non-existent session returns invalid."""
        is_valid, flags = SessionSecurityService.validate_session(
            "nonexistent_session", mock_request
        )

        assert is_valid is False

    def test_validate_session_multiple_flags(self, user, session_key, request_factory):
        """Test that multiple suspicious changes are all flagged."""
        # Create session
        original_request = request_factory.get("/")
        original_request.META["REMOTE_ADDR"] = "192.168.1.100"
        original_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Windows)"

        SessionSecurityService.create_session_security(session_key, user, original_request)

        # Validate with changed IP and UA
        new_request = request_factory.get("/")
        new_request.META["REMOTE_ADDR"] = "10.0.0.50"  # Changed
        new_request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Linux)"  # Changed

        is_valid, flags = SessionSecurityService.validate_session(session_key, new_request)

        assert "ip_change" in flags
        assert "user_agent_change" in flags


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_create_session_security_missing_ip(self, user, session_key, request_factory):
        """Test handling of requests without IP address."""
        request = request_factory.get("/")
        request.META.pop("REMOTE_ADDR", None)  # Remove IP

        # Should handle gracefully or raise appropriate error
        try:
            SessionSecurityService.create_session_security(session_key, user, request)
        except KeyError:
            # Expected if IP is required
            pass

    def test_create_session_security_missing_user_agent(self, user, session_key, request_factory):
        """Test handling of requests without user agent."""
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"
        # No HTTP_USER_AGENT

        SessionSecurityService.create_session_security(session_key, user, request)

        # Should create record with empty or null user agent hash
        # (Depends on implementation - may be None or empty string)
        assert SessionSecurity.objects.filter(session_key=session_key).exists()

    def test_validate_session_after_update(self, user, session_key, mock_request):
        """Test that session can be updated and revalidated."""
        SessionSecurityService.create_session_security(session_key, user, mock_request)

        # Update session (e.g., after legitimate IP change)
        SessionSecurityService.update_session_security(session_key, mock_request)

        is_valid, flags = SessionSecurityService.validate_session(session_key, mock_request)

        assert is_valid is True


class TestSecurityProperties:
    """Test security properties of session security."""

    def test_ip_addresses_hashed_not_stored_plaintext(self, user, session_key, mock_request):
        """Test that IP addresses are hashed, not stored in plaintext."""
        ip = mock_request.META["REMOTE_ADDR"]

        SessionSecurityService.create_session_security(session_key, user, mock_request)

        session_security = SessionSecurity.objects.get(session_key=session_key)

        # IP hash should not be the plaintext IP
        assert session_security.ip_hash != ip
        assert ip not in session_security.ip_hash

    def test_same_ip_produces_same_hash(self, user, request_factory):
        """Test that the same IP produces the same hash."""
        request1 = request_factory.get("/")
        request1.META["REMOTE_ADDR"] = "192.168.1.100"
        request1.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        request2 = request_factory.get("/")
        request2.META["REMOTE_ADDR"] = "192.168.1.100"  # Same IP
        request2.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="Password1!"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="Password2!"
        )

        SessionSecurityService.create_session_security("session1", user1, request1)
        SessionSecurityService.create_session_security("session2", user2, request2)

        hash1 = SessionSecurity.objects.get(session_key="session1").ip_hash
        hash2 = SessionSecurity.objects.get(session_key="session2").ip_hash

        # Same IP should produce same hash
        assert hash1 == hash2

    def test_different_ips_produce_different_hashes(self, user, request_factory):
        """Test that different IPs produce different hashes."""
        request1 = request_factory.get("/")
        request1.META["REMOTE_ADDR"] = "192.168.1.100"
        request1.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        request2 = request_factory.get("/")
        request2.META["REMOTE_ADDR"] = "10.0.0.50"  # Different IP
        request2.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        SessionSecurityService.create_session_security("session1", user, request1)
        SessionSecurityService.create_session_security("session2", user, request2)

        hash1 = SessionSecurity.objects.get(session_key="session1").ip_hash
        hash2 = SessionSecurity.objects.get(session_key="session2").ip_hash

        assert hash1 != hash2
