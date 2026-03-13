"""Migration 0003 for ``syntek-auth`` — encrypted-field lookup tokens.

Changes
-------
1. Add ``email_token``, ``phone_token``, and ``username_token`` columns to the
   ``User`` table.  All three are initially nullable so existing rows can be
   backfilled before the unique constraint is applied.

2. Run a Python data-migration step to compute HMAC-SHA256 tokens for any
   existing rows.  ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` must be configured before
   running this migration.

3. Tighten ``email_token`` to ``NOT NULL UNIQUE`` after backfill.

4. Apply ``UNIQUE`` to ``phone_token`` and ``username_token`` (both remain
   nullable — NULL values do not violate UNIQUE in PostgreSQL or SQLite).

5. Remove the now-redundant ``UNIQUE`` + ``db_index`` constraints from the
   ``email`` EncryptedField column.

6. Change the ``username`` field from ``CharField(max_length=150, unique=True)``
   to ``EncryptedField`` (a ``TextField`` subclass) so that username values are
   encrypted at rest.  The uniqueness invariant is transferred to
   ``username_token``.

Prerequisites
-------------
``SYNTEK_AUTH['FIELD_HMAC_KEY']`` must be set in Django settings before
running this migration on a database with existing rows.  On an empty database
(fresh installation) the data-migration step is a no-op and the key is not
strictly required for the migration itself, but should be set for subsequent
user creation to work.

Reversibility
-------------
The reverse migration restores the ``email`` unique/index constraints,
converts ``username`` back to ``CharField(max_length=150, unique=True)``, and
removes the token columns.  Reversing on a database where any username value
exceeds 150 characters will fail at the DB level.
"""

from __future__ import annotations

from django.conf import settings
from django.db import migrations, models

import syntek_auth.models.user

# ---------------------------------------------------------------------------
# Data migration helpers
# ---------------------------------------------------------------------------


def _populate_tokens(apps, _schema_editor):  # type: ignore[type-arg]
    """Compute HMAC-SHA256 tokens for all existing User rows.

    Reads ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` from settings.  If the key is not
    set and there are existing rows, raises ``ImproperlyConfigured`` with a
    descriptive message.  On an empty table the function is a no-op.
    """
    import hashlib
    import hmac as _hmac

    from django.core.exceptions import ImproperlyConfigured

    User = apps.get_model("syntek_auth", "User")

    if not User.objects.exists():
        return

    cfg = getattr(settings, "SYNTEK_AUTH", {})
    key_raw = cfg.get("FIELD_HMAC_KEY")
    if not key_raw:
        raise ImproperlyConfigured(
            "SYNTEK_AUTH['FIELD_HMAC_KEY'] must be configured before running "
            "syntek_auth migration 0003 on a database with existing User rows.  "
            "Set it to a cryptographically random value of at least 32 bytes "
            "read from an environment variable."
        )
    key: bytes = key_raw.encode("utf-8") if isinstance(key_raw, str) else bytes(key_raw)

    def token(value: str) -> str:
        return _hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    users = list(User.objects.all())
    for user in users:
        user.email_token = token(user.email.strip().lower()) if user.email else ""
        if user.phone:
            user.phone_token = token(user.phone.strip())
        if user.username:
            user.username_token = token(user.username.strip().lower())

    User.objects.bulk_update(users, ["email_token", "phone_token", "username_token"])


def _clear_tokens(apps, _schema_editor):  # type: ignore[type-arg]
    """Reverse: clear token columns so the reverse AlterField ops can proceed."""
    User = apps.get_model("syntek_auth", "User")
    User.objects.update(email_token=None, phone_token=None, username_token=None)


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


class Migration(migrations.Migration):
    """Add HMAC lookup tokens and tighten encrypted-field uniqueness."""

    dependencies = [
        ("syntek_auth", "0002_user_verification_flags_verification_code_denylist"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # Step 1 — add token columns as nullable (no unique yet)
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name="user",
            name="email_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="email lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised email address.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="phone_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="phone lookup token",
                help_text=(
                    "HMAC-SHA256 of the phone number.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="username_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="username lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised username.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Step 2 — backfill tokens for existing rows
        # ------------------------------------------------------------------
        migrations.RunPython(
            _populate_tokens,
            reverse_code=_clear_tokens,
        ),
        # ------------------------------------------------------------------
        # Step 3 — tighten email_token: NOT NULL + UNIQUE + db_index
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="user",
            name="email_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                verbose_name="email lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised email address.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Step 4 — apply UNIQUE to phone_token and username_token (nullable)
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="user",
            name="phone_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                null=True,
                blank=True,
                db_index=True,
                verbose_name="phone lookup token",
                help_text=(
                    "HMAC-SHA256 of the phone number.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="username_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                null=True,
                blank=True,
                verbose_name="username lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised username.  "
                    "Holds the uniqueness constraint in place of the ciphertext."
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Step 5 — remove the now-meaningless UNIQUE + db_index from email
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="user",
            name="email",
            field=syntek_auth.models.user.EncryptedField(
                blank=False,
                null=False,
                verbose_name="email address",
            ),
        ),
        # ------------------------------------------------------------------
        # Step 6 — change username from CharField(unique) to EncryptedField
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="user",
            name="username",
            field=syntek_auth.models.user.EncryptedField(
                blank=True,
                null=True,
                verbose_name="username",
            ),
        ),
    ]
