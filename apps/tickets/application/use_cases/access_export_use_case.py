"""Use case for exporting novedades from SQLite to Access."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from apps.tickets.infrastructure.services.access_novedad_exporter import (
    AccessNovedadExporter,
    ExportConfig,
)


@dataclass
class AccessExportResult:
    """Result of the export operation."""

    exported: int
    skipped: int
    errors: int
    duration_seconds: float
    error_details: list[str]


class AccessExportUseCase:
    """Orchestrate exports from SQLite to Access database."""

    def __init__(self, config: ExportConfig | None = None) -> None:
        self._config = config
        self._exporter: AccessNovedadExporter | None = None

    def execute(self) -> AccessExportResult:
        """Execute the export operation."""
        start = perf_counter()

        exporter = self._get_exporter()
        stats = exporter.export_all_pending()

        duration = perf_counter() - start

        return AccessExportResult(
            exported=stats.get("exported", 0),
            skipped=stats.get("skipped", 0),
            errors=stats.get("errors", 0),
            duration_seconds=duration,
            error_details=stats.get("error_details", []),
        )

    def _get_exporter(self) -> AccessNovedadExporter:
        if self._exporter is None:
            config = self._config or self._build_default_config()
            self._exporter = AccessNovedadExporter(config)
        return self._exporter

    @staticmethod
    def _build_default_config() -> ExportConfig:
        from pathlib import Path

        from django.conf import settings

        baselocs_path = getattr(settings, "ACCESS_BASELOCS_PATH", "")
        baseccrr_path = getattr(settings, "ACCESS_BASECCRR_PATH", "")
        script_path = getattr(settings, "ACCESS_EXPORT_SCRIPT", "")
        db_password = getattr(settings, "ACCESS_DB_PASSWORD", "")

        if not baselocs_path:
            raise ValueError("ACCESS_BASELOCS_PATH is not configured.")
        if not script_path:
            raise ValueError("ACCESS_EXPORT_SCRIPT is not configured.")

        return ExportConfig(
            script_path=Path(script_path),
            baselocs_path=Path(baselocs_path),
            baseccrr_path=Path(baseccrr_path) if baseccrr_path else None,
            db_password=db_password,
        )
