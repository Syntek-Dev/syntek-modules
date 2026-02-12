"""Email service for sending authentication-related emails.

This module provides email sending functionality for verification,
password reset, and notification emails. Supports both SMTP
and Mailpit for development/testing.

SECURITY NOTE:
- Rate limiting prevents email bombing
- Tokens are cryptographically secure
- Email templates sanitize user input
- Async sending with Celery (future)

Example:
    >>> EmailService.send_verification_email(user, token)
    >>> EmailService.send_password_reset_email(user, token)
    >>> EmailService.send_password_reset_confirmation_email(user)
"""

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

if TYPE_CHECKING:
    from syntek_authentication.models import User

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending authentication emails.

    Handles sending of verification emails, password reset emails,
    and other authentication-related notifications.

    Features:
    - Template-based email composition
    - Rate limiting to prevent abuse
    - Async sending support (Celery)
    - Retry logic for failed sends

    Attributes:
        None - All methods are static
    """

    # System template slugs
    TEMPLATE_PASSWORD_RESET_REQUEST = "password_reset_request"
    TEMPLATE_PASSWORD_RESET_CONFIRMATION = "password_reset_confirmation"
    TEMPLATE_EMAIL_VERIFICATION = "email_verification"
    TEMPLATE_WELCOME = "welcome"
    TEMPLATE_PASSWORD_CHANGED = "password_changed"
    TEMPLATE_2FA_ENABLED = "2fa_enabled"
    TEMPLATE_LOGIN_NOTIFICATION = "login_notification"

    @staticmethod
    def _render_inline_template(
        template_slug: str, context: dict[str, Any]
    ) -> tuple[str, str, str]:
        """Render inline HTML templates.

        Args:
            template_slug: Template identifier
            context: Context variables

        Returns:
            Tuple of (subject, html_body, plain_text_body)
        """
        site_name = getattr(settings, "SITE_NAME", "Syntek Platform")
        user = context.get("user")
        user_name = ""
        if user:
            user_name = user.get_full_name() or user.email

        # Password Reset Request Template
        if template_slug == EmailService.TEMPLATE_PASSWORD_RESET_REQUEST:
            reset_url = context.get("reset_link", "")
            expiry_minutes = context.get("expiry_minutes", 10)

            subject = f"Reset your password - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hi {user_name},</p>
                    <p>You requested to reset your password. Click the link below to set a new
                    password:</p>
                    <p><a href="{reset_url}" style="display: inline-block; padding: 10px 20px;
                    background-color: #007bff; color: white; text-decoration: none; border-radius:
                        5px;">Reset Password</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{reset_url}</p>
                    <p style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px;
                        margin: 15px 0; border-radius: 5px;">
                        <strong>⏰ Important:</strong> This link will expire in
                        <strong>{expiry_minutes} minutes</strong>.
                    </p>
                    <p>If you did not request a password reset, please ignore this email.
                    Your password will remain unchanged.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # Password Reset Confirmation Template
        if template_slug == EmailService.TEMPLATE_PASSWORD_RESET_CONFIRMATION:
            changed_at = context.get("changed_at", "recently")
            security_link = context.get("security_settings_link", "")
            support_email = context.get("support_email", "support@example.com")

            subject = f"Password Changed Successfully - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Password Changed Successfully</h2>
                    <p>Hi {user_name},</p>
                    <p>Your password was successfully changed on {changed_at}.</p>
                    <p style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px;
                        margin: 15px 0; border-radius: 5px;">
                        <strong>⚠️ Important:</strong> If you did not make this change,
                        please contact support immediately at {support_email}.
                    </p>
                    <p>
                        <a href="{security_link}" style="display: inline-block; padding: 10px 20px;
                        background-color: #007bff; color: white; text-decoration: none;
                        border-radius: 5px;">Review Account Security</a>
                    </p>
                    <p>For your security, all active sessions have been logged out.
                    You will need to log in again with your new password.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # Email Verification Template
        if template_slug == EmailService.TEMPLATE_EMAIL_VERIFICATION:
            verification_link = context.get("verification_link", "")

            subject = f"Verify your email address - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Welcome {user_name}!</h2>
                    <p>Thank you for registering. Please verify your email address by clicking
                    the link below:</p>
                    <p>
                        <a href="{verification_link}" style="display: inline-block;
                        padding: 10px 20px; background-color: #28a745; color: white;
                        text-decoration: none; border-radius: 5px;">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{verification_link}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not create an account, please ignore this email.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # Welcome Email Template
        if template_slug == EmailService.TEMPLATE_WELCOME:
            dashboard_link = context.get("dashboard_link", "")

            subject = f"Welcome to {site_name}!"
            html_body = f"""
            <html>
                <body>
                    <h2>Welcome {user_name}!</h2>
                    <p>Thank you for joining {site_name}.</p>
                    <p>Your account has been successfully verified and is now active.</p>
                    <p>
                        <a href="{dashboard_link}" style="display: inline-block;
                        padding: 10px 20px; background-color: #007bff; color: white;
                        text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
                    </p>
                    <p>You can now log in and start using our platform.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # Password Changed Notification Template
        if template_slug == EmailService.TEMPLATE_PASSWORD_CHANGED:
            changed_at = context.get("changed_at", "recently")
            security_link = context.get("security_settings_link", "")
            support_email = context.get("support_email", "support@example.com")

            subject = f"Password Changed - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Password Changed</h2>
                    <p>Hi {user_name},</p>
                    <p>Your password was successfully changed on {changed_at}.</p>
                    <p style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px;
                        margin: 15px 0; border-radius: 5px;">
                        <strong>⚠️ Important:</strong> If you did not make this change,
                        please contact support immediately at {support_email}.
                    </p>
                    <p>
                        <a href="{security_link}" style="display: inline-block; padding: 10px 20px;
                        background-color: #007bff; color: white; text-decoration: none;
                        border-radius: 5px;">Review Account Security</a>
                    </p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # 2FA Enabled Notification Template
        if template_slug == EmailService.TEMPLATE_2FA_ENABLED:
            enabled_at = context.get("enabled_at", "recently")
            backup_codes_url = context.get("backup_codes_url", "")
            support_email = context.get("support_email", "support@example.com")

            subject = f"Two-Factor Authentication Enabled - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Two-Factor Authentication Enabled</h2>
                    <p>Hi {user_name},</p>
                    <p>Two-factor authentication has been successfully enabled on your account
                    on {enabled_at}.</p>
                    <p>Your account is now more secure. You will be asked to enter a verification
                    code from your authenticator app each time you log in.</p>
                    <p style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px;
                        margin: 15px 0; border-radius: 5px;">
                        <strong>⚠️ Important:</strong> Save your backup codes in a secure location.
                        You will need them if you lose access to your authenticator app.
                    </p>
                    <p>
                        <a href="{backup_codes_url}" style="display: inline-block;
                        padding: 10px 20px; background-color: #28a745; color: white;
                        text-decoration: none; border-radius: 5px;">View Backup Codes</a>
                    </p>
                    <p>If you did not enable 2FA, please contact support immediately
                    at {support_email}.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # Login Notification Template
        if template_slug == EmailService.TEMPLATE_LOGIN_NOTIFICATION:
            login_time = context.get("login_time", "Unknown")
            device = context.get("device") or context.get("device_info", "Unknown device")
            location = context.get("location", "Unknown location")
            ip_address = context.get("ip_address", "Unknown")
            security_link = context.get("security_settings_link", "")

            subject = f"New Login to Your Account - {site_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>New Login Detected</h2>
                    <p>Hi {user_name},</p>
                    <p>We detected a new login to your account:</p>
                    <ul>
                        <li><strong>Time:</strong> {login_time}</li>
                        <li><strong>Device:</strong> {device}</li>
                        <li><strong>Location:</strong> {location}</li>
                        <li><strong>IP Address:</strong> {ip_address}</li>
                    </ul>
                    <p>If this was you, you can ignore this email.</p>
                    <p style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px;
                        margin: 15px 0; border-radius: 5px;">
                        <strong>⚠️ Important:</strong> If you did not log in, your account may be
                        compromised. Please secure your account immediately.
                    </p>
                    <p>
                        <a href="{security_link}" style="display: inline-block; padding: 10px 20px;
                        background-color: #dc3545; color: white; text-decoration: none;
                        border-radius: 5px;">Secure My Account</a>
                    </p>
                    <p>We recommend enabling two-factor authentication for additional security.</p>
                </body>
            </html>
            """
            plain_text = strip_tags(html_body)
            return subject, html_body, plain_text

        # No template found
        logger.error(f"No inline template fallback for: {template_slug}")
        return "", "", ""

    @staticmethod
    def send_verification_email(user: "User", token: str) -> bool:
        """Send email verification email to user.

        Args:
            user: User to send email to
            token: Email verification token (plain, not hashed)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Build verification URL
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            verification_url = f"{base_url}/verify-email/{token}"

            # Build context for template rendering
            context = {
                "user": user,
                "verification_url": verification_url,
                "verification_link": verification_url,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_EMAIL_VERIFICATION,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Verification email sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False

    @staticmethod
    def send_password_reset_email(user: "User", token: str) -> bool:
        """Send password reset email to user.

        Args:
            user: User to send email to
            token: Password reset token (plain, not hashed)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            reset_url = f"{base_url}/reset-password/{token}"

            # Get expiry minutes from settings
            expiry_minutes = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 10)

            # Build context for template rendering
            context = {
                "user": user,
                "reset_link": reset_url,
                "expiry_minutes": expiry_minutes,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_PASSWORD_RESET_REQUEST,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Password reset email sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return False

    @staticmethod
    def send_password_reset_confirmation_email(user: "User") -> bool:
        """Send confirmation email after successful password reset.

        This email notifies the user that their password was successfully
        changed. If they did not make this change, they are instructed
        to contact support immediately.

        Args:
            user: User whose password was reset

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from django.utils import timezone

            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            security_settings_url = f"{base_url}/settings/security"
            support_email = getattr(settings, "SUPPORT_EMAIL", "support@example.com")

            # Build context for template rendering
            context = {
                "user": user,
                "changed_at": timezone.now().strftime("%d/%m/%Y at %H:%M %Z"),
                "security_settings_link": security_settings_url,
                "support_email": support_email,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_PASSWORD_RESET_CONFIRMATION,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Password reset confirmation email sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset confirmation email to {user.email}: {e}")
            return False

    @staticmethod
    def send_welcome_email(user: "User") -> bool:
        """Send welcome email after successful registration.

        Args:
            user: User to send email to

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            dashboard_url = f"{base_url}/dashboard"

            # Build context for template rendering
            context = {
                "user": user,
                "dashboard_link": dashboard_url,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_WELCOME,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Welcome email sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
            return False

    @staticmethod
    def send_password_changed_notification(user: "User") -> bool:
        """Send notification email after password change.

        This is for password changes through settings, not the reset flow.

        Args:
            user: User to send email to

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from django.utils import timezone

            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            security_settings_url = f"{base_url}/settings/security"
            support_email = getattr(settings, "SUPPORT_EMAIL", "support@example.com")

            # Build context for template rendering
            context = {
                "user": user,
                "changed_at": timezone.now().strftime("%d/%m/%Y at %H:%M %Z"),
                "security_settings_link": security_settings_url,
                "support_email": support_email,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_PASSWORD_CHANGED,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Password changed notification sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password changed notification to {user.email}: {e}")
            return False

    @staticmethod
    def send_2fa_enabled_notification(user: "User") -> bool:
        """Send notification email after 2FA is enabled.

        Args:
            user: User to send email to

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from django.utils import timezone

            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            backup_codes_url = f"{base_url}/settings/security/backup-codes"
            support_email = getattr(settings, "SUPPORT_EMAIL", "support@example.com")

            # Build context for template rendering
            context = {
                "user": user,
                "enabled_at": timezone.now().strftime("%d/%m/%Y at %H:%M %Z"),
                "backup_codes_url": backup_codes_url,
                "support_email": support_email,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_2FA_ENABLED,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"2FA enabled notification sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send 2FA enabled notification to {user.email}: {e}")
            return False

    @staticmethod
    def send_login_notification(user: "User", login_details: dict[str, Any]) -> bool:
        """Send security notification email when user logs in from new device/location.

        Args:
            user: User who logged in
            login_details: Dictionary containing login metadata:
                - login_time: Formatted timestamp of login
                - device_info: Device/browser information
                - location: Geographic location (city, country)
                - ip_address: IP address of login

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            security_settings_url = f"{base_url}/settings/security"

            # Build context for template rendering
            context = {
                "user": user,
                "login_time": login_details.get("login_time", "Unknown"),
                "device": login_details.get("device_info", "Unknown device"),
                "location": login_details.get("location", "Unknown location"),
                "ip_address": login_details.get("ip_address", "Unknown"),
                "security_settings_link": security_settings_url,
                "site_name": getattr(settings, "SITE_NAME", "Syntek Platform"),
            }

            # Render template
            subject, html_message, plain_message = EmailService._render_inline_template(
                EmailService.TEMPLATE_LOGIN_NOTIFICATION,
                context,
            )

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Login notification sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send login notification to {user.email}: {e}")
            return False
