"""Migration 0006 for ``syntek-auth`` — encrypt token and JTI fields.

Changes
-------
``VerificationCode``:
1. Add ``token_token`` column (nullable initially).
2. Encrypt existing ``token`` values and backfill ``token_token``.
3. Alter ``token`` from ``CharField`` to ``EncryptedField``.
4. Tighten ``token_token`` to NOT NULL + UNIQUE + db_index.

``AccessTokenDenylist``:
5. Add ``jti_token`` column (nullable initially).
6. Encrypt existing ``jti`` values and backfill ``jti_token``.
7. Alter ``jti`` from ``CharField`` to ``EncryptedField``.
8. Tighten ``jti_token`` to NOT NULL + UNIQUE + db_index.

``RefreshToken``:
9.  Add ``jti_token`` column (nullable initially).
10. Encrypt existing ``jti`` values and backfill ``jti_token``.
11. Alter ``jti`` from ``CharField`` to ``EncryptedField``.
12. Tighten ``jti_token`` to NOT NULL + UNIQUE + db_index.

``BackupCode``:
13. Alter ``code_hash`` from ``CharField`` to ``EncryptedField``.
    Existing rows are encrypted in the same data-migration step.

Prerequisites
-------------
``SYNTEK_AUTH['FIELD_KEY']`` and ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` must be
set in Django settings before running this migration on a database with
existing rows.  On all-empty tables these keys are not strictly required for
the migration itself but must be present for subsequent row creation.
"""

from __future__ import annotations

from django.db import migrations, models

import syntek_auth.models.user

# ---------------------------------------------------------------------------
# Data migration helpers
# ---------------------------------------------------------------------------


def _get_keys(settings):  # type: ignore[type-arg]
    """Return (field_key_bytes, hmac_key_bytes) from SYNTEK_AUTH settings."""

    from django.core.exceptions import ImproperlyConfigured

    cfg = getattr(settings, "SYNTEK_AUTH", {})
    field_key_raw = cfg.get("FIELD_KEY")
    hmac_key_raw = cfg.get("FIELD_HMAC_KEY")
    if not field_key_raw or not hmac_key_raw:
        raise ImproperlyConfigured(
            "SYNTEK_AUTH['FIELD_KEY'] and SYNTEK_AUTH['FIELD_HMAC_KEY'] must be "
            "configured before running syntek_auth migration 0006 on a database "
            "with existing rows."
        )
    field_key: bytes = (
        field_key_raw.encode("utf-8")
        if isinstance(field_key_raw, str)
        else bytes(field_key_raw)
    )
    hmac_key: bytes = (
        hmac_key_raw.encode("utf-8")
        if isinstance(hmac_key_raw, str)
        else bytes(hmac_key_raw)
    )
    return field_key, hmac_key


