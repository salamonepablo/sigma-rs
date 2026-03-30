"""Seed maintenance cycles for wagons."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.tickets.infrastructure.models import BrandModel, MaintenanceCycleModel


class Command(BaseCommand):
    """Insert or replace wagon maintenance cycles (AL/REV/A/B)."""

    help = "Seed wagon maintenance cycles for brand Carga"

    def add_arguments(self, parser):
        parser.add_argument("--al", type=int, help="Trigger value for AL")
        parser.add_argument("--rev", type=int, help="Trigger value for REV")
        parser.add_argument("--a", type=int, help="Trigger value for A")
        parser.add_argument("--b", type=int, help="Trigger value for B")
        parser.add_argument(
            "--trigger-type",
            default="time",
            help="Trigger type (default: time)",
        )
        parser.add_argument(
            "--trigger-unit",
            default="month",
            help="Trigger unit (default: month)",
        )
        parser.add_argument(
            "--brand",
            default="Carga",
            help="Brand code for wagons (default: Carga)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing changes",
        )

    def handle(self, *args, **options):
        trigger_values = {
            "AL": options.get("al"),
            "REV": options.get("rev"),
            "A": options.get("a"),
            "B": options.get("b"),
        }
        if any(value is None for value in trigger_values.values()):
            self.stdout.write(
                self.style.ERROR(
                    "Missing trigger values. Provide --al, --rev, --a, and --b."
                )
            )
            return

        trigger_type = options["trigger_type"].strip() or "time"
        trigger_unit = options["trigger_unit"].strip() or "month"
        brand_code = options["brand"].strip() or "Carga"
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        brand, created = BrandModel.objects.get_or_create(
            code=brand_code,
            defaults={"name": brand_code, "full_name": "Vagones de Carga"},
        )
        if created:
            self.stdout.write(f"Created brand: {brand.code}")

        cycles = [
            ("AL", "Alistamiento"),
            ("REV", "Revision"),
            ("A", "Revision A"),
            ("B", "Revision B"),
        ]

        created_count = 0
        updated_count = 0
        removed_count = 0

        for code, name in cycles:
            if dry_run:
                created_count += 1
                continue

            with transaction.atomic():
                existing = MaintenanceCycleModel.objects.filter(
                    rolling_stock_type="vagon",
                    brand=brand,
                    model__isnull=True,
                    intervention_code=code,
                )
                if existing.count() > 1:
                    removed_count += existing.count() - 1
                    existing.exclude(pk=existing.first().pk).delete()

                cycle = existing.first()
                if cycle:
                    cycle.trigger_value = trigger_values[code]
                    cycle.intervention_name = name
                    cycle.trigger_type = trigger_type
                    cycle.trigger_unit = trigger_unit
                    cycle.is_active = True
                    cycle.save(
                        update_fields=[
                            "trigger_value",
                            "intervention_name",
                            "trigger_type",
                            "trigger_unit",
                            "is_active",
                        ]
                    )
                    updated_count += 1
                else:
                    MaintenanceCycleModel.objects.create(
                        rolling_stock_type="vagon",
                        brand=brand,
                        model=None,
                        intervention_code=code,
                        intervention_name=name,
                        trigger_type=trigger_type,
                        trigger_value=trigger_values[code],
                        trigger_unit=trigger_unit,
                        is_active=True,
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Wagon cycles seed complete: "
                f"{created_count} created, {updated_count} updated, {removed_count} removed"
            )
        )
