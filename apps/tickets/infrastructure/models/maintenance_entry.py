"""Maintenance entry model for operational ingress workflow."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel
from apps.tickets.infrastructure.models.novedad import NovedadModel
from apps.tickets.infrastructure.models.reference import (
    IntervencionTipoModel,
    LugarModel,
)


class MaintenanceEntryModel(models.Model):
    """Operational maintenance entry record."""

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
    novedad = models.ForeignKey(
        NovedadModel,
        on_delete=models.PROTECT,
        related_name="maintenance_entries",
        verbose_name="Novedad",
    )
    maintenance_unit = models.ForeignKey(
        MaintenanceUnitModel,
        on_delete=models.PROTECT,
        related_name="maintenance_entries",
        verbose_name="Unidad de mantenimiento",
        null=True,
        blank=True,
    )
    lugar = models.ForeignKey(
        LugarModel,
        on_delete=models.PROTECT,
        related_name="maintenance_entries",
        verbose_name="Lugar",
        null=True,
        blank=True,
    )
    entry_datetime = models.DateTimeField(
        verbose_name="Fecha y hora de ingreso",
    )
    exit_datetime = models.DateTimeField(
        verbose_name="Fecha y hora de egreso",
        null=True,
        blank=True,
    )
    trigger_type = models.CharField(
        max_length=10,
        choices=TriggerType.choices,
        verbose_name="Tipo de disparador",
        null=True,
        blank=True,
    )
    trigger_value = models.PositiveIntegerField(
        verbose_name="Valor de disparador",
        null=True,
        blank=True,
    )
    trigger_unit = models.CharField(
        max_length=10,
        choices=TriggerUnit.choices,
        verbose_name="Unidad de disparador",
        null=True,
        blank=True,
    )
    suggested_intervention_code = models.CharField(
        max_length=20,
        verbose_name="Intervención sugerida",
        null=True,
        blank=True,
    )
    selected_intervention = models.ForeignKey(
        IntervencionTipoModel,
        on_delete=models.PROTECT,
        related_name="maintenance_entries",
        verbose_name="Intervención seleccionada",
        null=True,
        blank=True,
    )
    checklist_tasks = models.TextField(
        verbose_name="Checklist de tareas",
        blank=True,
        null=True,
        help_text="Lista de tareas (una por línea)",
    )
    observations = models.TextField(
        verbose_name="Observaciones",
        blank=True,
        null=True,
    )
    pdf_path = models.CharField(
        max_length=255,
        verbose_name="Ruta del PDF",
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="maintenance_entries",
        verbose_name="Creado por",
        null=True,
        blank=True,
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
        db_table = "maintenance_entry"
        verbose_name = "Ingreso a mantenimiento"
        verbose_name_plural = "Ingresos a mantenimiento"
        ordering = ["-entry_datetime", "-created_at"]
        indexes = [
            models.Index(fields=["entry_datetime"]),
            models.Index(fields=["maintenance_unit"]),
        ]

    def __str__(self) -> str:
        unit = self.maintenance_unit.number if self.maintenance_unit else "-"
        return f"Ingreso {unit} - {self.entry_datetime:%Y-%m-%d}"
