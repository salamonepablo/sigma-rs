"""Base model for all Django models in the tickets app.

Provides common fields and behavior for all models.
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and timestamps.

    All models in the tickets app should inherit from this class.

    Attributes:
        id: UUID primary key, auto-generated.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
