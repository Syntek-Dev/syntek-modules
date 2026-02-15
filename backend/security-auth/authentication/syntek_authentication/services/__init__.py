"""Authentication services.

Exports all authentication-related services for easy importing.
"""

# Existing services
from .auth_service import AuthService
from .email_service import EmailService
from .email_verification_service import EmailVerificationService
from .failed_login_service import FailedLoginService
from .password_reset_service import PasswordResetService

# New Phase 1 services
from .account_deletion_service import AccountDeletionService
from .auto_logout_service import AutoLogoutService
from .consent_service import ConsentService
from .email_encryption_service import EmailEncryptionService
from .ip_tracking_service import IPTrackingService
from .oauth_callback_service import OAuthCallbackService
from .oauth_service import OAuthService
from .phone_verification_service import PhoneVerificationService
from .pii_access_log_service import PIIAccessLogService
from .recovery_key_service import RecoveryKeyService
from .session_security_service import SessionSecurityService

__all__ = [
    # Existing services
    "AuthService",
    "EmailService",
    "EmailVerificationService",
    "FailedLoginService",
    "PasswordResetService",
    # New Phase 1 services
    "AccountDeletionService",
    "AutoLogoutService",
    "ConsentService",
    "EmailEncryptionService",
    "IPTrackingService",
    "OAuthCallbackService",
    "OAuthService",
    "PhoneVerificationService",
    "PIIAccessLogService",
    "RecoveryKeyService",
    "SessionSecurityService",
]
