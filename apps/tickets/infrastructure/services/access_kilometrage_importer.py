"""Access kilometrage importer using PowerShell extractor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db.models import Max

from apps.tickets.application.use_cases.legacy_sync_use_case import SyncStats
from apps.tickets.infrastructure.services.access_extractor import (
    AccessExtractor,
    AccessExtractorConfig,
)
from apps.tickets.models import KilometrageRecordModel, MaintenanceUnitModel


@dataclass(frozen=True)
class AccessKilometrageSource:
    db_path: Path
    unit_field: str
    source_label: str


class AccessKilometrageImporter:
    """Import kilometrage records from Access databases."""

    TABLE_NAME = "Kilometraje"
    BATCH_SIZE = 1000

    def __init__(
        self,
        extractor: AccessExtractor,
    ) -> None:
        self._extractor = extractor

    def import_all(
        self,
        baselocs: AccessKilometrageSource | None,
        baseccrr: AccessKilometrageSource | None,
        db_password: str | None = None,
        since_date: date | None = None,
        dry_run: bool = False,
        progress_every: int = 500,
    ) -> SyncStats:
        unit_id_by_number = {
            number.upper(): unit_id
            for number, unit_id in MaintenanceUnitModel.objects.values_list(
                "number", "id"
            )
        }
        aggregated = SyncStats(
            processed=0,
            inserted=0,
            skipped_old=0,
            duplicates=0,
            invalid=0,
        )

        for source in (baselocs, baseccrr):
            if source is None:
                continue
            source_label = source.source_label
            resolved_since = since_date or self._resolve_last_date(source_label)
            records = self._extractor.extract(
                db_path=source.db_path,
                table=self.TABLE_NAME,
                unit_field=source.unit_field,
                since_date=resolved_since,
                db_password=db_password,
                progress_every=progress_every,
                source_label=source_label,
            )
            stats = self._import_records(
                records,
                unit_id_by_number=unit_id_by_number,
                dry_run=dry_run,
                source_label=source_label,
            )
            aggregated = self._merge_stats(aggregated, stats)

        return aggregated

    def _resolve_last_date(self, source_label: str) -> date:
        last = (
            KilometrageRecordModel.objects.filter(source=source_label).aggregate(
                Max("record_date")
            )
        )["record_date__max"]
        return last or date(1990, 1, 1)

    def _import_records(
        self,
        records: list[dict],
        unit_id_by_number: dict[str, str],
        dry_run: bool,
        source_label: str,
    ) -> SyncStats:
        processed = 0
        inserted = 0
        duplicates = 0
        invalid = 0
        batch: list[KilometrageRecordModel] = []
        batch_invalid = 0

        def flush_batch() -> None:
            nonlocal batch, batch_invalid, inserted, duplicates, invalid
            if not batch and not batch_invalid:
                return
            created = 0
            skipped = 0
            if batch:
                created, skipped = self._flush_batch(batch, dry_run)
            inserted += created
            duplicates += skipped
            invalid += batch_invalid
            batch = []
            batch_invalid = 0

        for record in records:
            processed += 1
            unit = (record.get("Unidad") or "").strip().upper()
            record_date = self._parse_date(record.get("Fecha"))
            km_value = self._parse_decimal(record.get("Kilometros"))

            if not unit or record_date is None or km_value is None:
                batch_invalid += 1
                continue

            batch.append(
                KilometrageRecordModel(
                    maintenance_unit_id=unit_id_by_number.get(unit),
                    unit_number=unit,
                    record_date=record_date,
                    km_value=km_value,
                    source=source_label,
                )
            )

            if len(batch) >= self.BATCH_SIZE:
                flush_batch()

        flush_batch()

        return SyncStats(
            processed=processed,
            inserted=inserted,
            skipped_old=0,
            duplicates=duplicates,
            invalid=invalid,
        )

    @staticmethod
    def _flush_batch(
        batch: list[KilometrageRecordModel],
        dry_run: bool,
    ) -> tuple[int, int]:
        if dry_run:
            return len(batch), 0

        created = KilometrageRecordModel.objects.bulk_create(
            batch, ignore_conflicts=True
        )
        inserted = len(created)
        return inserted, len(batch) - inserted

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        value_str = str(value).strip()
        if not value_str:
            return None
        try:
            return datetime.fromisoformat(value_str).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value_str, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_decimal(value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        value_str = str(value).strip()
        if not value_str:
            return None
        value_str = value_str.replace(".", "").replace(",", ".")
        try:
            return Decimal(value_str)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _merge_stats(left: SyncStats, right: SyncStats) -> SyncStats:
        return SyncStats(
            processed=left.processed + right.processed,
            inserted=left.inserted + right.inserted,
            skipped_old=left.skipped_old + right.skipped_old,
            duplicates=left.duplicates + right.duplicates,
            invalid=left.invalid + right.invalid,
        )
