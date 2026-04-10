"""Use case for synchronizing Access novedades and kilometrage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from time import perf_counter

from django.conf import settings

from apps.tickets.application.use_cases.legacy_sync_use_case import (
    LegacySyncResult,
    SyncStats,
)
from apps.tickets.infrastructure.services.access_extractor import (
    AccessExtractor,
    AccessExtractorConfig,
)
from apps.tickets.infrastructure.services.access_kilometrage_importer import (
    AccessKilometrageImporter,
    AccessKilometrageSource,
)
from apps.tickets.infrastructure.services.access_novedad_importer import (
    AccessNovedadImporter,
    AccessNovedadSource,
)


@dataclass(frozen=True)
class AccessSyncConfig:
    baselocs_path: Path
    baseccrr_path: Path
    db_password: str | None
    script_path: Path
    powershell_path: Path


class AccessSyncUseCase:
    """Orchestrate Access novedades and kilometrage imports."""

    def __init__(self, config: AccessSyncConfig | None = None) -> None:
        self._config = config or self._build_default_config()

    def run(
        self,
        since_date: date | None = None,
        dry_run: bool = False,
        progress_every: int = 500,
        stdout_writer=None,
        stderr_writer=None,
    ) -> LegacySyncResult:
        extractor = AccessExtractor(
            AccessExtractorConfig(
                script_path=self._config.script_path,
                powershell_path=self._config.powershell_path,
            ),
            stdout_writer=stdout_writer,
            stderr_writer=stderr_writer,
        )
        novedad_importer = AccessNovedadImporter(extractor)
        kilometrage_importer = AccessKilometrageImporter(extractor)

        baselocs_novedad = AccessNovedadSource(
            db_path=self._config.baselocs_path,
            unit_field="Locs",
        )
        baseccrr_novedad = AccessNovedadSource(
            db_path=self._config.baseccrr_path,
            unit_field="Coche",
        )
        baselocs_km = AccessKilometrageSource(
            db_path=self._config.baselocs_path,
            unit_field="Locs",
        )
        baseccrr_km = AccessKilometrageSource(
            db_path=self._config.baseccrr_path,
            unit_field="Coche",
        )

        start = perf_counter()
        novedades = novedad_importer.import_all(
            baselocs=baselocs_novedad,
            baseccrr=baseccrr_novedad,
            db_password=self._config.db_password,
            since_date=since_date,
            dry_run=dry_run,
            progress_every=progress_every,
        )
        kilometrage = kilometrage_importer.import_all(
            baselocs=baselocs_km,
            baseccrr=baseccrr_km,
            db_password=self._config.db_password,
            since_date=since_date,
            dry_run=dry_run,
            progress_every=progress_every,
        )
        duration_seconds = perf_counter() - start

        return LegacySyncResult(
            novedades=novedades,
            kilometrage=kilometrage,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _build_default_config() -> AccessSyncConfig:
        baselocs_path = getattr(settings, "ACCESS_BASELOCS_PATH", "")
        baseccrr_path = getattr(settings, "ACCESS_BASECCRR_PATH", "")
        script_path = getattr(settings, "ACCESS_EXTRACTOR_SCRIPT", "")
        powershell_path = getattr(settings, "ACCESS_POWERSHELL_PATH", "")

        if not baselocs_path or not baseccrr_path:
            raise ValueError("Access DB paths are not configured.")
        if not script_path or not powershell_path:
            raise ValueError("Access extractor settings are not configured.")

        return AccessSyncConfig(
            baselocs_path=Path(baselocs_path),
            baseccrr_path=Path(baseccrr_path),
            db_password=getattr(settings, "ACCESS_DB_PASSWORD", None) or None,
            script_path=Path(script_path),
            powershell_path=Path(powershell_path),
        )
