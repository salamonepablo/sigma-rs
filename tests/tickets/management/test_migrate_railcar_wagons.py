"""Tests for migrating railcar wagons command."""

import uuid

import pytest
from django.core.management import call_command

from apps.tickets.infrastructure.models import (
    BrandModel,
    MaintenanceUnitModel,
    RailcarClassModel,
    RailcarModel,
    WagonModel,
)


@pytest.mark.django_db
def test_migrate_railcar_wagons_moves_unit_to_wagon():
    legacy_brand = BrandModel.objects.create(
        id=uuid.uuid4(), code="Vagon", name="Vagon", full_name="Vagon"
    )
    target_brand = BrandModel.objects.create(
        id=uuid.uuid4(), code="Carga", name="Carga", full_name="Vagones de Carga"
    )
    railcar_class = RailcarClassModel.objects.create(
        id=uuid.uuid4(), code="VAGON_LEGACY", name="Vagon"
    )

    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(),
        number="CR100",
        unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
        rolling_stock_category=MaintenanceUnitModel.Category.RAILCAR,
    )
    RailcarModel.objects.create(
        maintenance_unit=unit, brand=legacy_brand, railcar_class=railcar_class
    )

    call_command("migrate_railcar_wagons")

    unit.refresh_from_db()
    assert unit.unit_type == MaintenanceUnitModel.UnitType.WAGON
    assert unit.rolling_stock_category == MaintenanceUnitModel.Category.CARGO

    assert not RailcarModel.objects.filter(maintenance_unit=unit).exists()
    wagon = WagonModel.objects.get(maintenance_unit=unit)
    assert wagon.brand_id == target_brand.id
    assert wagon.wagon_type.code == "VAGON"
    assert wagon.legacy_class == "VAGON_LEGACY"


@pytest.mark.django_db
def test_migrate_railcar_wagons_dry_run_keeps_data():
    legacy_brand = BrandModel.objects.create(
        id=uuid.uuid4(), code="Vagon", name="Vagon", full_name="Vagon"
    )
    railcar_class = RailcarClassModel.objects.create(
        id=uuid.uuid4(), code="VAGON_LEGACY", name="Vagon"
    )

    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(),
        number="CR200",
        unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
        rolling_stock_category=MaintenanceUnitModel.Category.RAILCAR,
    )
    RailcarModel.objects.create(
        maintenance_unit=unit, brand=legacy_brand, railcar_class=railcar_class
    )

    call_command("migrate_railcar_wagons", "--dry-run")

    unit.refresh_from_db()
    assert unit.unit_type == MaintenanceUnitModel.UnitType.RAILCAR
    assert RailcarModel.objects.filter(maintenance_unit=unit).exists()
    assert not WagonModel.objects.filter(maintenance_unit=unit).exists()
