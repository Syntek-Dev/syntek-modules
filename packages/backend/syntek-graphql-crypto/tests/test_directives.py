"""US008 — Red phase: directive definition tests for ``syntek-graphql-crypto``.

Verifies that the ``Encrypted`` Strawberry schema directive is correctly defined,
importable, and behaves as a proper Strawberry directive annotation.

All tests FAIL during the red phase because ``syntek_graphql_crypto`` does not
yet exist.  They will pass after the green phase.

Run with:
    pytest packages/backend/syntek-graphql-crypto/tests/test_directives.py -v

AC coverage:
    AC1  — individual ``@encrypted`` field annotation
    AC2  — batch ``@encrypted(batch: "group")`` field annotation
    AC3  — individual and batch variants are distinct and non-mixing
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# AC1 / AC2 / AC3: Encrypted directive — import and shape
# ---------------------------------------------------------------------------


class TestEncryptedDirective:
    """The ``Encrypted`` directive must be importable and correctly shaped."""

    def test_encrypted_directive_importable(self) -> None:
        """The ``Encrypted`` directive class must be importable from the
        ``syntek_graphql_crypto.directives`` module (AC1).
        """
        from syntek_graphql_crypto.directives import Encrypted  # noqa: F401

    def test_encrypted_directive_can_annotate_field(self) -> None:
        """``Encrypted()`` must be accepted by ``strawberry.field`` as a directive
        so that schema authors can annotate fields with ``@encrypted`` (AC1).
        """
        import strawberry
        from syntek_graphql_crypto.directives import Encrypted

        @strawberry.type
        class _TestType:
            email: str = strawberry.field(
                directives=[Encrypted()],
                resolver=lambda: "placeholder",
            )

        # If Strawberry accepts the directive without raising, the test passes.
        assert _TestType is not None

    def test_encrypted_individual_has_no_batch(self) -> None:
        """An ``Encrypted()`` instance with no arguments must have ``batch``
        equal to ``None`` — indicating an individually encrypted field (AC1).
        """
        from syntek_graphql_crypto.directives import Encrypted

        directive = Encrypted()
        assert directive.batch is None

    def test_encrypted_batch_has_batch_parameter(self) -> None:
        """An ``Encrypted(batch="profile")`` instance must expose the group name
        via its ``batch`` attribute (AC2).
        """
        from syntek_graphql_crypto.directives import Encrypted

        directive = Encrypted(batch="profile")
        assert directive.batch == "profile"

    def test_two_different_batch_groups_are_not_equal(self) -> None:
        """Two directives with different ``batch`` names must not share the same
        group identifier — the middleware must never combine them (AC3).
        """
        from syntek_graphql_crypto.directives import Encrypted

        group_a = Encrypted(batch="profile")
        group_b = Encrypted(batch="address")
        assert group_a.batch != group_b.batch

    def test_encrypted_is_a_strawberry_schema_directive(self) -> None:
        """``Encrypted`` must be a Strawberry schema directive type so it
        integrates transparently with Strawberry's extension mechanism (AC1 / AC2).
        """
        import strawberry
        from syntek_graphql_crypto.directives import Encrypted

        directive = Encrypted()
        # Strawberry schema directives are instances of a class decorated with
        # ``@strawberry.schema_directive``.  The generated class will have a
        # ``__strawberry_directive__`` attribute.
        assert hasattr(type(directive), "__strawberry_directive__") or isinstance(
            directive,
            strawberry.schema_directive,  # type: ignore[attr-defined]
        ), "Encrypted must be a Strawberry schema directive"

    def test_encrypted_individual_and_batch_instances_distinguish_by_batch_attribute(
        self,
    ) -> None:
        """The ``batch`` attribute alone must be sufficient to determine whether
        a field is individually encrypted or part of a group — the middleware
        relies on ``batch is None`` vs ``batch is not None`` (AC1 / AC2 / AC3).
        """
        from syntek_graphql_crypto.directives import Encrypted

        individual = Encrypted()
        batch = Encrypted(batch="profile")
        assert individual.batch is None
        assert batch.batch is not None
