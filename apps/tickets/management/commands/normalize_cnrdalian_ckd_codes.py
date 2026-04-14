"""Normalize Dalian CNR brand and CKD model codes."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.tickets.infrastructure.models.reference import (
    BrandModel,
    LocomotiveModelModel,
)


class Command(BaseCommand):
    help = "Normalize Dalian CNR brand and CKD locomotive model codes"
    requires_system_checks = []
    requires_migrations_checks = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving",
        )
        parser.add_argument(
            "--brand-name",
            type=str,
            default="Dalian CNR",
            help="Target brand name to set",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        target_brand_name = options["brand_name"].strip()

        brand = self._resolve_brand(target_brand_name)
        if not brand:
            raise CommandError("No se encontro una marca CNR/Dalian para normalizar.")

        self.stdout.write(
            "Marca objetivo: {name} (id={id})".format(
                name=brand.name,
                id=brand.id,
            )
        )

        updates = []
        if brand.code != "CNR" or brand.name != target_brand_name:
            updates.append("brand")

        model_updates = self._normalize_models(
            brand=brand,
            dry_run=dry_run,
        )

        if dry_run:
            self.stdout.write(
                "DRY RUN - cambios: marca={brand}, modelos={models}".format(
                    brand="si" if updates else "no",
                    models=model_updates,
                )
            )
            return

        with transaction.atomic():
            if updates:
                brand.code = "CNR"
                brand.name = target_brand_name
                brand.full_name = target_brand_name
                brand.save(update_fields=["code", "name", "full_name", "updated_at"])

            self._normalize_models(brand=brand, dry_run=False)

        self.stdout.write(
            "Normalizacion completa. Marca actualizada: {brand}, modelos: {models}.".format(
                brand="si" if updates else "no",
                models=model_updates,
            )
        )

    def _resolve_brand(self, target_name: str) -> BrandModel | None:
        by_code = BrandModel.objects.filter(code__iexact="CNR")
        if by_code.count() == 1:
            return by_code.first()
        if by_code.count() > 1:
            raise CommandError("Hay mas de una marca con codigo CNR.")

        candidates = BrandModel.objects.filter(name__iregex=r"(cnr|dalian)").order_by(
            "name"
        )
        if candidates.count() == 1:
            return candidates.first()
        if candidates.count() > 1:
            names = ", ".join(candidates.values_list("name", flat=True))
            raise CommandError(
                "Hay multiples marcas CNR/Dalian: {names}. "
                "Ajusta manualmente y reintenta.".format(names=names)
            )
        return None

    def _normalize_models(self, brand: BrandModel, dry_run: bool) -> int:
        updates = 0
        updates += self._normalize_model_code(
            brand=brand,
            target="CKD8G",
            aliases=["8G", "CKD8G"],
            dry_run=dry_run,
        )
        updates += self._normalize_model_code(
            brand=brand,
            target="CKD8H",
            aliases=["8H", "CKD8H"],
            dry_run=dry_run,
        )
        return updates

    def _normalize_model_code(
        self,
        brand: BrandModel,
        target: str,
        aliases: list[str],
        dry_run: bool,
    ) -> int:
        alias_query = None
        for alias in aliases:
            alias_query = (
                (alias_query | self._q(alias))
                if alias_query is not None
                else self._q(alias)
            )
        matches = LocomotiveModelModel.objects.filter(alias_query)

        if matches.count() == 0:
            self.stdout.write(
                "No se encontro modelo {target} para marca {brand}.".format(
                    target=target,
                    brand=brand.name,
                )
            )
            return 0
        if matches.count() > 1:
            names = ", ".join(matches.values_list("name", flat=True))
            raise CommandError(
                "Hay multiples modelos para {target}: {names}.".format(
                    target=target,
                    names=names,
                )
            )

        model = matches.first()
        if model.code == target and model.name == target:
            return 0
        if not dry_run:
            model.code = target
            model.name = target
            model.brand = brand
            model.save(update_fields=["code", "name", "brand", "updated_at"])
        return 1

    @staticmethod
    def _q(alias: str):
        from django.db.models import Q

        return (
            Q(code__iexact=alias)
            | Q(name__iexact=alias)
            | Q(name__icontains=alias)
            | Q(code__icontains=alias)
        )
