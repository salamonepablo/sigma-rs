from __future__ import annotations

from django.conf import settings
from django.db import models


class Ticket(models.Model):
    """Ticket de prueba para validar la arquitectura."""

    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        EN_PROGRESO = "en_progreso", "En Progreso"
        FINALIZADO = "finalizado", "Finalizado"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    numero = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )
    prioridad = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets_creados",
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self) -> str:
        return f"#{self.numero} - {self.titulo}"
