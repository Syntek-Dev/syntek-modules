"""US008 — Green phase: full write→DB→read integration tests.

Uses real ``syntek_pyo3`` AES-256-GCM encryption and an in-memory SQLite
database.  No mocking.  Skipped automatically when the native extension has
not been built.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_integration.py \
        -v -m integration

AC coverage:
    AC1  — individual @encrypted field: mutation stores ciphertext in DB;
            query returns decrypted plaintext
    AC2  — batch @encrypted(batch:) group: mutation stores ciphertext per
            field; query returns all plaintext via single decrypt call
    AC7  — tampered DB ciphertext: field nulled, structured error appended,
            rest of response intact
    AC10 — unauthenticated read: encrypted fields null, auth error in errors,
            request not aborted
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

from syntek_graphql_crypto.directives import Encrypted  # noqa: E402
from syntek_graphql_crypto.middleware import EncryptionMiddleware  # noqa: E402

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Test-only Django model
#
# app_label = "syntek_graphql_crypto" so Django accepts the model; the table
# is created by the session-scoped fixture, not via migrations.
# ---------------------------------------------------------------------------


class CryptoUser(models.Model):
    """Minimal user model for crypto round-trip integration tests.

    Each encrypted column stores the AES-256-GCM ciphertext written by the
    middleware on mutation and read back (still ciphertext) by the resolver
    on query.  The middleware decrypts before serialisation.
    """

    email = models.TextField(default="")
    first_name = models.TextField(default="")
    last_name = models.TextField(default="")
    display_name = models.TextField(default="")

    class Meta:
        app_label = "syntek_graphql_crypto"

    def __str__(self) -> str:
        return f"CryptoUser({self.pk})"


# ---------------------------------------------------------------------------
# Strawberry output type
# ---------------------------------------------------------------------------


@strawberry.type
class CryptoUserOut:
    """Output type — field values are DB ciphertexts; middleware decrypts."""

    user_id: int
    display_name: str
    email: str | None = strawberry.field(directives=[Encrypted()])
    first_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])
    last_name: str | None = strawberry.field(directives=[Encrypted(batch="profile")])


# ---------------------------------------------------------------------------
# Strawberry schema (module-level singleton)
# ---------------------------------------------------------------------------


@strawberry.type
class _Query:
    @strawberry.field
    def crypto_user(self, user_id: int) -> CryptoUserOut | None:
        """Resolver returns raw DB values (ciphertext); middleware decrypts."""
        try:
            u = CryptoUser.objects.get(pk=user_id)
        except CryptoUser.DoesNotExist:
            return None
        return CryptoUserOut(
            user_id=u.pk,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            display_name=u.display_name,
        )


@strawberry.type
class _Mutation:
    @strawberry.mutation
    def create_user(
        self,
        email: typing.Annotated[str, Encrypted()],
        display_name: str,
    ) -> int:
        """Resolver receives ciphertext (encrypted by middleware); saves to DB."""
        u = CryptoUser.objects.create(email=email, display_name=display_name)
        return u.pk

    @strawberry.mutation
    def create_user_profile(
        self,
        first_name: typing.Annotated[str, Encrypted(batch="profile")],
        last_name: typing.Annotated[str, Encrypted(batch="profile")],
        display_name: str,
    ) -> int:
        """Both first_name and last_name encrypted in one batch call."""
        u = CryptoUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
        )
        return u.pk


_schema = strawberry.Schema(
    query=_Query,
    mutation=_Mutation,
    extensions=[EncryptionMiddleware],
    types=[CryptoUserOut],
)


# ---------------------------------------------------------------------------
# DB table fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def crypto_user_table(django_db_setup, django_db_blocker):  # type: ignore[return]
    """Create the CryptoUser table once for this test session."""
    with django_db_blocker.unblock(), connection.schema_editor() as editor:
        editor.create_model(CryptoUser)
    yield
    # Guard against the in-memory DB being reset by Django's test runner before
    # session teardown fires (common when multi-package test runs share a session).
    try:
        with django_db_blocker.unblock(), connection.schema_editor() as editor:
            editor.delete_model(CryptoUser)
    except Exception:  # noqa: S110
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _execute(gql: str, *, authenticated: bool = True) -> dict:
    """Execute a GraphQL operation against the integration schema."""
    ctx = MagicMock()
    ctx.user.is_authenticated = authenticated
    result = _schema.execute_sync(gql, context_value=ctx)
    return {"data": result.data, "errors": result.errors or []}


# ---------------------------------------------------------------------------
# AC1 — Individual @encrypted field: mutation stores ciphertext; query
#        returns plaintext
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("crypto_user_table")
class TestIndividualFieldRoundTrip:
    """AC1: individual @encrypted field write→DB→read round-trip."""

    @pytest.mark.django_db
    def test_mutation_stores_ciphertext_not_plaintext(self) -> None:
        """The DB email column must contain ciphertext, not 'alice@example.com'."""
        result = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        assert not result["errors"], result["errors"]
        uid = result["data"]["createUser"]
        user = CryptoUser.objects.get(pk=uid)
        assert user.email != "alice@example.com", "DB must store ciphertext"
        assert len(user.email) > 0, "DB ciphertext must be non-empty"

    @pytest.mark.django_db
    def test_query_returns_decrypted_plaintext(self) -> None:
        """A subsequent query must return the original plaintext string."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        assert not write["errors"], write["errors"]
        uid = write["data"]["createUser"]

        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}")
        assert not read["errors"], read["errors"]
        assert read["data"]["cryptoUser"]["email"] == "alice@example.com"
        assert read["data"]["cryptoUser"]["displayName"] == "Alice"

    @pytest.mark.django_db
    def test_different_plaintexts_produce_different_ciphertexts(self) -> None:
        """Two different plaintext emails must produce distinct ciphertexts in
        the DB (AES-256-GCM with random nonce)."""
        r1 = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "A") }'
        )
        r2 = _execute(
            'mutation { createUser(email: "bob@example.com", displayName: "B") }'
        )
        u1 = CryptoUser.objects.get(pk=r1["data"]["createUser"])
        u2 = CryptoUser.objects.get(pk=r2["data"]["createUser"])
        assert u1.email != u2.email, (
            "Different plaintexts must produce different ciphertexts"
        )


