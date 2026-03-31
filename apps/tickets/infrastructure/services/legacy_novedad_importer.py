"""Legacy novedad importer extracted from management commands."""

from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from apps.tickets.application.use_cases.legacy_sync_use_case import SyncStats
from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)


@dataclass(frozen=True)
class _NovedadRow:
    unit_code: str
    fecha_desde: date
    fecha_hasta: date | None
    fecha_estimada: date | None
    intervencion_codigo: str
    lugar_codigo: str
    observaciones: str | None


class LegacyNovedadImporter:
    """Import detenciones from legacy TXT exports."""

    DEFAULT_PATH = Path("context/db-legacy")
    BATCH_SIZE = 1000

    def import_detenciones(
        self,
        base_path: Path | None = None,
        dry_run: bool = False,
        raise_on_missing: bool = False,
    ) -> SyncStats:
        return self._import_file(
            base_path=base_path,
            file_name="Detenciones_Locs.txt",
            unit_field="Locs",
            dry_run=dry_run,
            raise_on_missing=raise_on_missing,
        )

    def import_detenciones_ccrr(
        self,
        base_path: Path | None = None,
        dry_run: bool = False,
        raise_on_missing: bool = False,
    ) -> SyncStats:
        return self._import_file(
            base_path=base_path,
            file_name="Detenciones_CCRR.txt",
            unit_field="Coche",
            dry_run=dry_run,
            raise_on_missing=raise_on_missing,
        )

    def _import_file(
        self,
        base_path: Path | None,
        file_name: str,
        unit_field: str,
        dry_run: bool,
        raise_on_missing: bool,
    ) -> SyncStats:
        resolved_path = base_path or self.DEFAULT_PATH
        file_path = resolved_path / file_name
        if not file_path.exists():
            if raise_on_missing:
                raise FileNotFoundError(f"File not found: {file_path}")
            return SyncStats(
                processed=0,
                inserted=0,
                skipped_old=0,
                duplicates=0,
                invalid=0,
            )

        lugares_by_codigo = {lugar.codigo: lugar for lugar in LugarModel.objects.all()}
        units_by_number = {u.number: u for u in MaintenanceUnitModel.objects.all()}
        intervenciones_by_codigo = {
            i.codigo: i for i in IntervencionTipoModel.objects.all()
        }

        existing_records = set()
        for nov in NovedadModel.objects.filter(is_legacy=True).values(
            "maintenance_unit__number",
            "legacy_unit_code",
            "fecha_desde",
            "fecha_hasta",
            "intervencion__codigo",
            "legacy_intervencion_codigo",
            "lugar__codigo",
            "legacy_lugar_codigo",
        ):
            unit_num = nov["maintenance_unit__number"] or nov["legacy_unit_code"]
            interv = nov["intervencion__codigo"] or nov["legacy_intervencion_codigo"]
            lugar = nov["lugar__codigo"] or nov["legacy_lugar_codigo"]
            fecha_hasta = self._normalize_optional_date(nov["fecha_hasta"])
            key = (unit_num, str(nov["fecha_desde"]), fecha_hasta, interv, str(lugar))
            existing_records.add(key)

        processed = 0
        inserted = 0
        duplicates = 0
        invalid = 0
        batch: list[NovedadModel] = []

        with open(file_path, "r", encoding="latin-1") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                processed += 1
                parsed = self._parse_row(row, unit_field)
                if not parsed:
                    invalid += 1
                    continue

                fecha_hasta_key = self._normalize_optional_date(parsed.fecha_hasta)
                dup_key = (
                    parsed.unit_code,
                    str(parsed.fecha_desde),
                    fecha_hasta_key,
                    parsed.intervencion_codigo,
                    parsed.lugar_codigo,
                )
                if dup_key in existing_records:
                    duplicates += 1
                    continue

                intervencion = intervenciones_by_codigo.get(parsed.intervencion_codigo)
                legacy_intervencion_codigo = (
                    parsed.intervencion_codigo if not intervencion else None
                )

                maintenance_unit = units_by_number.get(parsed.unit_code)
                legacy_unit_code = parsed.unit_code if not maintenance_unit else None

                lugar = None
                legacy_lugar_codigo = None
                if parsed.lugar_codigo:
                    try:
                        lugar_codigo = int(parsed.lugar_codigo)
                        lugar = lugares_by_codigo.get(lugar_codigo)
                        if not lugar:
                            legacy_lugar_codigo = lugar_codigo
                    except ValueError:
                        legacy_lugar_codigo = None

                if dry_run:
                    inserted += 1
                    existing_records.add(dup_key)
                    continue

                batch.append(
                    NovedadModel(
                        id=uuid.uuid4(),
                        maintenance_unit=maintenance_unit,
                        legacy_unit_code=legacy_unit_code,
                        fecha_desde=parsed.fecha_desde,
                        fecha_hasta=parsed.fecha_hasta,
                        fecha_estimada=parsed.fecha_estimada,
                        intervencion=intervencion,
                        legacy_intervencion_codigo=legacy_intervencion_codigo,
                        lugar=lugar,
                        legacy_lugar_codigo=legacy_lugar_codigo,
                        observaciones=parsed.observaciones,
                        is_legacy=True,
                    )
                )
                existing_records.add(dup_key)

                if len(batch) >= self.BATCH_SIZE:
                    inserted += self._flush_batch(batch)
                    batch = []

        if batch and not dry_run:
            inserted += self._flush_batch(batch)

        return SyncStats(
            processed=processed,
            inserted=inserted,
            skipped_old=0,
            duplicates=duplicates,
            invalid=invalid,
        )

    def _parse_row(self, row: dict[str, str], unit_field: str) -> _NovedadRow | None:
        unit_code = (row.get(unit_field) or "").strip()
        if not unit_code:
            return None

        fecha_desde = self._parse_date((row.get("Fecha_desde") or "").strip())
        if not fecha_desde:
            return None

        fecha_hasta = self._parse_date((row.get("Fecha_hasta") or "").strip())
        fecha_estimada = self._parse_date((row.get("Fecha_est") or "").strip())
        intervencion_codigo = (row.get("Intervencion") or "").strip()
        lugar_codigo = (row.get("Lugar") or "").strip()
        observaciones = (row.get("Observaciones") or "").strip() or None

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
    def _parse_date(value: str) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _normalize_optional_date(value: date | None) -> date | None:
        return value or None

    @staticmethod
    def _flush_batch(batch: list[NovedadModel]) -> int:
        created = NovedadModel.objects.bulk_create(batch)
        return len(created)
