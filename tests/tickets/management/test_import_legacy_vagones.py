"""Tests para import_legacy_data --vagones."""

import pytest

from apps.tickets.management.commands.import_legacy_data import Command
from apps.tickets.models import (
    BrandModel,
    MaintenanceUnitModel,
    WagonModel,
    WagonTypeModel,
)


@pytest.mark.django_db
def test_import_vagones_creates_wagon_units(tmp_path):
    """Importa Vagones.txt y crea unidades de carga."""
    context_dir = tmp_path / "context" / "db-legacy" / "Iniciales"
    context_dir.mkdir(parents=True)

    vagones_txt = (
        "Coche,Tipo,Clase\n"
        "6046,Vagon,Automovilera\n"
        "977942,Vagon,Tolva (Hopper)\n"
        "999999,Vagon,Desconocido\n"
    )
    (context_dir / "Vagones.txt").write_text(vagones_txt, encoding="latin-1")

    command = Command()
    command.import_vagones(tmp_path / "context" / "db-legacy")

    assert MaintenanceUnitModel.objects.count() == 3
    assert WagonModel.objects.count() == 3
    assert BrandModel.objects.filter(code="Carga").exists()
    assert WagonTypeModel.objects.filter(code="HOPPER").exists()
    assert WagonTypeModel.objects.filter(code="VAGON").exists()

    unit = MaintenanceUnitModel.objects.get(number="6046")
    assert unit.unit_type == MaintenanceUnitModel.UnitType.WAGON
    assert unit.rolling_stock_category == MaintenanceUnitModel.Category.CARGO

    wagon_unknown = WagonModel.objects.get(maintenance_unit__number="999999")
    assert wagon_unknown.legacy_class == "Desconocido"
    assert wagon_unknown.wagon_type.code == "VAGON"
