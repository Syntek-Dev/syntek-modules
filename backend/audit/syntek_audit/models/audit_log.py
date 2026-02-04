"""AuditLog model for security event tracking."""

import uuid

from django.db import models


class AuditLog(models.Model):
    """Audit log for tracking security-relevant user actions."""

    class ActionType(models.TextChoices):
        """Choices for audit log action types."""

        LOGIN = "LOGIN", "Login"  # type: ignore[assignment]
        LOGOUT = "LOGOUT", "Logout"  # type: ignore[assignment]
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"  # type: ignore[assignment]
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"  # type: ignore[assignment]
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"  # type: ignore[assignment]
        EMAIL_VERIFIED = "EMAIL_VERIFIED", "Email Verified"  # type: ignore[assignment]
        TWO_FACTOR_ENABLED = "TWO_FACTOR_ENABLED", "Two Factor Enabled"  # type: ignore[assignment]
        TWO_FACTOR_DISABLED = "TWO_FACTOR_DISABLED", "Two Factor Disabled"  # type: ignore[assignment]
        ACCOUNT_LOCKED = "ACCOUNT_LOCKED", "Account Locked"  # type: ignore[assignment]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    organisation = models.ForeignKey(
        "syntek_authentication.Organisation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=ActionType.choices)
    ip_address = models.BinaryField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    device_fingerprint = models.CharField(max_length=64, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["organisation", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return audit log description."""
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"{self.action} by {user_email} at {self.created_at}"
