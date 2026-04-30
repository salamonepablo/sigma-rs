"""Run SQLite integrity checks on the default Django database."""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    """Execute PRAGMA integrity_check/quick_check for SQLite."""

    help = "Run SQLite integrity checks on the default database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--quick",
            action="store_true",
            help="Run PRAGMA quick_check instead of integrity_check",
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get("default", {})
        if db_settings.get("ENGINE") != "django.db.backends.sqlite3":
            self.stdout.write("Skipping: database engine is not SQLite.")
            return

        pragma_name = "quick_check" if options.get("quick") else "integrity_check"
        with connections["default"].cursor() as cursor:
            cursor.execute(f"PRAGMA {pragma_name};")
            rows = cursor.fetchall()

        messages = [str(row[0]) for row in rows if row]
        if len(messages) == 1 and messages[0].lower() == "ok":
            self.stdout.write(f"SQLite {pragma_name}: ok")
            return

        details = ", ".join(messages) if messages else "No result returned"
        raise CommandError(f"SQLite {pragma_name} failed: {details}")
