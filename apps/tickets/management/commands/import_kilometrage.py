"""Import kilometrage records from legacy TXT exports."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.tickets.infrastructure.services.legacy_kilometrage_importer import (
    LegacyKilometrageImporter,
)


class Command(BaseCommand):
    """Import kilometrage data from legacy exports."""

    help = "Import kilometrage data from legacy TXT exports"

    DEFAULT_PATH = Path("context/db-legacy")

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

        importer = LegacyKilometrageImporter()
        stats = importer.import_all(
            base_path=base_path,
            full=options["full"],
            dry_run=options["dry_run"],
            raise_on_missing=False,
        )
        self.stdout.write(
            "Kilometrage: imported {inserted}, processed {processed}, "
            "skipped_old {skipped_old}, invalid {invalid}".format(
                inserted=stats.inserted,
                processed=stats.processed,
                skipped_old=stats.skipped_old,
                invalid=stats.invalid,
            )
        )
