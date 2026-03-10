"""Import kilometrage records from legacy TXT exports."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Max

from apps.tickets.models import KilometrageRecordModel, MaintenanceUnitModel


class Command(BaseCommand):
    """Import kilometrage data from legacy exports."""

    help = "Import kilometrage data from legacy TXT exports"

    DEFAULT_PATH = Path("context/db-legacy")
    FILE_SPECS = [
        ("KilometrajeLocs.txt", "Locs"),
        ("Kilometraje_CCRR.txt", "Coche"),
    ]
    BATCH_SIZE = 1000

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=str(self.DEFAULT_PATH),
            help="Path to directory containing legacy data files",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Import all records (still ignores duplicates)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without writing",
        )

    def handle(self, *args, **options):
        base_path = Path(options["path"]) if options["path"] else self.DEFAULT_PATH
        if not base_path.exists():
            self.stderr.write(f"Path does not exist: {base_path}")
            return

        self.stdout.write(
            f"Importing kilometrage from {base_path} (full={options['full']})"
        )

        unit_id_by_number = {
            number.upper(): unit_id
            for number, unit_id in MaintenanceUnitModel.objects.values_list(
                "number", "id"
            )
        }

        latest_by_unit = {}
        if not options["full"]:
            latest_by_unit = {
                row["unit_number"].upper(): row["last_date"]
                for row in KilometrageRecordModel.objects.values(
                    "unit_number"
                ).annotate(last_date=Max("record_date"))
            }

        for file_name, unit_field in self.FILE_SPECS:
            self._import_file(
                base_path / file_name,
                unit_field,
                unit_id_by_number,
                latest_by_unit,
                options["full"],
                options["dry_run"],
            )

    def _import_file(
        self,
        file_path: Path,
        unit_field: str,
        unit_id_by_number: dict[str, str],
        latest_by_unit: dict[str, datetime.date],
        full_import: bool,
        dry_run: bool,
    ) -> None:
        if not file_path.exists():
            self.stdout.write(f"File not found: {file_path}")
            return

        self.stdout.write(f"Processing {file_path.name}...")
        processed = 0
        inserted = 0
        skipped_old = 0
        invalid = 0
        batch = []

        with open(file_path, encoding="latin-1") as handle:
            reader = csv.DictReader(handle)
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
                try:
                    km_value = int(float(raw_km))
                except ValueError:
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
                    self.stdout.write(
                        f"  Imported {inserted} rows (processed {processed})"
                    )

        if batch:
            inserted += self._flush_batch(batch, dry_run)

        self.stdout.write(
            "Finished {name}: imported {inserted}, processed {processed}, "
            "skipped_old {skipped_old}, invalid {invalid}".format(
                name=file_path.name,
                inserted=inserted,
                processed=processed,
                skipped_old=skipped_old,
                invalid=invalid,
            )
        )

    @staticmethod
    def _parse_date(value: str):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _flush_batch(batch, dry_run: bool) -> int:
        if dry_run:
            return len(batch)
        KilometrageRecordModel.objects.bulk_create(batch, ignore_conflicts=True)
        return len(batch)
