"""Migration 0005 for ``syntek-auth`` — encrypt provider on PendingOAuthSession.

Changes
-------
1. Add ``provider_token`` column (nullable initially) to
   ``syntek_auth_pending_oauth_session``.

2. Run a data-migration step to encrypt any existing ``provider`` plaintext
   values and compute their HMAC-SHA256 ``provider_token`` values.
   On a fresh install (empty table) this is a no-op.

3. Alter ``provider`` from ``CharField(max_length=100)`` to ``EncryptedField``
   (a ``TextField`` subclass) so values are stored as AES-256-GCM ciphertext.

4. Tighten ``provider_token`` to ``NOT NULL`` with a ``db_index``.

Prerequisites
-------------
``SYNTEK_AUTH['FIELD_KEY']`` and ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` must be set
in Django settings before running this migration on a database with existing
``PendingOAuthSession`` rows.  On an empty table these keys are not required for
the migration itself but must be present for subsequent row creation.
"""

from __future__ import annotations

from django.db import migrations, models

import syntek_auth.models.user

# ---------------------------------------------------------------------------
# Data migration helpers
# ---------------------------------------------------------------------------


def _encrypt_existing_providers(apps, _schema_editor):  # type: ignore[type-arg]
    """Encrypt any existing plaintext provider values and populate provider_token.

    Reads ``SYNTEK_AUTH['FIELD_KEY']`` and ``SYNTEK_AUTH['FIELD_HMAC_KEY']``
    from settings.  Raises ``ImproperlyConfigured`` when rows exist but keys
    are missing.  On an empty table this is a no-op.
    """
    import hashlib
    import hmac as _hmac

    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    PendingOAuthSession = apps.get_model("syntek_auth", "PendingOAuthSession")

    rows = list(PendingOAuthSession.objects.all())
    if not rows:
        return

    cfg = getattr(settings, "SYNTEK_AUTH", {})
    hmac_key_raw = cfg.get("FIELD_HMAC_KEY")
    field_key_raw = cfg.get("FIELD_KEY")

    if not hmac_key_raw or not field_key_raw:
        raise ImproperlyConfigured(
            "SYNTEK_AUTH['FIELD_KEY'] and SYNTEK_AUTH['FIELD_HMAC_KEY'] must be "
            "configured before running syntek_auth migration 0005 on a database "
            "with existing PendingOAuthSession rows."
        )

    hmac_key: bytes = (
        hmac_key_raw.encode("utf-8")
        if isinstance(hmac_key_raw, str)
        else bytes(hmac_key_raw)
    )
    field_key: bytes = (
        field_key_raw.encode("utf-8")
        if isinstance(field_key_raw, str)
        else bytes(field_key_raw)
    )

    from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

    def _token(value: str) -> str:
        return _hmac.new(hmac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    for row in rows:
        normalised = (row.provider or "").strip().lower()
        row.provider = encrypt_field(normalised, field_key)
        row.provider_token = _token(normalised)

    PendingOAuthSession.objects.bulk_update(rows, ["provider", "provider_token"])


def _clear_encrypted_providers(apps, _schema_editor):  # type: ignore[type-arg]
    """Reverse: clear provider_token so the reverse AlterField can proceed."""
    PendingOAuthSession = apps.get_model("syntek_auth", "PendingOAuthSession")
    PendingOAuthSession.objects.update(provider_token=None)


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


class Migration(migrations.Migration):
    """Encrypt provider field and add provider_token on PendingOAuthSession."""

    dependencies = [
        ("syntek_auth", "0004_pending_oauth_session"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # Step 1 — add provider_token as nullable (no index yet)
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name="pendingoauthsession",
            name="provider_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="provider lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised provider identifier.  "
                    "Use this column for filtering — never filter on the ciphertext."
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Step 2 — encrypt existing provider values + compute tokens
        # ------------------------------------------------------------------
        migrations.RunPython(
            _encrypt_existing_providers,
            reverse_code=_clear_encrypted_providers,
        ),
        # ------------------------------------------------------------------
        # Step 3 — change provider from CharField to EncryptedField
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="pendingoauthsession",
            name="provider",
            field=syntek_auth.models.user.EncryptedField(
                verbose_name="provider",
                help_text="AES-256-GCM ciphertext of the OAuth provider identifier.",
            ),
        ),
        # ------------------------------------------------------------------
        # Step 4 — tighten provider_token: NOT NULL + db_index
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="pendingoauthsession",
            name="provider_token",
            field=models.CharField(
                max_length=64,
                db_index=True,
                verbose_name="provider lookup token",
                help_text=(
                    "HMAC-SHA256 of the normalised provider identifier.  "
                    "Use this column for filtering — never filter on the ciphertext."
                ),
            ),
        ),
    ]
