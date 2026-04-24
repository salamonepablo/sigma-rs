"""Django app configuration for the tickets application."""

import sys

from django.apps import AppConfig

# Management commands that should NOT start the scheduler
_SKIP_COMMANDS = {
    "migrate",
    "makemigrations",
    "showmigrations",
    "collectstatic",
    "check",
    "shell",
    "dbshell",
    "createsuperuser",
    "test",
}

_SKIP_PREFIXES = (
    "import_",
    "load_",
    "build_",
    "sync_",
    "export_",
    "maintenance_",
    "seed_",
    "backfill_",
    "normalize_",
    "migrate_",
)


def _should_start_scheduler() -> bool:
    """Return True only when running as a web server process."""
    if "pytest" in sys.modules:
        return False
    argv = sys.argv
    if len(argv) >= 2:
        cmd = argv[1]
        if cmd in _SKIP_COMMANDS:
            return False
        if any(cmd.startswith(p) for p in _SKIP_PREFIXES):
            return False
    return True


class TicketsConfig(AppConfig):
    """Configuration for the tickets app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tickets"
    verbose_name = "Tickets de Mantenimiento"

    def ready(self) -> None:
        if not _should_start_scheduler():
            return
        try:
            from apps.tickets.infrastructure.scheduler import start_scheduler

            start_scheduler()
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Failed to start Access sync scheduler"
            )
