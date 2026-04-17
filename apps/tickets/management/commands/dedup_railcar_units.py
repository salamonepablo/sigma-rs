"""Find and remove duplicate railcar maintenance units with U/FU prefix."""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.tickets.infrastructure.models import (
    KilometrageRecordModel,
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
    RailcarModel,
    TicketModel,
    UnitMaintenanceSnapshotModel,
)

# Fields considered "real data" — railcar and snapshot are structural and will
# be deleted together with the unit, so they don't count as a conflict blocker.
_DATA_FIELDS = ("novedades", "km", "entries", "tickets")


def _has_prefix(number: str) -> bool:
    return bool(re.match(r"^F?U\s+", number.strip().upper()))


def _normalize(number: str) -> str:
    """Strip U / FU prefix (with optional space) and return the bare number."""
    return re.sub(r"^F?U\s*", "", number.strip().upper())


def _count_references(unit: MaintenanceUnitModel) -> dict[str, int]:
    uid = unit.pk
    return {
        "railcar": RailcarModel.objects.filter(maintenance_unit_id=uid).count(),
        "novedades": NovedadModel.objects.filter(maintenance_unit_id=uid).count(),
        "km": KilometrageRecordModel.objects.filter(maintenance_unit_id=uid).count(),
        "entries": MaintenanceEntryModel.objects.filter(
            maintenance_unit_id=uid
        ).count(),
        "tickets": TicketModel.objects.filter(maintenance_unit_id=uid).count(),
        "snapshot": UnitMaintenanceSnapshotModel.objects.filter(
            maintenance_unit_id=uid
        ).count(),
    }


def _has_real_data(counts: dict[str, int]) -> bool:
    """Return True if the unit has novedades, km, entries or tickets."""
    return any(counts[f] > 0 for f in _DATA_FIELDS)


class Command(BaseCommand):
    """Detect and optionally delete prefixed (U/FU) duplicate railcar units.

    The prefixed units only carry a RailcarModel and a snapshot record —
    no novedades, km, entries or tickets. The command deletes those
    structural records and then the MaintenanceUnitModel itself.
    """

    help = (
        "Delete railcar units duplicated with U/FU prefix that carry no real data "
        "(novedades, km, entries, tickets). Run without --execute for a dry-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete (default: dry-run preview only)",
        )
        parser.add_argument(
            "--unit-type",
            type=str,
            default=MaintenanceUnitModel.UnitType.RAILCAR,
            help="Unit type to inspect (default: coche_remolcado)",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        unit_type = options["unit_type"]

        units = list(
            MaintenanceUnitModel.objects.filter(unit_type=unit_type).order_by("number")
        )

        # Group by normalized number
        groups: dict[str, list[MaintenanceUnitModel]] = {}
        for unit in units:
            key = _normalize(unit.number)
            groups.setdefault(key, []).append(unit)

        duplicates = {k: v for k, v in groups.items() if len(v) > 1}

        if not duplicates:
            self.stdout.write("No se encontraron duplicados.")
            return

        self.stdout.write(f"Encontrados {len(duplicates)} grupo(s) con duplicados:\n")

        to_delete: list[MaintenanceUnitModel] = []
        blocked: list[tuple[str, MaintenanceUnitModel]] = []

        for key, group in sorted(duplicates.items()):
            prefixed = [u for u in group if _has_prefix(u.number)]
            bare = [u for u in group if not _has_prefix(u.number)]

            self.stdout.write(f"\n{'─' * 60}")
            self.stdout.write(f"  Grupo: {key!r}  ({len(group)} unidades)")

            for unit in group:
                refs = _count_references(unit)
                ref_summary = (
                    "  ".join(f"{k}={v}" for k, v in refs.items() if v > 0)
                    or "SIN DATOS"
                )
                tag = "PREFIJADO" if _has_prefix(unit.number) else "BASE     "
                self.stdout.write(
                    f"    [{tag}]  {unit.number!r:15s}  pk={unit.pk}  → {ref_summary}"
                )

            # Validate each prefixed candidate
            for unit in prefixed:
                refs = _count_references(unit)
                if _has_real_data(refs):
                    self.stdout.write(
                        f"    ⚠ BLOQUEADO {unit.number!r} — tiene datos reales: "
                        + "  ".join(f"{k}={refs[k]}" for k in _DATA_FIELDS if refs[k])
                    )
                    blocked.append((key, unit))
                else:
                    self.stdout.write(
                        f"    → Eliminar {unit.number!r} "
                        f"(railcar={refs['railcar']} snapshot={refs['snapshot']})"
                    )
                    to_delete.append(unit)

            if not bare:
                self.stdout.write("    ⚠ No hay unidad base sin prefijo en este grupo.")

        self.stdout.write(f"\n{'═' * 60}")
        self.stdout.write("Resumen:")
        self.stdout.write(f"  Grupos duplicados:   {len(duplicates)}")
        self.stdout.write(f"  Unidades a eliminar: {len(to_delete)}")
        self.stdout.write(f"  Bloqueadas (manual): {len(blocked)}")

        if blocked:
            self.stdout.write("\n⚠  Prefijadas con datos reales (revisión manual):")
            for key, unit in blocked:
                self.stdout.write(f"    {key}: {unit.number!r}  pk={unit.pk}")

        if not to_delete:
            self.stdout.write("\nNada para eliminar.")
            return

        self.stdout.write(f"\nUnidades a eliminar: {[u.number for u in to_delete]}")

        if not execute:
            self.stdout.write("\n[DRY-RUN] Agregá --execute para eliminar.")
            return

        deleted = 0
        with transaction.atomic():
            for unit in to_delete:
                self.stdout.write(f"  Eliminando {unit.number!r} (pk={unit.pk})...")
                # Cascade: RailcarModel and UnitMaintenanceSnapshotModel will be
                # deleted via on_delete=CASCADE / SET_NULL on the FK.
                unit.delete()
                deleted += 1

        self.stdout.write(f"\n✓ {deleted} unidad(es) eliminada(s).")
