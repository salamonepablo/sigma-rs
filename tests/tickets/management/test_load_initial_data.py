"""Tests para el comando load_initial_data."""

from pathlib import Path

import pytest

from apps.tickets.infrastructure.models import (
    GOPModel,
    LocomotiveModel,
    MaintenanceUnitModel,
    PersonalModel,
)
from apps.tickets.management.commands.load_initial_data import Command


@pytest.mark.django_db
def test_load_initial_data_creates_personal_and_units(tmp_path, monkeypatch):
    """Carga datos mínimos desde CSVs y crea entidades básicas."""
    context_dir = tmp_path / "context"
    context_dir.mkdir(parents=True)

    personal_csv = (
        "Legajo SAP;Cuit;Nombre y Apellido;Sector;SectorSIMAF\n"
        "123;20123456789;JUAN PEREZ;Locomotoras;PMRE\n"
    )
    ums_csv = (
        "Unidad de Mantenimiento;Tipo;Marca;Modelo;Clase;Cantidad Coches;Conformación\n"
        "A100;Locomotora;GM;G22-CW;;;\n"
    )

    (context_dir / "personal.csv").write_text(personal_csv, encoding="latin-1")
    (context_dir / "ums.csv").write_text(ums_csv, encoding="latin-1")

    monkeypatch.chdir(tmp_path)

    Command().handle()

    assert GOPModel.objects.exists()
    assert PersonalModel.objects.count() == 1
    assert MaintenanceUnitModel.objects.count() == 1
    assert LocomotiveModel.objects.count() == 1
