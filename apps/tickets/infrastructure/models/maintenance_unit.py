"""Maintenance unit models for the tickets app.

Contains models for rolling stock: Locomotive, Railcar, Motorcoach.
Uses Django model inheritance with a common MaintenanceUnit base.
"""

from django.db import models

from apps.tickets.infrastructure.models.reference import (
    BrandModel,
    LocomotiveModelModel,
    RailcarClassModel,
)


class MaintenanceUnitModel(models.Model):
    """Base model for all maintenance units (rolling stock).

    This is a concrete model that holds common fields.
    Subclasses (Locomotive, Railcar, Motorcoach) link to this via OneToOne.
    """

    class UnitType(models.TextChoices):
        LOCOMOTIVE = "locomotora", "Locomotora"
        RAILCAR = "coche_remolcado", "Coche Remolcado"
        MOTORCOACH = "coche_motor", "Coche Motor"

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
    )
    number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número",
        help_text="Número de identificación de la unidad (ej: A904, U3001)",
    )
    unit_type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        verbose_name="Tipo de unidad",
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
        db_table = "maintenance_unit"
        verbose_name = "Unidad de mantenimiento"
        verbose_name_plural = "Unidades de mantenimiento"
        ordering = ["number"]

    def __str__(self) -> str:
        return self.number


class LocomotiveModel(models.Model):
    """Diesel locomotive maintenance unit.

    Known brands: GM (GT22CW, G22CW, etc.), CNR (8G, 8H).
    """

    maintenance_unit = models.OneToOneField(
        MaintenanceUnitModel,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="locomotive",
        verbose_name="Unidad de mantenimiento",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.PROTECT,
        related_name="locomotives",
        verbose_name="Marca",
    )
    model = models.ForeignKey(
        LocomotiveModelModel,
        on_delete=models.PROTECT,
        related_name="locomotives",
        verbose_name="Modelo",
    )

    class Meta:
        db_table = "locomotive"
        verbose_name = "Locomotora"
        verbose_name_plural = "Locomotoras"

    def __str__(self) -> str:
        return f"Locomotora {self.maintenance_unit.number}"

    @property
    def number(self) -> str:
        """Return the unit number."""
        return self.maintenance_unit.number

    @property
    def is_active(self) -> bool:
        """Return whether the unit is active."""
        return self.maintenance_unit.is_active


class RailcarModel(models.Model):
    """Railcar (Coche Remolcado) maintenance unit.

    Known brands: Materfer (U, FU, F), CNR (CPA, CRA, PUA, etc.).
    """

    maintenance_unit = models.OneToOneField(
        MaintenanceUnitModel,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="railcar",
        verbose_name="Unidad de mantenimiento",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.PROTECT,
        related_name="railcars",
        verbose_name="Marca",
    )
    railcar_class = models.ForeignKey(
        RailcarClassModel,
        on_delete=models.PROTECT,
        related_name="railcars",
        verbose_name="Clase",
    )

    class Meta:
        db_table = "railcar"
        verbose_name = "Coche remolcado"
        verbose_name_plural = "Coches remolcados"

    def __str__(self) -> str:
        return f"Coche {self.maintenance_unit.number}"

    @property
    def number(self) -> str:
        """Return the unit number."""
        return self.maintenance_unit.number

    @property
    def is_active(self) -> bool:
        """Return whether the unit is active."""
        return self.maintenance_unit.is_active


class MotorcoachModel(models.Model):
    """Motorcoach (Coche Motor) maintenance unit.

    Known brand: CNR.
    Configurations: CM-CM, CM-R-CM.
    """

    maintenance_unit = models.OneToOneField(
        MaintenanceUnitModel,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="motorcoach",
        verbose_name="Unidad de mantenimiento",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.PROTECT,
        related_name="motorcoaches",
        verbose_name="Marca",
    )
    configuration = models.CharField(
        max_length=50,
        verbose_name="Configuración",
        help_text="Configuración de coches (ej: CM-CM, CM-R-CM)",
    )
    car_count = models.PositiveSmallIntegerField(
        verbose_name="Cantidad de coches",
        help_text="Número de coches en la formación",
    )

    class Meta:
        db_table = "motorcoach"
        verbose_name = "Coche motor"
        verbose_name_plural = "Coches motor"

    def __str__(self) -> str:
        return f"Coche Motor {self.maintenance_unit.number}"

    @property
    def number(self) -> str:
        """Return the unit number."""
        return self.maintenance_unit.number

    @property
    def is_active(self) -> bool:
        """Return whether the unit is active."""
        return self.maintenance_unit.is_active
