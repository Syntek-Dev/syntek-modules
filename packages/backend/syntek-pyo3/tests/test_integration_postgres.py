"""M1 — PostgreSQL integration tests for EncryptedField.

Verifies the full write/read cycle for EncryptedField against a real
PostgreSQL 18.3 container via testcontainers-python.

Key assertions:
- pre_save() rejects plaintext with ValidationError — nothing bad reaches the DB.
- A value returned by pre_save() and written to the DB is the ciphertext.
- The DB column never contains plaintext after an ORM-style save.
- from_db_value() is a passthrough — it returns whatever is in the column.
- A nullable EncryptedField(null=True) saves NULL without raising.
- encrypt_fields_batch / decrypt_fields_batch round-trip correctly with a real DB.

Run explicitly (not collected by default because the postgres mark is excluded
from the standard CI run):
    pytest packages/backend/syntek-pyo3/tests/test_integration_postgres.py -v -m integration
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

# TEST KEY ONLY — NOT FOR PRODUCTION USE.  Generate from a CSPRNG in production.
_TEST_KEY = bytes(range(32))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def postgres_dsn():
    """Spin up a real PostgreSQL 18.3-alpine container and yield DSN parameters."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:18.3-alpine") as pg:
        yield {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": pg.dbname,
            "USER": pg.username,
            "PASSWORD": pg.password,
            "HOST": pg.get_container_host_ip(),
            "PORT": pg.get_exposed_port(5432),
        }


@pytest.fixture(scope="module")
def pg_connection(postgres_dsn, django_db_blocker):
    """Reconfigure Django's default DB to point at the test container.

    Uses `django_db_blocker.unblock()` to bypass pytest-django's database
    access guard for the lifetime of this module-scoped fixture.  This is the
    correct pattern when bringing your own database (testcontainers) rather
    than letting pytest-django create a test database.
    """
    from django.conf import settings as django_settings
    from django.db import connection, connections

    django_settings.DATABASES["default"].update(postgres_dsn)
    connections["default"].close()

    with django_db_blocker.unblock():
        # Verify the connection is usable before any test runs.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

        yield

    connections["default"].close()


@pytest.fixture(scope="module")
def encrypted_table(pg_connection):
    """Create a minimal table for EncryptedField round-trip tests.

    Uses a raw SQL CREATE rather than migrations so that this test file has no
    dependency on Django's app registry or migration framework.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS syntek_test_encrypted (
                id      BIGSERIAL PRIMARY KEY,
                email   TEXT,
                phone   TEXT
            )
            """
        )

    yield

    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS syntek_test_encrypted")


# ---------------------------------------------------------------------------
# Helpers
#
# Each helper opens its own cursor context.  Using separate `with
# connection.cursor()` blocks for writes and reads ensures that psycopg3's
# internal cursor state never interferes between INSERT and SELECT — each
# block gets a clean cursor, and the statement auto-commits (Django connects
# in autocommit=True mode by default) before the next block runs.
# ---------------------------------------------------------------------------


def _make_ciphertext(
    plaintext: str,
    model: str = "User",
    field: str = "email",
    version: int = 1,
) -> str:
    """Produce a real versioned ciphertext using the PyO3 API."""
    from syntek_pyo3 import KeyRing, encrypt_field

    ring = KeyRing()
    ring.add(version, _TEST_KEY)
    return encrypt_field(plaintext, ring, model, field)


def _write_email(value) -> None:
    """Insert one row with the given email value (may be None for NULL)."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO syntek_test_encrypted (email) VALUES (%s)", [value])


def _write_row(email=None, phone=None) -> None:
    """Insert one row with email and phone columns."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO syntek_test_encrypted (email, phone) VALUES (%s, %s)",
            [email, phone],
        )


def _read_latest_email() -> str | None:
    """Read the email from the most recently inserted row."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email FROM syntek_test_encrypted ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None


def _read_latest_row() -> tuple | None:
    """Read (email, phone) from the most recently inserted row."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email, phone FROM syntek_test_encrypted ORDER BY id DESC LIMIT 1"
        )
        return cursor.fetchone()


