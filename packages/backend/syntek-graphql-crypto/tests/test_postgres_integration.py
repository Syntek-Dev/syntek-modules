"""US008 — PostgreSQL integration tests for ``syntek-graphql-crypto``.

Runs the same write→DB→read round-trip tests as ``test_integration.py`` but
against a real ``postgres:18.3-alpine`` container via ``testcontainers-python``.

Skipped automatically when either ``syntek_pyo3`` is not built or
``testcontainers`` is not installed.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_integration_postgres.py \
        -v -m integration

AC coverage:
    AC1  — individual @encrypted field round-trip against PostgreSQL
    AC2  — batch @encrypted(batch:) round-trip against PostgreSQL
    M4   — verifies middleware works with PostgreSQL (not just SQLite)
"""

from __future__ import annotations

import typing
from unittest.mock import MagicMock

import pytest
import strawberry
from django.db import connection, models

syntek_pyo3 = pytest.importorskip(
    "syntek_pyo3",
    reason="syntek_pyo3 native extension not built — run: maturin build -p syntek-pyo3",
)
tc = pytest.importorskip(
    "testcontainers.postgres",
    reason="testcontainers[postgres] not installed — run: uv pip install testcontainers[postgres]",
)

from syntek_graphql_crypto.directives import Encrypted  # noqa: E402
from syntek_graphql_crypto.middleware import EncryptionMiddleware  # noqa: E402

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Test-only Django model
# ---------------------------------------------------------------------------


class PgCryptoUser(models.Model):
    """Minimal user model for PostgreSQL crypto round-trip tests."""

    email = models.TextField(default="")
    first_name = models.TextField(default="")
    last_name = models.TextField(default="")
    display_name = models.TextField(default="")

    class Meta:
        app_label = "syntek_graphql_crypto"

    def __str__(self) -> str:
        return f"PgCryptoUser({self.pk})"


# ---------------------------------------------------------------------------
# Strawberry schema
# ---------------------------------------------------------------------------


@strawberry.type
class PgCryptoUserOut:
    """Output type — field values are DB ciphertexts; middleware decrypts."""

    user_id: int
    display_name: str
    email: str | None = strawberry.field(directives=[Encrypted()])
    first_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])
    last_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])


@strawberry.type
class _PgQuery:
    @strawberry.field
    def crypto_user(self, user_id: int) -> PgCryptoUserOut | None:
        try:
            u = PgCryptoUser.objects.get(pk=user_id)
        except PgCryptoUser.DoesNotExist:
            return None
        return PgCryptoUserOut(
            user_id=u.pk,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            display_name=u.display_name,
        )


@strawberry.type
class _PgMutation:
    @strawberry.mutation
    def create_user(
        self,
        email: typing.Annotated[str, Encrypted()],
        display_name: str,
    ) -> int:
        u = PgCryptoUser.objects.create(email=email, display_name=display_name)
        return u.pk

    @strawberry.mutation
    def create_user_profile(
        self,
        first_name: typing.Annotated[str, Encrypted(batch="profile")],
        last_name: typing.Annotated[str, Encrypted(batch="profile")],
        display_name: str,
    ) -> int:
        u = PgCryptoUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
        )
        return u.pk


_pg_schema = strawberry.Schema(
    query=_PgQuery,
    mutation=_PgMutation,
    extensions=[EncryptionMiddleware],
    types=[PgCryptoUserOut],
)


# ---------------------------------------------------------------------------
# PostgreSQL container fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def postgres_dsn():
    """Spin up a postgres:18.3-alpine container and yield DSN parameters."""
    with tc.PostgresContainer("postgres:18.3-alpine") as pg:
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
    """Reconfigure Django's default DB to point at the container."""
    from django.conf import settings

    original = dict(settings.DATABASES["default"])
    settings.DATABASES["default"].update(postgres_dsn)
    connection.close()
    connection.settings_dict.update(postgres_dsn)
    with django_db_blocker.unblock():
        yield
    settings.DATABASES["default"].update(original)
    connection.close()
    connection.settings_dict.update(original)


@pytest.fixture(scope="module")
def pg_crypto_table(pg_connection, django_db_blocker):
    """Create the PgCryptoUser table in the PostgreSQL container."""
    with django_db_blocker.unblock(), connection.schema_editor() as editor:
        editor.create_model(PgCryptoUser)
    yield
    try:
        with django_db_blocker.unblock(), connection.schema_editor() as editor:
            editor.delete_model(PgCryptoUser)
    except Exception:  # noqa: S110
        pass


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _execute(gql: str, *, authenticated: bool = True) -> dict:
    """Execute a GraphQL operation against the PostgreSQL-backed schema."""
    ctx = MagicMock()
    ctx.user.is_authenticated = authenticated
    result = _pg_schema.execute_sync(gql, context_value=ctx)
    return {"data": result.data, "errors": result.errors or []}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("pg_crypto_table")
class TestPostgresIndividualField:
    """AC1 against PostgreSQL: individual @encrypted field round-trip."""

    @pytest.mark.django_db
    def test_mutation_stores_ciphertext(self) -> None:
        result = _execute(
            'mutation { createUser(email: "pg@example.com", displayName: "PG") }'
        )
        assert not result["errors"], result["errors"]
        uid = result["data"]["createUser"]
        user = PgCryptoUser.objects.get(pk=uid)
        assert user.email != "pg@example.com", "DB must store ciphertext"

    @pytest.mark.django_db
    def test_query_returns_decrypted_plaintext(self) -> None:
        write = _execute(
            'mutation { createUser(email: "pg@example.com", displayName: "PG") }'
        )
        uid = write["data"]["createUser"]
        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}")
        assert not read["errors"], read["errors"]
        assert read["data"]["cryptoUser"]["email"] == "pg@example.com"


@pytest.mark.usefixtures("pg_crypto_table")
class TestPostgresBatchField:
    """AC2 against PostgreSQL: batch @encrypted(batch:) round-trip."""

    @pytest.mark.django_db
    def test_batch_round_trip(self) -> None:
        write = _execute(
            'mutation { createUserProfile(firstName: "PG", lastName: "User",'
            ' displayName: "PG User") }'
        )
        assert not write["errors"], write["errors"]
        uid = write["data"]["createUserProfile"]
        read = _execute(
            f"{{ cryptoUser(userId: {uid}) {{ firstName lastName displayName }} }}"
        )
        assert not read["errors"], read["errors"]
        assert read["data"]["cryptoUser"]["firstName"] == "PG"
        assert read["data"]["cryptoUser"]["lastName"] == "User"
