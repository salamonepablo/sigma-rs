"""Find and remove duplicate railcar maintenance units that have no associated records."""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand

from apps.tickets.infrastructure.models import (
    KilometrageRecordModel,
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
    RailcarModel,
    TicketModel,
    UnitMaintenanceSnapshotModel,
)


def _normalize(number: str) -> str:
    """Strip U / FU prefix and return the bare numeric part."""
    return re.sub(r"^F?U", "", number.strip().upper())


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


def _has_any_reference(counts: dict[str, int]) -> bool:
    return any(v > 0 for v in counts.values())


class Command(BaseCommand):
    """Detect and optionally delete railcar units that are duplicates with no data."""

    help = (
        "Find railcar units duplicated by U/FU prefix and delete those with no "
        "associated records. Run without --execute to preview only."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete the empty duplicates (default: dry-run preview only)",
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
        has_conflict: list[tuple[str, list[MaintenanceUnitModel]]] = []

        for key, group in sorted(duplicates.items()):
            self.stdout.write(f"\n{'─' * 60}")
            self.stdout.write(f"  Grupo: {key!r}  ({len(group)} unidades)")
            refs_by_unit = {}
            for unit in group:
                refs = _count_references(unit)
                refs_by_unit[unit.pk] = refs
                ref_summary = (
                    "  ".join(f"{k}={v}" for k, v in refs.items() if v > 0)
                    or "SIN DATOS"
                )
                marker = "✗ VACÍO" if not _has_any_reference(refs) else "✓ CON DATOS"
                self.stdout.write(
                    f"    [{marker}]  {unit.number!r:15s}  pk={unit.pk}  → {ref_summary}"
                )

            empty = [u for u in group if not _has_any_reference(refs_by_unit[u.pk])]
            with_data = [u for u in group if _has_any_reference(refs_by_unit[u.pk])]

            if len(empty) == len(group):
                # All empty — keep the one without prefix, delete the rest
                bare = sorted(empty, key=lambda u: len(u.number))[0]
                to_drop = [u for u in empty if u.pk != bare.pk]
                self.stdout.write(
                    f"    → Todos vacíos. Se conserva {bare.number!r}, "
                    f"se elimina: {[u.number for u in to_drop]}"
                )
                to_delete.extend(to_drop)
            elif not with_data:
                # Shouldn't happen, guard anyway
                pass
            elif len(empty) > 0:
                self.stdout.write(
                    f"    → Se puede eliminar: {[u.number for u in empty]}"
                )
                to_delete.extend(empty)
            else:
                self.stdout.write(
                    "    ⚠ Todos tienen datos — no se puede eliminar ninguno automáticamente."
                )
                has_conflict.append((key, group))

        self.stdout.write(f"\n{'═' * 60}")
        self.stdout.write("Resumen:")
        self.stdout.write(f"  Grupos duplicados:    {len(duplicates)}")
        self.stdout.write(f"  Unidades a eliminar:  {len(to_delete)}")
        self.stdout.write(f"  Conflictos (manual):  {len(has_conflict)}")

        if has_conflict:
            self.stdout.write(
                "\n⚠  Grupos con datos en ambas unidades (requieren revisión manual):"
            )
            for key, group in has_conflict:
                self.stdout.write(f"    {key}: {[u.number for u in group]}")

        if not to_delete:
            self.stdout.write("\nNada para eliminar.")
            return

        self.stdout.write(f"\nUnidades a eliminar: {[u.number for u in to_delete]}")

        if not execute:
            self.stdout.write(
                "\n[DRY-RUN] Agregá --execute para eliminar las unidades vacías."
            )
            return

        deleted = 0
        for unit in to_delete:
            self.stdout.write(f"  Eliminando {unit.number!r} (pk={unit.pk})...")
            unit.delete()
            deleted += 1

        self.stdout.write(f"\n✓ {deleted} unidad(es) eliminada(s).")
