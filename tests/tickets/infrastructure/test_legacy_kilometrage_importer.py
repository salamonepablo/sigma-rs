"""Pruebas para el importador de kilometraje legacy."""

from datetime import date
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.services.legacy_kilometrage_importer import (
    LegacyKilometrageImporter,
)
from apps.tickets.models import KilometrageRecordModel, MaintenanceUnitModel


@pytest.mark.django_db
def test_import_kilometrage_skips_old(tmp_path):
    """Saltea registros antiguos cuando no se usa full."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A100",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    KilometrageRecordModel.objects.create(
        maintenance_unit=unit,
        unit_number="A100",
        record_date=date(2024, 1, 1),
        km_value=100,
        source="legacy_csv",
    )

    content = "Locs,Fecha,Kms_diario\n" "A100,01/01/2024,120\n" "A100,02/01/2024,150\n"
    (base_path / "Kilometraje_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyKilometrageImporter()
    stats = importer.import_all(base_path=base_path, full=False)

    assert stats.processed == 2
    assert stats.inserted == 1
    assert stats.skipped_old == 1
    assert stats.invalid == 0
    assert KilometrageRecordModel.objects.count() == 2


@pytest.mark.django_db
def test_import_kilometrage_no_cuenta_duplicados(tmp_path):
    """No cuenta duplicados cuando ignore_conflicts evita inserts."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A101",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    KilometrageRecordModel.objects.create(
        maintenance_unit=unit,
        unit_number="A101",
        record_date=date(2024, 1, 1),
        km_value=100,
        source="legacy_csv",
    )

    content = "Locs,Fecha,Kms_diario\n" "A101,01/01/2024,120\n"
    (base_path / "Kilometraje_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyKilometrageImporter()
    stats = importer.import_all(base_path=base_path, full=True)

    assert stats.processed == 1
    assert stats.inserted == 0
    assert stats.skipped_old == 0
    assert stats.invalid == 0
    assert KilometrageRecordModel.objects.count() == 1


@pytest.mark.django_db
def test_import_kilometrage_cuenta_solo_nuevos_con_duplicados(tmp_path):
    """Cuenta solo los inserts reales cuando hay duplicados."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A102",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    KilometrageRecordModel.objects.create(
        maintenance_unit=unit,
        unit_number="A102",
        record_date=date(2024, 1, 1),
        km_value=100,
        source="legacy_csv",
    )

    content = "Locs,Fecha,Kms_diario\n" "A102,01/01/2024,120\n" "A102,02/01/2024,150\n"
    (base_path / "Kilometraje_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyKilometrageImporter()
    stats = importer.import_all(base_path=base_path, full=True)

    assert stats.processed == 2
    assert stats.inserted == 1
    assert stats.skipped_old == 0
    assert stats.invalid == 0
    assert KilometrageRecordModel.objects.count() == 2
