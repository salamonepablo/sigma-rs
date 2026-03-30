"""Migrate legacy railcars with wagon brand into wagons."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.tickets.infrastructure.models import (
    BrandModel,
    MaintenanceUnitModel,
    RailcarModel,
    WagonModel,
    WagonTypeModel,
)


class Command(BaseCommand):
    """Move misclassified railcars (wagons) into WagonModel."""

    help = "Move railcars with legacy wagon brand into wagons, updating unit_type and category."

    DEFAULT_LEGACY_BRANDS = ("Vagon", "VAGON")

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without writing changes",
        )
        parser.add_argument(
            "--legacy-brand",
            action="append",
            default=list(self.DEFAULT_LEGACY_BRANDS),
            help=("Legacy brand code or name to migrate. Can be used multiple times."),
        )
        parser.add_argument(
            "--target-brand",
            default="Carga",
            help="Target brand code to assign to wagons (default: Carga)",
        )
        parser.add_argument(
            "--wagon-type",
            default="VAGON",
            help="Wagon type code to assign (default: VAGON)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        legacy_brands = [b.strip() for b in options["legacy_brand"] if b.strip()]
        target_brand_code = options["target_brand"].strip() or "Carga"
        wagon_type_code = options["wagon_type"].strip() or "VAGON"

        if not legacy_brands:
            self.stdout.write(self.style.ERROR("No legacy brands provided"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        target_brand, brand_created = BrandModel.objects.get_or_create(
            code=target_brand_code,
            defaults={"name": target_brand_code, "full_name": "Vagones de Carga"},
        )
        if brand_created:
            self.stdout.write(f"Created brand: {target_brand.code}")

        wagon_type, type_created = WagonTypeModel.objects.get_or_create(
            code=wagon_type_code,
            defaults={"name": wagon_type_code.title()},
        )
        if type_created:
            self.stdout.write(f"Created wagon type: {wagon_type.code}")

        legacy_brand_qs = RailcarModel.objects.none()
        for legacy in legacy_brands:
            legacy_brand_qs = legacy_brand_qs | RailcarModel.objects.filter(
                brand__code__iexact=legacy
            )
            legacy_brand_qs = legacy_brand_qs | RailcarModel.objects.filter(
                brand__name__iexact=legacy
            )

        railcars = legacy_brand_qs.select_related(
            "maintenance_unit", "brand", "railcar_class"
        ).distinct()

        migrated = 0
        skipped_existing_wagon = 0
        errors = 0

        for railcar in railcars:
            maintenance_unit = railcar.maintenance_unit
            if not maintenance_unit:
                errors += 1
                self.stdout.write(
                    self.style.WARNING(f"Railcar {railcar.pk} missing maintenance unit")
                )
                continue

            if hasattr(maintenance_unit, "wagon"):
                skipped_existing_wagon += 1
                continue

            legacy_class = None
            if railcar.railcar_class_id:
                legacy_class = railcar.railcar_class.code

            if dry_run:
                migrated += 1
                continue

            try:
                with transaction.atomic():
                    maintenance_unit.unit_type = MaintenanceUnitModel.UnitType.WAGON
                    maintenance_unit.rolling_stock_category = (
                        MaintenanceUnitModel.Category.CARGO
                    )
                    maintenance_unit.save(
                        update_fields=["unit_type", "rolling_stock_category"]
                    )

                    WagonModel.objects.create(
                        maintenance_unit=maintenance_unit,
                        brand=target_brand,
                        wagon_type=wagon_type,
                        legacy_class=legacy_class,
                    )
                    railcar.delete()
                    migrated += 1
            except Exception as exc:  # pragma: no cover - safety net
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed to migrate {railcar.pk}: {exc}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Railcar wagons migration complete: "
                f"{migrated} migrated, {skipped_existing_wagon} skipped, {errors} errors"
            )
        )
