"""Kilometrage records for maintenance units."""

from django.db import models

from apps.tickets.infrastructure.models.base import BaseModel
from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel


class KilometrageRecordModel(BaseModel):
    """Kilometrage record for a unit at a given date."""

    maintenance_unit = models.ForeignKey(
        MaintenanceUnitModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kilometrage_records",
        verbose_name="Unidad de mantenimiento",
    )
    unit_number = models.CharField(
        max_length=50,
        verbose_name="Número de unidad",
    )
    record_date = models.DateField(
        verbose_name="Fecha",
    )
    km_value = models.PositiveIntegerField(
        verbose_name="Kilometraje",
    )
    source = models.CharField(
        max_length=30,
        verbose_name="Origen",
        blank=True,
        default="",
    )

    class Meta:
        db_table = "kilometrage_record"
        verbose_name = "Registro de kilometraje"
        verbose_name_plural = "Registros de kilometraje"
        ordering = ["-record_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit_number", "record_date"],
                name="uniq_kilometrage_unit_date",
            )
        ]
        indexes = [
            models.Index(
                fields=["unit_number", "record_date"],
                name="km_unit_date_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.unit_number} - {self.record_date:%d/%m/%Y}"
