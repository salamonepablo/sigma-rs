"""Run novedades + kilometrage legacy sync in one command."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tickets.application.use_cases.legacy_sync_use_case import LegacySyncUseCase


class Command(BaseCommand):
    """Execute the combined legacy sync pipeline."""

    help = "Sync novedades and kilometrage from legacy TXT exports"
    DEFAULT_PATH = Path(settings.LEGACY_DATA_PATH)

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
            help="Import all kilometrage records (still ignores duplicates)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without writing",
        )

    def handle(self, *args, **options):
        base_path = Path(options["path"]) if options["path"] else self.DEFAULT_PATH
        if not base_path.exists():
            raise CommandError(f"Path does not exist: {base_path}")

        use_case = LegacySyncUseCase()
        result = use_case.run(
            base_path=base_path,
            full=options["full"],
            dry_run=options["dry_run"],
        )

        self.stdout.write(
            "Novedades: {inserted} inserted, {duplicates} duplicates, {invalid} invalid".format(
                inserted=result.novedades.inserted,
                duplicates=result.novedades.duplicates,
                invalid=result.novedades.invalid,
            )
        )
        self.stdout.write(
            "Kilometrage: {inserted} inserted, {skipped_old} skipped_old, {invalid} invalid".format(
                inserted=result.kilometrage.inserted,
                skipped_old=result.kilometrage.skipped_old,
                invalid=result.kilometrage.invalid,
            )
        )
        self.stdout.write(
            "Duration: {seconds:.2f}s".format(seconds=result.duration_seconds)
        )
