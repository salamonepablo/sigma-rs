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
    baselocs_path: Path | None
    baseccrr_path: Path | None
    db_password: str | None
    script_path: Path
    powershell_path: Path


@dataclass(frozen=True)
class AccessSyncFilters:
    include_locs: bool = True
    include_ccrr: bool = True
    include_novedades: bool = True
    include_kilometrage: bool = True


class AccessSyncUseCase:
    """Orchestrate Access novedades and kilometrage imports."""

    def __init__(self, config: AccessSyncConfig | None = None) -> None:
        self._config = config or self._build_default_config()

    def run(
        self,
        since_date: date | None = None,
        dry_run: bool = False,
        progress_every: int = 5000,
        with_count: bool = False,
        stdout_writer=None,
        stderr_writer=None,
        filters: AccessSyncFilters | None = None,
    ) -> LegacySyncResult:
        resolved_filters = filters or AccessSyncFilters()
        self._validate_filters(resolved_filters)
        self._validate_config_paths(resolved_filters)

        extractor = AccessExtractor(
            AccessExtractorConfig(
                script_path=self._config.script_path,
                powershell_path=self._config.powershell_path,
            ),
            stdout_writer=stdout_writer,
            stderr_writer=stderr_writer,
        )

        baselocs_path = (
            self._config.baselocs_path if resolved_filters.include_locs else None
        )
        baseccrr_path = (
            self._config.baseccrr_path if resolved_filters.include_ccrr else None
        )

        start = perf_counter()
        novedades = self._empty_stats()
        kilometrage = self._empty_stats()

        if resolved_filters.include_novedades:
            novedad_importer = AccessNovedadImporter(extractor)
            baselocs_novedad = (
                AccessNovedadSource(db_path=baselocs_path, unit_field="Locs")
                if baselocs_path
                else None
            )
            baseccrr_novedad = (
                AccessNovedadSource(db_path=baseccrr_path, unit_field="Coche")
                if baseccrr_path
                else None
            )
            novedades = novedad_importer.import_all(
                baselocs=baselocs_novedad,
                baseccrr=baseccrr_novedad,
                db_password=self._config.db_password,
                since_date=since_date,
                dry_run=dry_run,
                progress_every=progress_every,
                skip_count=not with_count,
            )

        if resolved_filters.include_kilometrage:
            kilometrage_importer = AccessKilometrageImporter(extractor)
            baselocs_km = (
                AccessKilometrageSource(
                    db_path=baselocs_path,
                    unit_field="Locs",
                    source_label="access_locs",
                )
                if baselocs_path
                else None
            )
            baseccrr_km = (
                AccessKilometrageSource(
                    db_path=baseccrr_path,
                    unit_field="Coche",
                    source_label="access_ccrr",
                )
                if baseccrr_path
                else None
            )
            kilometrage = kilometrage_importer.import_all(
                baselocs=baselocs_km,
                baseccrr=baseccrr_km,
                db_password=self._config.db_password,
                since_date=since_date,
                dry_run=dry_run,
                progress_every=progress_every,
                skip_count=not with_count,
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

    @staticmethod
    def _validate_filters(filters: AccessSyncFilters) -> None:
        if not (filters.include_locs or filters.include_ccrr):
            raise ValueError("At least one origin must be selected.")
        if not (filters.include_novedades or filters.include_kilometrage):
            raise ValueError("At least one data type must be selected.")

    def _validate_config_paths(self, filters: AccessSyncFilters) -> None:
        if filters.include_locs and not self._config.baselocs_path:
            raise ValueError("Baselocs path is required for LOCS import.")
        if filters.include_ccrr and not self._config.baseccrr_path:
            raise ValueError("BaseCCRR path is required for CCRR import.")

    @staticmethod
    def _empty_stats() -> SyncStats:
        return SyncStats(
            processed=0,
            inserted=0,
            skipped_old=0,
            duplicates=0,
            invalid=0,
        )
