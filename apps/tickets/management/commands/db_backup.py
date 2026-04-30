"""Create SQLite backups for the default Django database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    """Create a consistent SQLite backup using sqlite3 backup API."""

    help = "Create a consistent backup of the SQLite default database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Output directory for backup files",
        )
        parser.add_argument(
            "--retention-days",
            type=int,
            default=None,
            help="Delete backup files older than this amount of days",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="app",
            help="Backup filename prefix",
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get("default", {})
        if db_settings.get("ENGINE") != "django.db.backends.sqlite3":
            self.stdout.write("Skipping: database engine is not SQLite.")
            return

        output_dir = self._get_output_dir(options.get("output_dir"))
        output_dir.mkdir(parents=True, exist_ok=True)

        prefix = options.get("prefix") or "app"
        backup_path = output_dir / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.db"

        source_connection = connections["default"]
        source_connection.ensure_connection()
        sqlite_connection = source_connection.connection
        if sqlite_connection is None:
            raise RuntimeError("Could not establish SQLite connection.")

        with sqlite3.connect(backup_path) as destination_connection:
            sqlite_connection.backup(destination_connection)

        deleted_count = self._delete_old_backups(
            output_dir=output_dir,
            prefix=prefix,
            retention_days=options.get("retention_days"),
        )

        self.stdout.write(f"Deleted backups: {deleted_count}")
        self.stdout.write(f"Backup created: {backup_path}")

    @staticmethod
    def _get_output_dir(output_dir_option: str | None) -> Path:
        if output_dir_option:
            return Path(output_dir_option)
        return Path(settings.BASE_DIR) / "db" / "backups"

    @staticmethod
    def _delete_old_backups(
        *,
        output_dir: Path,
        prefix: str,
        retention_days: int | None,
    ) -> int:
        if retention_days is None:
            return 0

        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        for backup_file in output_dir.glob(f"{prefix}_*.db"):
            modified_at = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if modified_at >= cutoff:
                continue
            backup_file.unlink(missing_ok=True)
            deleted_count += 1

        return deleted_count
