"""Novedad (Detencion) model for the tickets app.

Represents historical maintenance records imported from legacy Access database.
This model stores locomotive detention/maintenance events.
"""

import uuid

from django.db import models

from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel
from apps.tickets.infrastructure.models.reference import (
    IntervencionTipoModel,
    LugarModel,
)


class NovedadModel(models.Model):
    """Maintenance event record (Detención/Novedad).

    Imported from legacy baseLocs.mdb Access database.
    Records maintenance interventions on locomotives and motorcoaches.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    maintenance_unit = models.ForeignKey(
        MaintenanceUnitModel,
        on_delete=models.PROTECT,
        related_name="novedades",
        verbose_name="Unidad de Mantenimiento",
        null=True,
        blank=True,
        help_text="Locomotora o Coche Motor",
    )
    # Keep legacy unit identifier for records without matching MaintenanceUnit
    legacy_unit_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código Unidad (Legacy)",
        help_text="Código original de la base legacy",
    )
    fecha_desde = models.DateField(
        verbose_name="Fecha Desde",
    )
    fecha_hasta = models.DateField(
        verbose_name="Fecha Hasta",
        blank=True,
        null=True,
    )
    fecha_estimada = models.DateField(
        verbose_name="Fecha Estimada",
        blank=True,
        null=True,
        help_text="Fecha estimada de finalización",
    )
    intervencion = models.ForeignKey(
        IntervencionTipoModel,
        on_delete=models.PROTECT,
        related_name="novedades",
        verbose_name="Tipo de Intervención",
        null=True,
        blank=True,
    )
    # Keep legacy intervention code for records without matching IntervencionTipo
    legacy_intervencion_codigo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Código Intervención (Legacy)",
    )
    lugar = models.ForeignKey(
        LugarModel,
        on_delete=models.PROTECT,
        related_name="novedades",
        verbose_name="Lugar",
        null=True,
        blank=True,
    )
    # Keep legacy lugar code for records without matching Lugar
    legacy_lugar_codigo = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Código Lugar (Legacy)",
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )
    # Flag to identify imported vs manually created records
    is_legacy = models.BooleanField(
        default=False,
        verbose_name="Registro Legacy",
        help_text="Indica si fue importado de la base legacy",
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
        db_table = "novedad"
        verbose_name = "Novedad"
        verbose_name_plural = "Novedades"
        ordering = ["-fecha_desde", "-created_at"]
        indexes = [
            models.Index(fields=["fecha_desde"]),
            models.Index(fields=["maintenance_unit"]),
            models.Index(fields=["intervencion"]),
            models.Index(fields=["legacy_unit_code"]),
        ]

    def __str__(self) -> str:
        unit = (
            self.maintenance_unit.number
            if self.maintenance_unit
            else self.legacy_unit_code
        )
        interv = (
            self.intervencion.codigo
            if self.intervencion
            else self.legacy_intervencion_codigo
        )
        return f"{unit} - {self.fecha_desde} - {interv}"
