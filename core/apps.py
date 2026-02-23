from __future__ import annotations

from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _activate_wal_mode(sender, connection, **kwargs):
    """Activa WAL mode en SQLite para mejor concurrencia."""
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Núcleo"

    def ready(self):
        connection_created.connect(_activate_wal_mode)
