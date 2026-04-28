"""Access novedad importer using PowerShell extractor."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from django.db.models import Max

from apps.tickets.application.use_cases.legacy_sync_use_case import SyncStats
from apps.tickets.infrastructure.services.access_extractor import AccessExtractor
from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)


@dataclass(frozen=True)
class AccessNovedadSource:
    db_path: Path
    unit_field: str


@dataclass(frozen=True)
class _NovedadRow:
    unit_code: str
    fecha_desde: date
    fecha_hasta: date | None
    fecha_estimada: date | None
    intervencion_codigo: str
    lugar_codigo: int | None
    observaciones: str | None


class AccessNovedadImporter:
    """Import detenciones from Access databases."""

    TABLE_NAME = "Detenciones"
    BATCH_SIZE = 5000

    def __init__(self, extractor: AccessExtractor) -> None:
        self._extractor = extractor

    def import_all(
        self,
        baselocs: AccessNovedadSource | None,
        baseccrr: AccessNovedadSource | None,
        db_password: str | None = None,
        since_date: date | None = None,
        dry_run: bool = False,
        progress_every: int = 5000,
        skip_count: bool = True,
    ) -> SyncStats:
        resolved_since = since_date or self._resolve_last_date()
        aggregated = SyncStats(
            processed=0,
            inserted=0,
            skipped_old=0,
            duplicates=0,
            invalid=0,
        )

        lugares_by_codigo = {
            lugar.codigo: lugar.id for lugar in LugarModel.objects.all()
        }
        units_by_number = {
            unit.number.upper(): unit.id for unit in MaintenanceUnitModel.objects.all()
        }
        intervenciones_by_codigo = {
            intervencion.codigo: intervencion.id
            for intervencion in IntervencionTipoModel.objects.all()
        }

        for source in (baselocs, baseccrr):
            if source is None:
                continue
            source_label = self._source_label(source)
            records = self._extractor.extract(
                db_path=source.db_path,
                table=self.TABLE_NAME,
                unit_field=source.unit_field,
                since_date=resolved_since,
                db_password=db_password,
                progress_every=progress_every,
                skip_count=skip_count,
                source_label=source_label,
            )
            stats = self._import_records(
                records,
                lugares_by_codigo=lugares_by_codigo,
                units_by_number=units_by_number,
                intervenciones_by_codigo=intervenciones_by_codigo,
                dry_run=dry_run,
            )
            aggregated = self._merge_stats(aggregated, stats)

        return aggregated

    def _resolve_last_date(self) -> date:
        last = NovedadModel.objects.filter(is_legacy=True).aggregate(
            Max("fecha_desde")
        )["fecha_desde__max"]
        return last or date(1990, 1, 1)

    def _import_records(
        self,
        records: list[dict],
        lugares_by_codigo: dict[int, int],
        units_by_number: dict[str, uuid.UUID],
        intervenciones_by_codigo: dict[str, int],
        dry_run: bool,
    ) -> SyncStats:
        processed = 0
        inserted = 0
        duplicates = 0
        invalid = 0
        batch: list[NovedadModel] = []

        for record in records:
            processed += 1
            parsed = self._parse_row(record)
            if not parsed:
                invalid += 1
                continue

            intervencion_id = (
                intervenciones_by_codigo.get(parsed.intervencion_codigo)
                if parsed.intervencion_codigo
                else None
            )
            legacy_intervencion_codigo = parsed.intervencion_codigo

            maintenance_unit_id = units_by_number.get(parsed.unit_code)
            legacy_unit_code = parsed.unit_code

            lugar_id = None
            legacy_lugar_codigo = None
            if parsed.lugar_codigo is not None:
                lugar_id = lugares_by_codigo.get(parsed.lugar_codigo)
                legacy_lugar_codigo = parsed.lugar_codigo

            if dry_run:
                inserted += 1
                continue

            batch.append(
                NovedadModel(
                    id=uuid.uuid4(),
                    maintenance_unit_id=maintenance_unit_id,
                    legacy_unit_code=legacy_unit_code,
                    fecha_desde=parsed.fecha_desde,
                    fecha_hasta=parsed.fecha_hasta,
                    fecha_estimada=parsed.fecha_estimada,
                    intervencion_id=intervencion_id,
                    legacy_intervencion_codigo=legacy_intervencion_codigo,
                    lugar_id=lugar_id,
                    legacy_lugar_codigo=legacy_lugar_codigo,
                    observaciones=parsed.observaciones,
                    is_legacy=True,
                )
            )

            if len(batch) >= self.BATCH_SIZE:
                created, skipped = self._flush_batch(batch)
                inserted += created
                duplicates += skipped
                batch = []

        if batch and not dry_run:
            created, skipped = self._flush_batch(batch)
            inserted += created
            duplicates += skipped

        return SyncStats(
            processed=processed,
            inserted=inserted,
            skipped_old=0,
            duplicates=duplicates,
            invalid=invalid,
        )

    def _parse_row(self, row: dict[str, object]) -> _NovedadRow | None:
        unit_code = self._normalize_code(row.get("Unidad"), upper=True)
        if not unit_code:
            return None

        fecha_desde = self._parse_date(str(row.get("Fecha_desde") or "").strip())
        if not fecha_desde:
            return None

        fecha_hasta = self._parse_date(str(row.get("Fecha_hasta") or "").strip())
        fecha_estimada = self._parse_date(str(row.get("Fecha_est") or "").strip())
        intervencion_codigo = self._normalize_code(row.get("Intervencion"), upper=True)
        lugar_codigo = self._parse_lugar_codigo(row.get("Lugar"))
        observaciones = str(row.get("Observaciones") or "").strip() or None

        return _NovedadRow(
            unit_code=unit_code,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            fecha_estimada=fecha_estimada,
            intervencion_codigo=intervencion_codigo,
            lugar_codigo=lugar_codigo,
            observaciones=observaciones,
        )

    @staticmethod
    def _normalize_code(value: object, *, upper: bool) -> str | None:
        text = str(value or "").strip()
        if not text:
            return None
        return text.upper() if upper else text

    @staticmethod
    def _parse_lugar_codigo(value: object) -> int | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            try:
                return int(float(text))
            except ValueError:
                return None

    @staticmethod
    def _parse_date(value: str) -> date | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_optional_date(value: date | None) -> date | None:
        return value or None

    @staticmethod
    def _flush_batch(batch: list[NovedadModel]) -> tuple[int, int]:
        created = NovedadModel.objects.bulk_create(batch, ignore_conflicts=True)
        inserted = len(created)
        return inserted, len(batch) - inserted

    @staticmethod
    def _merge_stats(first: SyncStats, second: SyncStats) -> SyncStats:
        return SyncStats(
            processed=first.processed + second.processed,
            inserted=first.inserted + second.inserted,
            skipped_old=first.skipped_old + second.skipped_old,
            duplicates=first.duplicates + second.duplicates,
            invalid=first.invalid + second.invalid,
        )

    @staticmethod
    def _source_label(source: AccessNovedadSource) -> str:
        if source.unit_field.strip().lower() == "locs":
            return "LOCS"
        return "CCRR"
