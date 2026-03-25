"""Maintenance entry email dispatch audit model."""

from __future__ import annotations

from django.db import models

from apps.tickets.infrastructure.models.base import BaseModel
from apps.tickets.infrastructure.models.maintenance_entry import MaintenanceEntryModel


class MaintenanceEntryEmailDispatchModel(BaseModel):
    """Track local Outlook email dispatch for maintenance entries."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CLAIMED = "claimed", "Claimed"
        DRAFTED = "drafted", "Drafted"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    entry = models.ForeignKey(
        MaintenanceEntryModel,
        on_delete=models.PROTECT,
        related_name="email_dispatches",
        verbose_name="Ingreso",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Estado",
    )
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="Intentos",
    )
    last_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Error",
    )
    windows_username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Usuario Windows",
    )
    sent_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de envio",
    )
    drafted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de borrador",
    )
    claimed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de reclamacion",
    )
    to_recipients = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Destinatarios TO",
    )
    cc_recipients = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Destinatarios CC",
    )
    subject = models.CharField(
        max_length=255,
        verbose_name="Asunto",
    )
    body = models.TextField(
        verbose_name="Cuerpo",
    )
    body_html = models.TextField(
        blank=True,
        null=True,
        verbose_name="Cuerpo HTML",
    )

    class Meta:
        db_table = "maintenance_entry_email_dispatch"
        verbose_name = "Ingreso - Envio de correo"
        verbose_name_plural = "Ingresos - Envios de correo"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["entry"]),
        ]

    def __str__(self) -> str:
        return f"Ingreso {self.entry_id} - {self.status}"
