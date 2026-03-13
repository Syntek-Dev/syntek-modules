"""Initial migration for ``syntek-auth`` — US009.

Creates three tables:
- ``syntek_auth_user`` — concrete user model with EncryptedField PII columns.
- ``syntek_auth_refresh_token`` — persisted refresh token records keyed by JTI.
- ``syntek_auth_backup_code`` — single-use MFA backup codes stored as hashes.

``EncryptedField`` is a ``TextField`` subclass so Django writes it as a TEXT
column.  The field class reference is preserved in the migration so that
future ``makemigrations`` runs detect when the field type changes (e.g. when
syntek-pyo3 replaces the placeholder).

Dependencies on ``auth`` migration ``0012`` are required for the
``PermissionsMixin`` M2M relations (``groups`` and ``user_permissions``) to
reference the correct ``auth.Group`` and ``auth.Permission`` tables.
"""

from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import syntek_auth.models.user


class Migration(migrations.Migration):
    """Create the initial syntek_auth schema."""

    initial = True

    dependencies = [
        # PermissionsMixin M2M tables reference auth.Group and auth.Permission.
        ("auth", "0012_alter_user_first_name_max_length"),
        # contenttypes is required by auth's permission framework.
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # syntek_auth_user
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="User",
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
                # AbstractBaseUser fields
                (
                    "password",
                    models.CharField(max_length=128, verbose_name="password"),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                # PermissionsMixin field
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user has all permissions "
                            "without explicitly assigning them."
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                # AbstractSyntekUser PII fields (EncryptedField = TextField subclass)
                (
                    "email",
                    syntek_auth.models.user.EncryptedField(
                        db_index=True,
                        unique=True,
                        verbose_name="email address",
                    ),
                ),
                (
                    "phone",
                    syntek_auth.models.user.EncryptedField(
                        blank=True,
                        null=True,
                        verbose_name="phone number",
                    ),
                ),
                # AbstractSyntekUser optional username
                (
                    "username",
                    models.CharField(
                        blank=True,
                        max_length=150,
                        null=True,
                        unique=True,
                        verbose_name="username",
                    ),
                ),
                # AbstractSyntekUser status flags
                (
                    "is_staff",
                    models.BooleanField(default=False),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True),
                ),
            ],
            options={
                "swappable": "AUTH_USER_MODEL",
            },
        ),
        # M2M: User <-> auth.Group (from PermissionsMixin)
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "The groups this user belongs to. A user will get all "
                    "permissions granted to each of their groups."
                ),
                related_name="user_set",
                related_query_name="user",
                to="auth.group",
                verbose_name="groups",
            ),
        ),
        # M2M: User <-> auth.Permission (from PermissionsMixin)
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific permissions for this user.",
                related_name="user_set",
                related_query_name="user",
                to="auth.permission",
                verbose_name="user permissions",
            ),
        ),
        # ------------------------------------------------------------------
        # syntek_auth_refresh_token
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="RefreshToken",
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
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "expires_at",
                    models.DateTimeField(),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "syntek_auth_refresh_token",
            },
        ),
        # ------------------------------------------------------------------
        # syntek_auth_backup_code
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="BackupCode",
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
                    "code_hash",
                    models.CharField(max_length=256),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="backup_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "syntek_auth_backup_code",
            },
        ),
    ]