def _count_email(value: str) -> int:
    """Count rows where email exactly equals the given value."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM syntek_test_encrypted WHERE email = %s", [value]
        )
        return cursor.fetchone()[0]


# ---------------------------------------------------------------------------
# pre_save → DB write: only ciphertext is stored
# ---------------------------------------------------------------------------


class TestPreSaveToDatabase:
    @pytest.mark.usefixtures("encrypted_table")
    def test_ciphertext_is_what_gets_stored(self) -> None:
        """The value returned by pre_save equals what ends up in the DB column."""
        from unittest.mock import MagicMock

        from syntek_pyo3 import EncryptedField

        ct = _make_ciphertext("hello@example.com")

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = ct
        stored_value = field.pre_save(instance, add=False)

        # Write what pre_save returned to the DB.
        _write_email(stored_value)

        # Read back in a fresh cursor and verify.
        db_value = _read_latest_email()
        assert db_value is not None
        assert db_value == ct, "DB must contain the ciphertext, not plaintext"
        assert "hello@example.com" not in db_value, (
            "Plaintext must not appear in the stored column value"
        )

    @pytest.mark.usefixtures("encrypted_table")
    def test_plaintext_never_reaches_database(self) -> None:
        """pre_save raises ValidationError — plaintext is never inserted."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = "never-reaches-db@example.com"

        with pytest.raises(ValidationError):
            field.pre_save(instance, add=False)

        assert _count_email("never-reaches-db@example.com") == 0, (
            "Plaintext must never appear in the database"
        )

    @pytest.mark.usefixtures("encrypted_table")
    def test_nullable_field_stores_null(self) -> None:
        """EncryptedField(null=True) saves NULL to the DB column without error."""
        from unittest.mock import MagicMock

        from syntek_pyo3 import EncryptedField

        field = EncryptedField(null=True, blank=True)
        field.attname = "email"
        instance = MagicMock()
        instance.email = None

        stored_value = field.pre_save(instance, add=False)
        assert stored_value is None

        _write_email(stored_value)

        db_value = _read_latest_email()
        assert db_value is None

    @pytest.mark.usefixtures("encrypted_table")
    def test_non_nullable_field_raises_for_none_value(self) -> None:
        """EncryptedField() raises ValidationError for None — not TypeError."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        field.attname = "email"
        instance = MagicMock()
        instance.email = None

        with pytest.raises(ValidationError):
            field.pre_save(instance, add=False)


# ---------------------------------------------------------------------------
# from_db_value round-trip
# ---------------------------------------------------------------------------


class TestFromDbValueRoundTrip:
    @pytest.mark.usefixtures("encrypted_table")
    def test_ciphertext_survives_db_round_trip(self) -> None:
        """Ciphertext written to the DB comes back unchanged via from_db_value."""
        from syntek_pyo3 import EncryptedField

        ct = _make_ciphertext("secret@domain.com")
        _write_email(ct)

        raw = _read_latest_email()
        field = EncryptedField()
        result = field.from_db_value(raw, expression=None, connection=None)
        assert result == ct

    @pytest.mark.usefixtures("encrypted_table")
    def test_null_db_value_returns_none(self) -> None:
        """NULL from the database comes back as None from from_db_value."""
        from syntek_pyo3 import EncryptedField

        _write_email(None)

        raw = _read_latest_email()
        assert raw is None  # sanity: DB stored NULL

        field = EncryptedField()
        result = field.from_db_value(raw, expression=None, connection=None)
        assert result is None

    @pytest.mark.usefixtures("encrypted_table")
    def test_legacy_plaintext_passes_through_from_db_value(self) -> None:
        """A value written directly (bypassing the ORM) returns as-is from from_db_value.

        from_db_value is a passthrough by design — decryption is the GraphQL
        middleware's responsibility.  This test documents the documented behaviour.
        """
        from syntek_pyo3 import EncryptedField

        # Directly insert a non-ciphertext value (simulating a pre-migration row).
        _write_email("legacy-plaintext-value")

        raw = _read_latest_email()
        field = EncryptedField()
        result = field.from_db_value(raw, expression=None, connection=None)
        assert result == "legacy-plaintext-value"


# ---------------------------------------------------------------------------
# full_clean → pre_save integration
# ---------------------------------------------------------------------------


class TestFullCleanIntegration:
    @pytest.mark.usefixtures("encrypted_table")
    def test_full_clean_with_valid_ciphertext_does_not_raise(self) -> None:
        """EncryptedField.validate (called by full_clean) accepts valid ciphertext."""
        from syntek_pyo3 import EncryptedField

        ct = _make_ciphertext("user@example.com")
        field = EncryptedField()
        field.validate(ct, model_instance=None)

    @pytest.mark.usefixtures("encrypted_table")
    def test_full_clean_with_plaintext_raises_validation_error(self) -> None:
        """EncryptedField.validate raises ValidationError for plaintext."""
        from django.core.exceptions import ValidationError
        from syntek_pyo3 import EncryptedField

        field = EncryptedField()
        with pytest.raises(ValidationError):
            field.validate("plaintext-value", model_instance=None)


# ---------------------------------------------------------------------------
# Batch round-trip with real DB writes
# ---------------------------------------------------------------------------


class TestBatchRoundTrip:
    @pytest.mark.usefixtures("encrypted_table")
    def test_batch_encrypt_write_read_decrypt(self) -> None:
        """encrypt_fields_batch / decrypt_fields_batch round-trip through the DB."""
        from syntek_pyo3 import KeyRing, decrypt_fields_batch, encrypt_fields_batch

        ring = KeyRing()
        ring.add(1, _TEST_KEY)

        fields = [
            ("email", "batch-user@example.com"),
            ("phone", "+441234567890"),
        ]
        encrypted = encrypt_fields_batch(fields, ring, "User")
        assert len(encrypted) == 2

        # Confirm encrypted values do not expose plaintext.
        for ct in encrypted:
            assert "example.com" not in ct
            assert "+441234567890" not in ct

        # Write to DB.
        _write_row(email=encrypted[0], phone=encrypted[1])

        # Read back in a fresh cursor.
        row = _read_latest_row()
        assert row is not None
        db_email, db_phone = row

        # Decrypt what came back from the DB.
        decrypted = decrypt_fields_batch(
            [("email", db_email), ("phone", db_phone)], ring, "User"
        )
        assert decrypted[0] == "batch-user@example.com"
        assert decrypted[1] == "+441234567890"

    @pytest.mark.usefixtures("encrypted_table")
    def test_batch_decrypt_wrong_aad_raises_batch_decryption_error(self) -> None:
        """Batch decryption with wrong model name fails with BatchDecryptionError."""
        from syntek_pyo3 import (
            BatchDecryptionError,
            KeyRing,
            decrypt_fields_batch,
            encrypt_field,
        )

        ring = KeyRing()
        ring.add(1, _TEST_KEY)

        ct = encrypt_field("secret", ring, "User", "email")
        _write_email(ct)

        db_value = _read_latest_email()
        assert db_value is not None

        with pytest.raises(BatchDecryptionError):
            # Wrong model name → AAD mismatch → GCM tag failure
            decrypt_fields_batch([("email", db_value)], ring, "WrongModel")
