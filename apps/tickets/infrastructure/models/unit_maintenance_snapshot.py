"""Pre-computed maintenance km snapshot per unit."""

from __future__ import annotations

from django.db import models

from apps.tickets.infrastructure.models.base import BaseModel
from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel


class UnitMaintenanceSnapshotModel(BaseModel):
    """Cached km-since values for a maintenance unit.

    One row per unit. Updated after every km sync and after a novedad close.
    Eliminates expensive SUM queries from the maintenance entry critical path.
    """

    maintenance_unit = models.OneToOneField(
        MaintenanceUnitModel,
        on_delete=models.CASCADE,
        related_name="maintenance_snapshot",
        verbose_name="Unidad de mantenimiento",
    )
    unit_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de unidad",
        db_index=True,
    )

    # --- RG or Puesta en Servicio ---
    last_rg_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha última RG / PS",
    )
    km_since_rg = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KM desde última RG / PS",
    )

    # --- Secondary: numeral (N1-N11 / 360K-720K) or RP ---
    last_numeral_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Código última numeral",
    )
    last_numeral_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha última numeral",
    )
    km_since_numeral = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KM desde última numeral",
    )

    # --- RP (Materfer / Nohab secondary slot) ---
    last_rp_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Código último RP",
    )
    last_rp_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha último RP",
    )
    km_since_rp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KM desde último RP",
    )

    # --- Tertiary: ABC, R6, or equivalent ---
    last_abc_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Código última ABC / R6",
    )
    last_abc_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha última ABC / R6",
    )
    km_since_abc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KM desde última ABC / R6",
    )

    computed_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Calculado el",
    )

    class Meta:
        db_table = "unit_maintenance_snapshot"
        verbose_name = "Snapshot de mantenimiento"
        verbose_name_plural = "Snapshots de mantenimiento"

    def __str__(self) -> str:
        return f"Snapshot {self.unit_number} @ {self.computed_at:%d/%m/%Y %H:%M}"