# ---------------------------------------------------------------------------
# AC2 — Batch @encrypted(batch:) group: mutation stores ciphertext per field;
#        query returns all plaintext
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("crypto_user_table")
class TestBatchGroupRoundTrip:
    """AC2: batch @encrypted(batch='profile') write→DB→read round-trip."""

    @pytest.mark.django_db
    def test_batch_mutation_stores_ciphertext_for_each_field(self) -> None:
        """Both first_name and last_name must be stored as ciphertext."""
        result = _execute(
            'mutation { createUserProfile(firstName: "Alice", lastName: "Smith",'
            ' displayName: "Alice Smith") }'
        )
        assert not result["errors"], result["errors"]
        uid = result["data"]["createUserProfile"]
        user = CryptoUser.objects.get(pk=uid)
        assert user.first_name != "Alice", "first_name DB value must be ciphertext"
        assert user.last_name != "Smith", "last_name DB value must be ciphertext"
        assert len(user.first_name) > 0
        assert len(user.last_name) > 0

    @pytest.mark.django_db
    def test_batch_query_returns_plaintext_for_all_fields(self) -> None:
        """Query must return decrypted plaintext for all batch-group fields."""
        write = _execute(
            'mutation { createUserProfile(firstName: "Alice", lastName: "Smith",'
            ' displayName: "Alice Smith") }'
        )
        assert not write["errors"], write["errors"]
        uid = write["data"]["createUserProfile"]

        read = _execute(
            f"{{ cryptoUser(userId: {uid}) {{ firstName lastName displayName }} }}"
        )
        assert not read["errors"], read["errors"]
        assert read["data"]["cryptoUser"]["firstName"] == "Alice"
        assert read["data"]["cryptoUser"]["lastName"] == "Smith"
        assert read["data"]["cryptoUser"]["displayName"] == "Alice Smith"

    @pytest.mark.django_db
    def test_non_encrypted_field_passes_through_unchanged(self) -> None:
        """The non-encrypted displayName field must be returned as-is."""
        write = _execute(
            'mutation { createUserProfile(firstName: "Alice", lastName: "Smith",'
            ' displayName: "Alice Smith") }'
        )
        uid = write["data"]["createUserProfile"]
        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ displayName }} }}")
        assert read["data"]["cryptoUser"]["displayName"] == "Alice Smith"


