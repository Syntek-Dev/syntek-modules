"""Migration 0004 for ``syntek-auth`` — add PendingOAuthSession table.

Creates the ``syntek_auth_pending_oauth_session`` table used to store
short-lived pending sessions for MFA-gated OAuth providers.  Rows are
created at the OAuth callback and consumed once the user completes a
local MFA challenge.

The ``expires_at`` index enables efficient background pruning of expired rows.
"""

from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add PendingOAuthSession table for MFA-gated OAuth flow."""

    dependencies = [
        ("syntek_auth", "0003_user_encrypted_unique_tokens"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PendingOAuthSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=__import__("uuid").uuid4,
                        editable=False,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pending_oauth_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "provider",
                    models.CharField(max_length=100),
                ),
                (
                    "expires_at",
                    models.DateTimeField(),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
            ],
            options={
                "db_table": "syntek_auth_pending_oauth_session",
            },
        ),
        migrations.AddIndex(
            model_name="pendingoauthsession",
            index=models.Index(
                fields=["expires_at"],
                name="syntek_pending_oauth_exp_idx",
            ),
        ),
    ]
