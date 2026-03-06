"""Email recipient configuration models."""

from __future__ import annotations

import uuid

from django.db import models

from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel
from apps.tickets.infrastructure.models.reference import LugarModel


class LugarEmailRecipientModel(models.Model):
    """Recipients for maintenance entry notifications by location."""

    class RecipientType(models.TextChoices):
        TO = "to", "Para"
        CC = "cc", "Copia"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    lugar = models.ForeignKey(
        LugarModel,
        on_delete=models.PROTECT,
        related_name="mail_recipients",
        verbose_name="Lugar",
        null=True,
        blank=True,
        help_text="Lugar específico. Si está vacío, aplica como default.",
    )
    unit_type = models.CharField(
        max_length=20,
        choices=MaintenanceUnitModel.UnitType.choices,
        verbose_name="Tipo de unidad",
    )
    recipient_type = models.CharField(
        max_length=5,
        choices=RecipientType.choices,
        verbose_name="Tipo de destinatario",
    )
    email = models.EmailField(
        verbose_name="Email",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
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
        db_table = "lugar_email_recipient"
        verbose_name = "Destinatario por lugar"
        verbose_name_plural = "Destinatarios por lugar"
        ordering = ["unit_type", "recipient_type", "email"]
        indexes = [
            models.Index(fields=["lugar", "unit_type"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        lugar_desc = self.lugar.descripcion if self.lugar else "Default"
        return f"{lugar_desc} - {self.email}"
