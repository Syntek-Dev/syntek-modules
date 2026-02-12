"""Organisation model.

Multi-tenant organisation model for isolating data across tenants.
Each organisation represents a separate tenant with its own users and data.
"""

import uuid

from django.core.validators import RegexValidator
from django.db import models


class Organisation(models.Model):
    """Multi-tenant organisation model.

    Represents a tenant organisation in the multi-tenant architecture.
    Each organisation has isolated data and its own set of users.

    Attributes:
        id: UUID primary key
        name: Organisation name
        slug: URL-friendly unique identifier (lowercase alphanumeric with hyphens)
        industry: Organisation industry/sector
        is_active: Active status flag
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
                message="Slug must be lowercase alphanumeric with hyphens only.",
            )
        ],
    )
    industry = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)  # type: ignore[call-arg]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_organisation"
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        """Return organisation name."""
        return str(self.name)