# ---------------------------------------------------------------------------
# AC7 — Tampered DB ciphertext: field nulled, structured error appended,
#        rest of response intact
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("crypto_user_table")
class TestTamperedCiphertext:
    """AC7: corrupt ciphertext → field null, error appended, response intact."""

    @pytest.mark.django_db
    def test_tampered_field_returns_null(self) -> None:
        """Overwriting the DB ciphertext with garbage must null the field."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]
        CryptoUser.objects.filter(pk=uid).update(email="TAMPERED_NOT_VALID_CT")

        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}")
        assert read["data"]["cryptoUser"]["email"] is None, (
            "Tampered field must be null"
        )

    @pytest.mark.django_db
    def test_tampered_field_appends_structured_error(self) -> None:
        """A structured error must appear in the errors array."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]
        CryptoUser.objects.filter(pk=uid).update(email="TAMPERED_NOT_VALID_CT")

        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}")
        assert len(read["errors"]) >= 1, "At least one error must be appended"

    @pytest.mark.django_db
    def test_tampered_field_does_not_abort_rest_of_response(self) -> None:
        """Non-encrypted fields must still be present when decryption fails."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]
        CryptoUser.objects.filter(pk=uid).update(email="TAMPERED_NOT_VALID_CT")

        read = _execute(f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}")
        assert read["data"]["cryptoUser"]["displayName"] == "Alice", (
            "Non-encrypted field must be returned even when decryption fails"
        )


# ---------------------------------------------------------------------------
# AC10 — Unauthenticated read: encrypted fields null, auth error, not aborted
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("crypto_user_table")
class TestUnauthenticatedRead:
    """AC10: unauthenticated requests null encrypted fields and append auth error."""

    @pytest.mark.django_db
    def test_unauthenticated_read_nulls_encrypted_fields(self) -> None:
        """All @encrypted fields must be null when the request is unauthenticated."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]

        read = _execute(
            f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}",
            authenticated=False,
        )
        assert read["data"]["cryptoUser"]["email"] is None

    @pytest.mark.django_db
    def test_unauthenticated_read_appends_auth_error(self) -> None:
        """An auth error must appear in the errors array."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]

        read = _execute(
            f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}",
            authenticated=False,
        )
        assert len(read["errors"]) >= 1
        error_text = " ".join(str(e) for e in read["errors"]).lower()
        keywords = ("auth", "unauthenticated", "unauthori")
        assert any(kw in error_text for kw in keywords), (
            f"Error must reference authentication: {read['errors']}"
        )

    @pytest.mark.django_db
    def test_unauthenticated_read_does_not_abort_response(self) -> None:
        """Non-encrypted fields must still be returned for unauthenticated requests."""
        write = _execute(
            'mutation { createUser(email: "alice@example.com", displayName: "Alice") }'
        )
        uid = write["data"]["createUser"]

        read = _execute(
            f"{{ cryptoUser(userId: {uid}) {{ email displayName }} }}",
            authenticated=False,
        )
        assert read["data"]["cryptoUser"]["displayName"] == "Alice"
