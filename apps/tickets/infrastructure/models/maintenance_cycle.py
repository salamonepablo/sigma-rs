"""Maintenance cycle configuration models."""

from __future__ import annotations

import uuid

from django.db import models

from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel
from apps.tickets.infrastructure.models.reference import (
    BrandModel,
    LocomotiveModelModel,
)


class MaintenanceCycleModel(models.Model):
    """Maintenance cycle definition for intervention scheduling."""

    class TriggerType(models.TextChoices):
        KM = "km", "Kilometers"
        TIME = "time", "Time"

    class TriggerUnit(models.TextChoices):
        KM = "km", "Kilometers"
        MONTH = "month", "Month"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    rolling_stock_type = models.CharField(
        max_length=20,
        choices=MaintenanceUnitModel.UnitType.choices,
        verbose_name="Tipo de unidad",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.PROTECT,
        related_name="maintenance_cycles",
        verbose_name="Marca",
    )
    model = models.ForeignKey(
        LocomotiveModelModel,
        on_delete=models.PROTECT,
        related_name="maintenance_cycles",
        null=True,
        blank=True,
        verbose_name="Modelo",
        help_text="Modelo específico cuando aplica",
    )
    intervention_code = models.CharField(
        max_length=20,
        verbose_name="Código de intervención",
        help_text="Código alineado con Tipos de Intervención",
    )
    intervention_name = models.CharField(
        max_length=100,
        verbose_name="Nombre de intervención",
    )
    trigger_type = models.CharField(
        max_length=10,
        choices=TriggerType.choices,
        verbose_name="Tipo de disparador",
    )
    trigger_value = models.PositiveIntegerField(
        verbose_name="Valor de disparador",
    )
    trigger_unit = models.CharField(
        max_length=10,
        choices=TriggerUnit.choices,
        verbose_name="Unidad de disparador",
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
        db_table = "maintenance_cycle"
        verbose_name = "Ciclo de mantenimiento"
        verbose_name_plural = "Ciclos de mantenimiento"
        ordering = ["rolling_stock_type", "brand", "trigger_value"]
        indexes = [
            models.Index(fields=["rolling_stock_type", "brand", "model"]),
            models.Index(fields=["intervention_code"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "rolling_stock_type",
                    "brand",
                    "model",
                    "intervention_code",
                    "trigger_type",
                    "trigger_value",
                    "trigger_unit",
                ],
                name="uniq_cycle_definition",
            )
        ]

    def __str__(self) -> str:
        model_label = f" {self.model.code}" if self.model else ""
        return (
            f"{self.rolling_stock_type} {self.brand.code}{model_label} - "
            f"{self.intervention_code} ({self.trigger_value} {self.trigger_unit})"
        )
