"""Legacy kilometrage importer extracted from management command."""

from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db.models import Max

from apps.tickets.application.use_cases.legacy_sync_use_case import SyncStats
from apps.tickets.models import KilometrageRecordModel, MaintenanceUnitModel


class LegacyKilometrageImporter:
    """Import kilometrage records from legacy TXT exports."""

    DEFAULT_PATH = Path("context/db-legacy")
    DELIMITER = ";"
    FILE_SPECS = [
        ("Kilometraje_Locs.txt", "Locs"),
        ("Kilometraje_CCRR.txt", "Coche"),
    ]
    BATCH_SIZE = 1000

    def import_all(
        self,
        base_path: Path | None = None,
        full: bool = False,
        dry_run: bool = False,
        raise_on_missing: bool = False,
    ) -> SyncStats:
        resolved_path = base_path or self.DEFAULT_PATH
        unit_id_by_number = {
            number.upper(): unit_id
            for number, unit_id in MaintenanceUnitModel.objects.values_list(
                "number", "id"
            )
        }

        latest_by_unit = {}
        if not full:
            latest_by_unit = {
                row["unit_number"].upper(): row["last_date"]
                for row in KilometrageRecordModel.objects.values(
                    "unit_number"
                ).annotate(last_date=Max("record_date"))
            }

        aggregated = SyncStats(
            processed=0,
            inserted=0,
            skipped_old=0,
            duplicates=0,
            invalid=0,
        )
        for file_name, unit_field in self.FILE_SPECS:
            stats = self._import_file(
                resolved_path / file_name,
                unit_field,
                unit_id_by_number,
                latest_by_unit,
                full,
                dry_run,
                raise_on_missing,
            )
            aggregated = self._merge_stats(aggregated, stats)

        return aggregated

    def _import_file(
        self,
        file_path: Path,
        unit_field: str,
        unit_id_by_number: dict[str, str],
        latest_by_unit: dict[str, date],
        full_import: bool,
        dry_run: bool,
        raise_on_missing: bool,
    ) -> SyncStats:
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

        processed = 0
        inserted = 0
        skipped_old = 0
        invalid = 0
        batch = []

        with open(file_path, encoding="latin-1") as handle:
            reader = csv.DictReader(handle, delimiter=self.DELIMITER)
            for row in reader:
                processed += 1
                unit_number = (row.get(unit_field) or "").strip().upper()
                if not unit_number:
                    invalid += 1
                    continue

                parsed_date = self._parse_date((row.get("Fecha") or "").strip())
                if not parsed_date:
                    invalid += 1
                    continue

                raw_km = (row.get("Kms_diario") or "").strip()
                if raw_km:
                    raw_km = raw_km.replace(",", ".")
                try:
                    km_value = Decimal(raw_km)
                except (InvalidOperation, ValueError):
                    invalid += 1
                    continue

                if not full_import:
                    last_date = latest_by_unit.get(unit_number)
                    if last_date and parsed_date <= last_date:
                        skipped_old += 1
                        continue

                unit_id = unit_id_by_number.get(unit_number)
                batch.append(
                    KilometrageRecordModel(
                        maintenance_unit_id=unit_id,
                        unit_number=unit_number,
                        record_date=parsed_date,
                        km_value=km_value,
                        source="legacy_csv",
                    )
                )

                if len(batch) >= self.BATCH_SIZE:
                    inserted += self._flush_batch(batch, dry_run)
                    batch = []

        if batch:
            inserted += self._flush_batch(batch, dry_run)

        return SyncStats(
            processed=processed,
            inserted=inserted,
            skipped_old=skipped_old,
            duplicates=0,
            invalid=invalid,
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
    def _flush_batch(batch, dry_run: bool) -> int:
        if not batch:
            return 0

        unit_numbers = {row.unit_number for row in batch}
        record_dates = {row.record_date for row in batch}
        existing = set(
            KilometrageRecordModel.objects.filter(
                unit_number__in=unit_numbers,
                record_date__in=record_dates,
            ).values_list("unit_number", "record_date")
        )
        new_batch = [
            row for row in batch if (row.unit_number, row.record_date) not in existing
        ]

        if dry_run:
            return len(new_batch)

        created = KilometrageRecordModel.objects.bulk_create(
            new_batch, ignore_conflicts=True
        )
        return len(created)

    @staticmethod
    def _merge_stats(left: SyncStats, right: SyncStats) -> SyncStats:
        return SyncStats(
            processed=left.processed + right.processed,
            inserted=left.inserted + right.inserted,
            skipped_old=left.skipped_old + right.skipped_old,
            duplicates=left.duplicates + right.duplicates,
            invalid=left.invalid + right.invalid,
        )
