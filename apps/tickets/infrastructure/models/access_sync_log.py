"""Model for tracking Access sync execution history."""

from django.db import models


class AccessSyncLogModel(models.Model):
    """Log entry for each Access sync run."""

    TRIGGER_STARTUP = "startup"
    TRIGGER_SCHEDULED = "scheduled"
    TRIGGER_MANUAL = "manual"

    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_SKIPPED = "skipped"

    ran_at = models.DateTimeField(auto_now_add=True, verbose_name="Ejecutado")
    trigger = models.CharField(max_length=20, verbose_name="Disparador")
    novedades_inserted = models.IntegerField(default=0, verbose_name="Novedades nuevas")
    novedades_duplicates = models.IntegerField(
        default=0, verbose_name="Novedades duplicadas"
    )
    kilometrage_inserted = models.IntegerField(default=0, verbose_name="Km insertados")
    duration_seconds = models.FloatField(default=0, verbose_name="Duración (s)")
    status = models.CharField(max_length=20, default="ok", verbose_name="Estado")
    error_message = models.TextField(blank=True, default="", verbose_name="Error")

    class Meta:
        db_table = "access_sync_log"
        verbose_name = "Log de sync Access"
        verbose_name_plural = "Logs de sync Access"
        ordering = ["-ran_at"]

    def __str__(self) -> str:
        return f"{self.trigger} {self.ran_at:%d/%m/%Y %H:%M} [{self.status}]"
