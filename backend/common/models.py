"""Base model classes with proper type annotations for Django models.

This module provides base classes that include proper type hints for Django's
ORM features, particularly the `objects` manager, which is not properly typed
in django-stubs.

Usage:
    from backend.common.models import BaseModel

    class MyModel(BaseModel):
        name = models.CharField(max_length=100)

        class Meta:
            db_table = "my_model"

The BaseModel automatically provides proper typing for:
- Model.objects manager
- Model.DoesNotExist exception
- Model.MultipleObjectsReturned exception
"""

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from django.db import models
from django.db.models import Manager

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager

# Type variable for generic model typing
_T = TypeVar("_T", bound="BaseModel")


class BaseModel(models.Model):
    """Abstract base model with proper type annotations.

    Provides proper type hints for Django ORM features that django-stubs
    doesn't handle well, particularly the objects manager.

    All Syntek models should inherit from this base class for better
    type checking support.
    """

    # Properly typed objects manager
    objects: ClassVar[BaseManager[Any]] = Manager()

    # Exception classes (automatically created by Django)
    DoesNotExist: ClassVar[type[Exception]]
    MultipleObjectsReturned: ClassVar[type[Exception]]

    class Meta:
        """Mark this as an abstract model."""

        abstract = True
