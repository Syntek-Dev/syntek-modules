"""Migration 0002 for ``syntek-auth`` — US009.

Adds:
- ``email_verified`` and ``phone_verified`` boolean fields to ``User``.
- ``VerificationCode`` table for email/phone OTP and password-reset tokens.
- ``AccessTokenDenylist`` table for short-lived access token invalidation.
"""

from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add verification flags, VerificationCode, and AccessTokenDenylist."""

    dependencies = [
        ("syntek_auth", "0001_initial"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # Add email_verified to User
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="email verified"),
        ),
        # ------------------------------------------------------------------
        # Add phone_verified to User
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name="user",
            name="phone_verified",
            field=models.BooleanField(default=False, verbose_name="phone verified"),
        ),
        # ------------------------------------------------------------------
        # syntek_auth_verification_code
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="VerificationCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code_type",
                    models.CharField(
                        choices=[
                            ("email_verify", "Email verification"),
                            ("phone_verify", "Phone OTP verification"),
                            ("password_reset", "Password reset"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "token",
                    models.CharField(db_index=True, max_length=128, unique=True),
                ),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "attempt_count",
                    models.PositiveSmallIntegerField(default=0),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "syntek_auth_verification_code",
            },
        ),
        migrations.AddIndex(
            model_name="verificationcode",
            index=models.Index(
                fields=["user", "code_type", "expires_at"],
                name="syntek_vc_lookup_idx",
            ),
        ),
        # ------------------------------------------------------------------
        # syntek_auth_access_token_denylist
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="AccessTokenDenylist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "jti",
                    models.CharField(db_index=True, max_length=64, unique=True),
                ),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "syntek_auth_access_token_denylist",
            },
        ),
    ]
