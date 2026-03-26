"""Tray terminal registry model."""

from __future__ import annotations

from django.db import models

from apps.tickets.infrastructure.models.base import BaseModel


class TrayTerminalModel(BaseModel):
    """Track registered tray terminals for email dispatch routing."""

    terminal_id = models.CharField(
        max_length=36,
        unique=True,
        verbose_name="ID de terminal",
    )
    windows_username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Usuario Windows",
    )
    hostname = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre de host",
    )
    last_seen = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Última conexión",
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name="En línea",
    )
    registration_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP de registro",
    )

    class Meta:
        db_table = "tray_terminal"
        verbose_name = "Terminal de bandeja"
        verbose_name_plural = "Terminales de bandeja"
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["terminal_id"]),
            models.Index(fields=["is_online", "last_seen"]),
        ]

    def __str__(self) -> str:
        return f"Terminal {self.terminal_id} ({self.windows_username})"
