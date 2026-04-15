"""Management command to build the km snapshot for maintenance units."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.tickets.infrastructure.services.unit_maintenance_snapshot_service import (
    UnitMaintenanceSnapshotService,
)


class Command(BaseCommand):
    """Build or refresh the UnitMaintenanceSnapshot table.

    Usage:
        python manage.py build_km_snapshot
        python manage.py build_km_snapshot --unit A710 --unit CKD8G0013
    """

    help = "Build or refresh the km snapshot for maintenance units"

    def add_arguments(self, parser):
        parser.add_argument(
            "--unit",
            dest="units",
            action="append",
            default=None,
            metavar="UNIT_NUMBER",
            help=(
                "Refresh only the specified unit (can be repeated for multiple units). "
                "Defaults to all units."
            ),
        )

    def handle(self, *args, **options):
        service = UnitMaintenanceSnapshotService()
        unit_numbers = options.get("units")

        if unit_numbers:
            self.stdout.write(f"Refreshing snapshot for: {', '.join(unit_numbers)}")
        else:
            self.stdout.write("Building km snapshot for all units...")

        processed = 0

        def on_progress(unit_number: str) -> None:
            nonlocal processed
            processed += 1
            if processed % 50 == 0:
                self.stdout.write(f"  {processed} units processed...")

        count = service.refresh_bulk(
            unit_numbers=unit_numbers,
            progress_callback=on_progress,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Done. {count} snapshot(s) built/refreshed.")
        )
