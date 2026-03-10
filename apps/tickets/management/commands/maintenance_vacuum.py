"""Run VACUUM/ANALYZE for SQLite database."""

from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Compact and analyze the SQLite database."""

    help = "Run VACUUM/ANALYZE on the SQLite database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--analyze",
            action="store_true",
            help="Run ANALYZE after VACUUM",
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get("default", {})
        if db_settings.get("ENGINE") != "django.db.backends.sqlite3":
            self.stdout.write("Skipping: database engine is not SQLite.")
            return

        db_path = Path(db_settings.get("NAME", ""))
        size_before = self._get_size(db_path)
        self.stdout.write(f"Running VACUUM on {db_path}...")
        with connection.cursor() as cursor:
            cursor.execute("VACUUM")

        if options.get("analyze"):
            self.stdout.write("Running ANALYZE...")
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE")

        size_after = self._get_size(db_path)
        if size_before is not None and size_after is not None:
            self.stdout.write(
                "Size before: {before} MB | after: {after} MB".format(
                    before=self._to_mb(size_before),
                    after=self._to_mb(size_after),
                )
            )

    @staticmethod
    def _get_size(path: Path) -> int | None:
        if not path or not path.exists():
            return None
        return os.path.getsize(path)

    @staticmethod
    def _to_mb(size_bytes: int) -> str:
        return f"{size_bytes / (1024 * 1024):.2f}"
