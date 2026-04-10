"""Run novedades + kilometrage Access sync in one command."""

from __future__ import annotations

from pathlib import Path

from datetime import date, datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tickets.application.use_cases.access_sync_use_case import (
    AccessSyncConfig,
    AccessSyncUseCase,
)


class Command(BaseCommand):
    """Execute the combined legacy sync pipeline."""

    help = "Sync novedades and kilometrage from Access databases"
    DEFAULT_BASELOCS_PATH = getattr(settings, "ACCESS_BASELOCS_PATH", "")
    DEFAULT_BASECCRR_PATH = getattr(settings, "ACCESS_BASECCRR_PATH", "")
    DEFAULT_SCRIPT = getattr(
        settings, "ACCESS_EXTRACTOR_SCRIPT", "extractor_access.ps1"
    )
    DEFAULT_POWERSHELL = getattr(
        settings,
        "ACCESS_POWERSHELL_PATH",
        r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe",
    )
    DEFAULT_PASSWORD = getattr(settings, "ACCESS_DB_PASSWORD", "")

    def add_arguments(self, parser):
        parser.add_argument(
            "--baselocs-path",
            type=str,
            default=self.DEFAULT_BASELOCS_PATH,
            help="Path to baselocs.mdb",
        )
        parser.add_argument(
            "--baseccrr-path",
            type=str,
            default=self.DEFAULT_BASECCRR_PATH,
            help="Path to baseCCRR.mdb",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Import all records (still ignores duplicates)",
        )
        parser.add_argument(
            "--since-date",
            type=str,
            default=None,
            help="Override last date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--db-password",
            type=str,
            default=self.DEFAULT_PASSWORD,
            help="Access database password",
        )
        parser.add_argument(
            "--script-path",
            type=str,
            default=self.DEFAULT_SCRIPT,
            help="Path to extractor_access.ps1",
        )
        parser.add_argument(
            "--powershell",
            type=str,
            default=self.DEFAULT_POWERSHELL,
            help="Path to 32-bit PowerShell executable",
        )
        parser.add_argument(
            "--progress-every",
            type=int,
            default=500,
            help="Log progress every N records (0 disables)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without writing",
        )

    def handle(self, *args, **options):
        baselocs_path = (
            Path(options["baselocs_path"]) if options["baselocs_path"] else None
        )
        baseccrr_path = (
            Path(options["baseccrr_path"]) if options["baseccrr_path"] else None
        )
        if not baselocs_path or not baselocs_path.exists():
            raise CommandError(f"baselocs.mdb path does not exist: {baselocs_path}")
        if not baseccrr_path or not baseccrr_path.exists():
            raise CommandError(f"baseCCRR.mdb path does not exist: {baseccrr_path}")

        since_date = None
        if options["full"]:
            since_date = date(1900, 1, 1)
        elif options["since_date"]:
            since_date = datetime.strptime(options["since_date"], "%Y-%m-%d").date()

        config = AccessSyncConfig(
            baselocs_path=baselocs_path,
            baseccrr_path=baseccrr_path,
            db_password=options["db_password"] or None,
            script_path=Path(options["script_path"]),
            powershell_path=Path(options["powershell"]),
        )
        use_case = AccessSyncUseCase(config=config)
        result = use_case.run(
            since_date=since_date,
            dry_run=options["dry_run"],
            progress_every=options["progress_every"],
            stdout_writer=self.stdout.write,
            stderr_writer=self.stderr.write,
        )

        self.stdout.write("Resumen final")
        self.stdout.write(
            "Novedades: {inserted} inserted, {duplicates} duplicates, {invalid} invalid".format(
                inserted=result.novedades.inserted,
                duplicates=result.novedades.duplicates,
                invalid=result.novedades.invalid,
            )
        )
        self.stdout.write(
            "Kilometrage: {inserted} inserted, {duplicates} duplicates, {invalid} invalid".format(
                inserted=result.kilometrage.inserted,
                duplicates=result.kilometrage.duplicates,
                invalid=result.kilometrage.invalid,
            )
        )
        self.stdout.write(
            "Duration: {seconds:.2f}s".format(seconds=result.duration_seconds)
        )
