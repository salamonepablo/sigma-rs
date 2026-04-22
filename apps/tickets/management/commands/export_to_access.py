"""Django management command for exporting novedades to Access."""

from django.core.management.base import BaseCommand

from apps.tickets.application.use_cases.access_export_use_case import (
    AccessExportResult,
    AccessExportUseCase,
)


class Command(BaseCommand):
    help = "Export nuevas novedades from SQLite to Access database"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando export a Access..."))

        use_case = AccessExportUseCase()
        result = use_case.execute()

        self.stdout.write(
            self.style.SUCCESS(
                f"Export completado: {result.exported} exportados, "
                f"{result.skipped} omitidos, {result.errors} errores "
                f"({result.duration_seconds:.2f}s)"
            )
        )

        if result.error_details:
            self.stdout.write(self.style.ERROR("Errores:"))
            for error in result.error_details[:10]:
                self.stdout.write(f"  - {error}")

        # BaseCommand expects handle() to return a string/None.
        # Returning a dataclass causes Django to call .endswith() on it and crash.
        return None
