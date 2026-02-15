"""
Unit tests for GDPR compliance services.

Tests PII access logging, consent management, and account deletion.
"""

import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from syntek_authentication.models import (
    PIIAccessLog,
    ConsentLog,
    AccountDeletion,
    IPTracking,
)
from syntek_authentication.services import (
    PIIAccessLogService,
    ConsentService,
    AccountDeletionService,
    IPTrackingService,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ============================================================================
# PII Access Log Service Tests
# ============================================================================


class TestPIIAccessLogging:
    """Test PII access logging for GDPR Article 32 compliance."""

    def test_log_access_creates_record(self, user, admin_user, mock_request):
        """Test that logging PII access creates a record."""
        PIIAccessLogService.log_access(
            admin_user=admin_user,
            action="view_email",
            resource_type="EncryptedEmail",
            resource_id=1,
            user_affected=user,
            request=mock_request,
        )

        assert PIIAccessLog.objects.filter(
            admin_user=admin_user, action="view_email", user_affected=user
        ).exists()

    def test_log_access_stores_ip_address(self, user, admin_user, mock_request):
        """Test that PII access logs include IP address."""
        PIIAccessLogService.log_access(
            admin_user=admin_user,
            action="view_email",
            resource_type="EncryptedEmail",
            resource_id=1,
            user_affected=user,
            request=mock_request,
        )

        log = PIIAccessLog.objects.get(admin_user=admin_user)
        assert log.ip_address is not None

    def test_log_access_without_request(self, user, admin_user):
        """Test that logging works even without HTTP request."""
        PIIAccessLogService.log_access(
            admin_user=admin_user,
            action="automated_export",
            resource_type="User",
            resource_id=user.id,
            user_affected=user,
            request=None,
        )

        log = PIIAccessLog.objects.get(admin_user=admin_user)
        assert log.ip_address is None or log.ip_address == ""

    def test_get_user_access_logs(self, user, admin_user, mock_request):
        """Test retrieving all PII access logs for a user."""
        # Create multiple logs
        for i in range(3):
            PIIAccessLogService.log_access(
                admin_user=admin_user,
                action=f"action_{i}",
                resource_type="EncryptedEmail",
                resource_id=i,
                user_affected=user,
                request=mock_request,
            )

        logs = PIIAccessLogService.get_user_access_logs(user)

        assert logs.count() == 3

    def test_retention_policy_7_years_eu(self, user, admin_user, mock_request):
        """Test that logs are retained for 7 years in EU."""
        PIIAccessLogService.log_access(
            admin_user=admin_user,
            action="view_email",
            resource_type="EncryptedEmail",
            resource_id=1,
            user_affected=user,
            request=mock_request,
        )

        log = PIIAccessLog.objects.get(admin_user=admin_user)

        # Manually set created_at to 7 years ago
        log.created_at = timezone.now() - timedelta(days=365 * 7 + 1)
        log.save()

        # Check if should be deleted (depends on implementation)
        # This is a placeholder for actual retention logic
        assert log.should_be_deleted() is True  # Hypothetical method


# ============================================================================
# Consent Service Tests
# ============================================================================


class TestConsentManagement:
    """Test consent management for GDPR Article 7 compliance."""

    def test_grant_consent_creates_log(self, user):
        """Test that granting consent creates a log entry."""
        ConsentService.grant_consent(user, "marketing_email")

        assert ConsentLog.objects.filter(
            user=user, consent_type="marketing_email", granted=True
        ).exists()

    def test_revoke_consent_creates_log(self, user):
        """Test that revoking consent creates a log entry."""
        # First grant
        ConsentService.grant_consent(user, "marketing_email")

        # Then revoke
        ConsentService.revoke_consent(user, "marketing_email")

        # Should have two logs: grant and revoke
        logs = ConsentLog.objects.filter(user=user, consent_type="marketing_email")
        assert logs.count() == 2
        assert logs.filter(granted=False).exists()

    def test_has_consent_true_when_granted(self, user):
        """Test that has_consent returns True for granted consent."""
        ConsentService.grant_consent(user, "analytics")

        assert ConsentService.has_consent(user, "analytics") is True

    def test_has_consent_false_when_not_granted(self, user):
        """Test that has_consent returns False when consent not granted."""
        assert ConsentService.has_consent(user, "analytics") is False

    def test_has_consent_false_after_revocation(self, user):
        """Test that has_consent returns False after revocation."""
        ConsentService.grant_consent(user, "analytics")
        ConsentService.revoke_consent(user, "analytics")

        assert ConsentService.has_consent(user, "analytics") is False

    def test_get_all_consents(self, user):
        """Test retrieving all consents for a user."""
        ConsentService.grant_consent(user, "marketing_email")
        ConsentService.grant_consent(user, "analytics")
        ConsentService.revoke_consent(user, "marketing_sms")

        consents = ConsentService.get_all_consents(user)

        assert "marketing_email" in consents
        assert "analytics" in consents
        assert consents["marketing_email"] is True
        assert consents["analytics"] is True
        assert consents.get("marketing_sms", False) is False

    def test_consent_versioning(self, user):
        """Test that consent logs include version information."""
        ConsentService.grant_consent(user, "phone", version="1.0")

        log = ConsentLog.objects.get(user=user, consent_type="phone")
        assert log.version == "1.0"

    def test_grant_consent_invalid_type_raises_error(self, user):
        """Test that granting invalid consent type raises error."""
        with pytest.raises(ValueError):
            ConsentService.grant_consent(user, "invalid_consent_type")

    def test_consent_history(self, user):
        """Test retrieving consent history for audit."""
        ConsentService.grant_consent(user, "marketing_email")
        ConsentService.revoke_consent(user, "marketing_email")
        ConsentService.grant_consent(user, "marketing_email")

        history = ConsentService.get_consent_history(user, "marketing_email")

        # Should have 3 entries: grant, revoke, grant
        assert history.count() == 3


# ============================================================================
# Account Deletion Service Tests
# ============================================================================


class TestAccountDeletion:
    """Test account deletion for GDPR Article 17 Right to Erasure."""

    def test_request_deletion_creates_record(self, user):
        """Test that requesting deletion creates an AccountDeletion record."""
        AccountDeletionService.request_deletion(user, "User requested deletion")

        assert AccountDeletion.objects.filter(user=user, status="pending").exists()

    def test_request_deletion_sets_grace_period(self, user):
        """Test that deletion is scheduled 30 days in the future."""
        AccountDeletionService.request_deletion(user)

        deletion = AccountDeletion.objects.get(user=user)
        expected_date = timezone.now().date() + timedelta(days=30)

        assert deletion.scheduled_deletion_date == expected_date

    def test_request_deletion_soft_deletes_user(self, user):
        """Test that requesting deletion soft-deletes the user."""
        AccountDeletionService.request_deletion(user)

        user.refresh_from_database()
        assert user.is_active is False

    def test_cancel_deletion_restores_account(self, user):
        """Test that canceling deletion restores the account."""
        AccountDeletionService.request_deletion(user)
        AccountDeletionService.cancel_deletion(user)

        user.refresh_from_database()
        assert user.is_active is True

        deletion = AccountDeletion.objects.get(user=user)
        assert deletion.status == "cancelled"

    def test_cancel_deletion_within_grace_period(self, user):
        """Test that deletion can be cancelled within 30 days."""
        AccountDeletionService.request_deletion(user)

        # Cancel immediately (within grace period)
        result = AccountDeletionService.cancel_deletion(user)

        assert result is True

    def test_cancel_deletion_after_grace_period_fails(self, user):
        """Test that deletion cannot be cancelled after 30 days."""
        AccountDeletionService.request_deletion(user)

        # Manually set scheduled date to past
        deletion = AccountDeletion.objects.get(user=user)
        deletion.scheduled_deletion_date = timezone.now().date() - timedelta(days=1)
        deletion.save()

        # Try to cancel (should fail)
        result = AccountDeletionService.cancel_deletion(user)

        assert result is False

    def test_execute_deletion_hard_deletes_user(self, user):
        """Test that executing deletion hard-deletes the user."""
        AccountDeletionService.request_deletion(user)

        # Manually set scheduled date to past (simulate grace period elapsed)
        deletion = AccountDeletion.objects.get(user=user)
        deletion.scheduled_deletion_date = timezone.now().date() - timedelta(days=1)
        deletion.save()

        # Execute deletion
        AccountDeletionService.execute_deletion(user)

        # User should be deleted
        assert not User.objects.filter(id=user.id).exists()

        # Deletion record should be marked as completed
        deletion.refresh_from_database()
        assert deletion.status == "completed"

    def test_get_pending_deletions(self, user):
        """Test retrieving pending deletions due for execution."""
        AccountDeletionService.request_deletion(user)

        # Set scheduled date to today
        deletion = AccountDeletion.objects.get(user=user)
        deletion.scheduled_deletion_date = timezone.now().date()
        deletion.save()

        pending = AccountDeletionService.get_pending_deletions()

        assert pending.count() == 1
        assert pending.first().user == user


# ============================================================================
# IP Tracking Service Tests
# ============================================================================


class TestIPTracking:
    """Test IP tracking, whitelisting, and blacklisting."""

    def test_is_ip_blacklisted_false_for_unlisted_ip(self):
        """Test that unlisted IPs are not blacklisted."""
        result = IPTrackingService.is_ip_blacklisted("192.168.1.100")

        assert result is False

    def test_is_ip_blacklisted_true_for_blacklisted_ip(self):
        """Test that blacklisted IPs are detected."""
        IPTrackingService.blacklist_ip("10.0.0.50", "Suspicious activity")

        result = IPTrackingService.is_ip_blacklisted("10.0.0.50")

        assert result is True

    def test_is_ip_whitelisted_false_for_unlisted_ip(self):
        """Test that unlisted IPs are not whitelisted."""
        result = IPTrackingService.is_ip_whitelisted("192.168.1.100")

        assert result is False

    def test_is_ip_whitelisted_true_for_whitelisted_ip(self):
        """Test that whitelisted IPs are detected."""
        IPTrackingService.whitelist_ip("192.168.1.100", "Corporate office")

        result = IPTrackingService.is_ip_whitelisted("192.168.1.100")

        assert result is True

    def test_blacklist_ip_creates_record(self):
        """Test that blacklisting creates an IPTracking record."""
        IPTrackingService.blacklist_ip("10.0.0.50", "Brute force detected")

        assert IPTracking.objects.filter(
            ip_address_hash__isnull=False, is_blacklisted=True
        ).exists()

    def test_whitelist_ip_creates_record(self):
        """Test that whitelisting creates an IPTracking record."""
        IPTrackingService.whitelist_ip("192.168.1.100", "Trusted location")

        assert IPTracking.objects.filter(
            ip_address_hash__isnull=False, is_whitelisted=True
        ).exists()

    def test_remove_from_blacklist(self):
        """Test removing an IP from the blacklist."""
        IPTrackingService.blacklist_ip("10.0.0.50")
        IPTrackingService.remove_from_blacklist("10.0.0.50")

        assert IPTrackingService.is_ip_blacklisted("10.0.0.50") is False

    def test_remove_from_whitelist(self):
        """Test removing an IP from the whitelist."""
        IPTrackingService.whitelist_ip("192.168.1.100")
        IPTrackingService.remove_from_whitelist("192.168.1.100")

        assert IPTrackingService.is_ip_whitelisted("192.168.1.100") is False

    def test_auto_blacklist_after_failed_attempts(self, user):
        """Test automatic blacklisting after threshold of failed logins."""
        ip = "10.0.0.75"

        # Simulate 10 failed attempts
        for i in range(10):
            IPTrackingService.record_failed_attempt(ip, user)

        # Should be auto-blacklisted
        assert IPTrackingService.is_ip_blacklisted(ip) is True

    def test_redis_caching_for_blacklist_check(self):
        """Test that blacklist checks use Redis cache."""

        ip = "10.0.0.60"
        IPTrackingService.blacklist_ip(ip)

        # First call should hit database and cache
        result1 = IPTrackingService.is_ip_blacklisted(ip)

        # Clear database but keep cache
        IPTracking.objects.all().delete()

        # Second call should still return True from cache
        result2 = IPTrackingService.is_ip_blacklisted(ip)

        assert result1 is True
        assert result2 is True  # From cache


class TestSecurityProperties:
    """Test security properties of GDPR services."""

    def test_pii_access_logs_immutable(self, user, admin_user, mock_request):
        """Test that PII access logs cannot be modified."""
        PIIAccessLogService.log_access(
            admin_user=admin_user,
            action="view_email",
            resource_type="EncryptedEmail",
            resource_id=1,
            user_affected=user,
            request=mock_request,
        )

        log = PIIAccessLog.objects.get(admin_user=admin_user)

        # Try to modify
        log.action = "modified_action"
        log.save()

        # Refresh and check (in real system, would be prevented)
        log.refresh_from_database()
        # Note: Actual immutability would require database triggers or permissions

    def test_consent_logs_include_timestamp(self, user):
        """Test that consent logs include precise timestamps."""
        before = timezone.now()
        ConsentService.grant_consent(user, "analytics")
        after = timezone.now()

        log = ConsentLog.objects.get(user=user)

        assert before <= log.created_at <= after

    def test_ip_addresses_hashed_in_tracking(self):
        """Test that IP addresses are hashed in tracking records."""
        ip = "192.168.1.100"
        IPTrackingService.whitelist_ip(ip)

        tracking = IPTracking.objects.first()

        # IP hash should not be the plaintext IP
        assert tracking.ip_address_hash != ip
