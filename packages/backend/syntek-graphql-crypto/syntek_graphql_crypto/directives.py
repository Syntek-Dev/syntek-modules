"""Strawberry schema directives for the syntek-graphql-crypto middleware."""

from __future__ import annotations

import strawberry
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION], name="encrypted")
class Encrypted:
    """Mark a GraphQL field as encrypted.

    Use ``Encrypted()`` for individually encrypted fields and
    ``Encrypted(batch="group")`` for fields that share a batch decryption key.
    """

    batch: str | None = None

    def __init__(self, batch: str | None = None) -> None:
        self.batch = batch
