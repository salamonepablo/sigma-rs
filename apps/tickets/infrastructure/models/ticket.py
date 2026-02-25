"""Ticket model for the tickets app.

The main entity of the SIGMA-RS system - tracks maintenance tickets
for rolling stock failures.
"""

from django.db import models

from apps.tickets.infrastructure.models.maintenance_unit import MaintenanceUnitModel
from apps.tickets.infrastructure.models.reference import (
    AffectedSystemModel,
    FailureTypeModel,
    GOPModel,
    SupervisorModel,
    TrainNumberModel,
)


class TicketModel(models.Model):
    """Maintenance ticket for rolling stock failures.

    Tracks reported failures, their resolution status, and associated data.
    """

    class Status(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        COMPLETED = "finalizado", "Finalizado"

    class EntryType(models.TextChoices):
        IMMEDIATE = "inmediato", "Inmediato"
        SCHEDULED = "programado", "Programado"
        NO = "no", "NO"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
    )

    # Required fields
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de ticket",
        help_text="Número único del ticket (ej: 2024-001)",
    )
    date = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha de la avería",
    )
    maintenance_unit = models.ForeignKey(
        MaintenanceUnitModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Unidad de mantenimiento",
    )
    gop = models.ForeignKey(
        GOPModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="GOP",
        help_text="Guardia Operativa que atiende el ticket",
    )
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        verbose_name="Tipo de ingreso",
        help_text="Inmediato, Programado o NO",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Estado",
    )
    reported_failure = models.TextField(
        verbose_name="Falla denunciada",
        help_text="Descripción de la falla reportada por el conductor",
    )

    # Optional foreign keys
    work_order_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de OT",
        help_text="Número de Orden de Trabajo (opcional)",
    )
    supervisor = models.ForeignKey(
        SupervisorModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        blank=True,
        null=True,
        verbose_name="Supervisor",
        help_text="Supervisor interviniente (opcional)",
    )
    train_number = models.ForeignKey(
        TrainNumberModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        blank=True,
        null=True,
        verbose_name="Número de tren",
    )
    failure_type = models.ForeignKey(
        FailureTypeModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        blank=True,
        null=True,
        verbose_name="Tipo de falla",
    )
    affected_system = models.ForeignKey(
        AffectedSystemModel,
        on_delete=models.PROTECT,
        related_name="tickets",
        blank=True,
        null=True,
        verbose_name="Sistema afectado",
    )

    # Time tracking
    notification_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de aviso",
    )
    intervention_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de intervención",
    )
    delivery_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de entrega",
    )

    # Observations
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Trabajo realizado / observaciones de la GOP",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "ticket"
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["ticket_number"]),
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["maintenance_unit"]),
        ]

    def __str__(self) -> str:
        return f"Ticket {self.ticket_number}"

    @property
    def is_pending(self) -> bool:
        """Check if the ticket is pending."""
        return self.status == self.Status.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if the ticket is completed."""
        return self.status == self.Status.COMPLETED
