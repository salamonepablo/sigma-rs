"""Use case for synchronizing legacy novedades and kilometrage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from django.conf import settings


@dataclass(frozen=True)
class SyncStats:
    """Aggregate stats for a sync step."""

    processed: int
    inserted: int
    skipped_old: int
    duplicates: int
    invalid: int


@dataclass(frozen=True)
class LegacySyncResult:
    """Combined sync output for novedades and kilometrage."""

    novedades: SyncStats
    kilometrage: SyncStats
    duration_seconds: float


class LegacySyncUseCase:
    """Orchestrate legacy novedades and kilometrage imports."""

    def __init__(
        self,
        novedad_importer=None,
        kilometrage_importer=None,
    ) -> None:
        if novedad_importer is None or kilometrage_importer is None:
            from apps.tickets.infrastructure.services.legacy_kilometrage_importer import (
                LegacyKilometrageImporter,
            )
            from apps.tickets.infrastructure.services.legacy_novedad_importer import (
                LegacyNovedadImporter,
            )

            novedad_importer = novedad_importer or LegacyNovedadImporter()
            kilometrage_importer = kilometrage_importer or LegacyKilometrageImporter()

        self._novedad_importer = novedad_importer
        self._kilometrage_importer = kilometrage_importer

    def run(
        self,
        base_path: Path | None = None,
        full: bool = False,
        dry_run: bool = False,
    ) -> LegacySyncResult:
        """Execute the sync pipeline synchronously."""

        if base_path:
            resolved_path = Path(base_path)
        else:
            configured_path = getattr(settings, "LEGACY_DATA_PATH", "")
            resolved_path = Path(configured_path) if configured_path else None
        if base_path and resolved_path and not resolved_path.exists():
            raise ValueError(f"Legacy path does not exist: {resolved_path}")

        start = perf_counter()
        novedades_locs = self._novedad_importer.import_detenciones(
            base_path=resolved_path,
            dry_run=dry_run,
            raise_on_missing=True,
        )
        novedades_ccrr = self._novedad_importer.import_detenciones_ccrr(
            base_path=resolved_path,
            dry_run=dry_run,
            raise_on_missing=True,
        )
        novedades = self._merge_stats(novedades_locs, novedades_ccrr)
        kilometrage = self._kilometrage_importer.import_all(
            base_path=resolved_path,
            full=full,
            dry_run=dry_run,
            raise_on_missing=True,
        )
        duration_seconds = perf_counter() - start

        return LegacySyncResult(
            novedades=novedades,
            kilometrage=kilometrage,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _merge_stats(first: SyncStats, second: SyncStats) -> SyncStats:
        return SyncStats(
            processed=first.processed + second.processed,
            inserted=first.inserted + second.inserted,
            skipped_old=first.skipped_old + second.skipped_old,
            duplicates=first.duplicates + second.duplicates,
            invalid=first.invalid + second.invalid,
        )
