"""Backfill legacy codes for novedades."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.tickets.models import NovedadModel


class Command(BaseCommand):
    """Fill missing legacy codes from related fields."""

    help = "Backfill legacy_unit_code/intervencion/lugar when they are null."

    SPECIAL_UNIT_CODE = "CKG8G0013"
    SPECIAL_LUGAR_CODE = 3105
    SPECIAL_INTERVENCION_CODE = "360K"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without writing to the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be saved"))

        filters = (
            Q(legacy_unit_code__isnull=True, maintenance_unit__isnull=False)
            | Q(legacy_intervencion_codigo__isnull=True, intervencion__isnull=False)
            | Q(legacy_lugar_codigo__isnull=True, lugar__isnull=False)
            | Q(
                legacy_unit_code__isnull=True,
                maintenance_unit__number=self.SPECIAL_UNIT_CODE,
            )
            | Q(
                legacy_intervencion_codigo__isnull=True,
                intervencion__codigo=self.SPECIAL_INTERVENCION_CODE,
            )
            | Q(
                legacy_lugar_codigo__isnull=True,
                lugar__codigo=self.SPECIAL_LUGAR_CODE,
            )
        )

        queryset = (
            NovedadModel.objects.select_related(
                "maintenance_unit",
                "intervencion",
                "lugar",
            )
            .filter(filters)
            .distinct()
        )

        updated: list[NovedadModel] = []
        unit_updates = 0
        interv_updates = 0
        lugar_updates = 0

        for novedad in queryset:
            changed = False
            if novedad.legacy_unit_code is None and novedad.maintenance_unit:
                novedad.legacy_unit_code = novedad.maintenance_unit.number
                unit_updates += 1
                changed = True
            if novedad.legacy_intervencion_codigo is None and novedad.intervencion:
                novedad.legacy_intervencion_codigo = novedad.intervencion.codigo
                interv_updates += 1
                changed = True
            if novedad.legacy_lugar_codigo is None and novedad.lugar:
                novedad.legacy_lugar_codigo = novedad.lugar.codigo
                lugar_updates += 1
                changed = True

            if changed:
                updated.append(novedad)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Would update {rows} records "
                    "(legacy_unit_code: {units}, legacy_intervencion_codigo: {intervs}, "
                    "legacy_lugar_codigo: {lugares}).".format(
                        rows=len(updated),
                        units=unit_updates,
                        intervs=interv_updates,
                        lugares=lugar_updates,
                    )
                )
            )
            return

        if not updated:
            self.stdout.write(self.style.SUCCESS("No records required backfill."))
            return

        with transaction.atomic():
            NovedadModel.objects.bulk_update(
                updated,
                [
                    "legacy_unit_code",
                    "legacy_intervencion_codigo",
                    "legacy_lugar_codigo",
                ],
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Updated {rows} records "
                "(legacy_unit_code: {units}, legacy_intervencion_codigo: {intervs}, "
                "legacy_lugar_codigo: {lugares}).".format(
                    rows=len(updated),
                    units=unit_updates,
                    intervs=interv_updates,
                    lugares=lugar_updates,
                )
            )
        )