def _make_hmac(hmac_key: bytes, value: str) -> str:
    import hashlib
    import hmac as _hmac

    return _hmac.new(hmac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def _encrypt_verification_codes(apps, _schema_editor):  # type: ignore[type-arg]
    from django.conf import settings

    VC = apps.get_model("syntek_auth", "VerificationCode")
    rows = list(VC.objects.all())
    if not rows:
        return
    field_key, hmac_key = _get_keys(settings)
    from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

    for row in rows:
        plaintext = (row.token or "").strip()
        row.token = encrypt_field(plaintext, field_key, "VerificationCode", "token")
        row.token_token = _make_hmac(hmac_key, plaintext)
    VC.objects.bulk_update(rows, ["token", "token_token"])


def _clear_verification_tokens(apps, _schema_editor):  # type: ignore[type-arg]
    VC = apps.get_model("syntek_auth", "VerificationCode")
    VC.objects.update(token_token=None)


def _encrypt_denylist_jtis(apps, _schema_editor):  # type: ignore[type-arg]
    from django.conf import settings

    ATD = apps.get_model("syntek_auth", "AccessTokenDenylist")
    rows = list(ATD.objects.all())
    if not rows:
        return
    field_key, hmac_key = _get_keys(settings)
    from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

    for row in rows:
        plaintext = (row.jti or "").strip()
        row.jti = encrypt_field(plaintext, field_key, "AccessTokenDenylist", "jti")
        row.jti_token = _make_hmac(hmac_key, plaintext)
    ATD.objects.bulk_update(rows, ["jti", "jti_token"])


def _clear_denylist_jti_tokens(apps, _schema_editor):  # type: ignore[type-arg]
    ATD = apps.get_model("syntek_auth", "AccessTokenDenylist")
    ATD.objects.update(jti_token=None)


def _encrypt_refresh_jtis(apps, _schema_editor):  # type: ignore[type-arg]
    from django.conf import settings

    RT = apps.get_model("syntek_auth", "RefreshToken")
    rows = list(RT.objects.all())
    if not rows:
        return
    field_key, hmac_key = _get_keys(settings)
    from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

    for row in rows:
        plaintext = (row.jti or "").strip()
        row.jti = encrypt_field(plaintext, field_key, "RefreshToken", "jti")
        row.jti_token = _make_hmac(hmac_key, plaintext)
    RT.objects.bulk_update(rows, ["jti", "jti_token"])


def _clear_refresh_jti_tokens(apps, _schema_editor):  # type: ignore[type-arg]
    RT = apps.get_model("syntek_auth", "RefreshToken")
    RT.objects.update(jti_token=None)


def _encrypt_backup_code_hashes(apps, _schema_editor):  # type: ignore[type-arg]
    from django.conf import settings

    BC = apps.get_model("syntek_auth", "BackupCode")
    rows = list(BC.objects.all())
    if not rows:
        return
    field_key, _ = _get_keys(settings)
    from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

    for row in rows:
        plaintext_hash = (row.code_hash or "").strip()
        row.code_hash = encrypt_field(
            plaintext_hash, field_key, "BackupCode", "code_hash"
        )
    BC.objects.bulk_update(rows, ["code_hash"])


def _decrypt_backup_code_hashes(apps, _schema_editor):  # type: ignore[type-arg]
    from django.conf import settings

    BC = apps.get_model("syntek_auth", "BackupCode")
    rows = list(BC.objects.all())
    if not rows:
        return
    field_key, _ = _get_keys(settings)
    from syntek_pyo3 import decrypt_field  # type: ignore[import-not-found]

    for row in rows:
        row.code_hash = decrypt_field(
            row.code_hash, field_key, "BackupCode", "code_hash"
        )
    BC.objects.bulk_update(rows, ["code_hash"])


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


class Migration(migrations.Migration):
    """Encrypt token/JTI fields and add HMAC lookup token columns."""

    dependencies = [
        ("syntek_auth", "0005_pending_oauth_session_encrypt_provider"),
    ]

    operations = [
        # ==================================================================
        # VerificationCode.token → EncryptedField + token_token
        # ==================================================================
        migrations.AddField(
            model_name="verificationcode",
            name="token_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="token lookup token",
                help_text="HMAC-SHA256 of the plaintext token.",
            ),
        ),
        migrations.RunPython(
            _encrypt_verification_codes,
            reverse_code=_clear_verification_tokens,
        ),
        migrations.AlterField(
            model_name="verificationcode",
            name="token",
            field=syntek_auth.models.user.EncryptedField(
                verbose_name="token",
                help_text="AES-256-GCM ciphertext of the plaintext verification token.",
            ),
        ),
        migrations.AlterField(
            model_name="verificationcode",
            name="token_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                verbose_name="token lookup token",
                help_text="HMAC-SHA256 of the plaintext token.",
            ),
        ),
        # ==================================================================
        # AccessTokenDenylist.jti → EncryptedField + jti_token
        # ==================================================================
        migrations.AddField(
            model_name="accesstokendenylist",
            name="jti_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="JTI lookup token",
                help_text="HMAC-SHA256 of the plaintext JTI.",
            ),
        ),
        migrations.RunPython(
            _encrypt_denylist_jtis,
            reverse_code=_clear_denylist_jti_tokens,
        ),
        migrations.AlterField(
            model_name="accesstokendenylist",
            name="jti",
            field=syntek_auth.models.user.EncryptedField(
                verbose_name="JTI",
                help_text="AES-256-GCM ciphertext of the JWT Token ID.",
            ),
        ),
        migrations.AlterField(
            model_name="accesstokendenylist",
            name="jti_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                verbose_name="JTI lookup token",
                help_text="HMAC-SHA256 of the plaintext JTI.",
            ),
        ),
        # ==================================================================
        # RefreshToken.jti → EncryptedField + jti_token
        # ==================================================================
        migrations.AddField(
            model_name="refreshtoken",
            name="jti_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=64,
                verbose_name="JTI lookup token",
                help_text="HMAC-SHA256 of the plaintext JTI.",
            ),
        ),
        migrations.RunPython(
            _encrypt_refresh_jtis,
            reverse_code=_clear_refresh_jti_tokens,
        ),
        migrations.AlterField(
            model_name="refreshtoken",
            name="jti",
            field=syntek_auth.models.user.EncryptedField(
                verbose_name="JTI",
                help_text="AES-256-GCM ciphertext of the JWT Token ID.",
            ),
        ),
        migrations.AlterField(
            model_name="refreshtoken",
            name="jti_token",
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                verbose_name="JTI lookup token",
                help_text="HMAC-SHA256 of the plaintext JTI.",
            ),
        ),
        # ==================================================================
        # BackupCode.code_hash → EncryptedField
        # ==================================================================
        migrations.RunPython(
            _encrypt_backup_code_hashes,
            reverse_code=_decrypt_backup_code_hashes,
        ),
        migrations.AlterField(
            model_name="backupcode",
            name="code_hash",
            field=syntek_auth.models.user.EncryptedField(
                verbose_name="code hash",
                help_text="AES-256-GCM ciphertext of the Argon2id hash of the backup code.",
            ),
        ),
    ]
