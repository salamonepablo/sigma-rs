"""Pruebas para el importador de novedades legacy."""

from datetime import date
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.services.legacy_novedad_importer import (
    LegacyNovedadImporter,
)
from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)


@pytest.mark.django_db
def test_import_detenciones_counts(tmp_path):
    """Cuenta insertados, duplicados e invalidos para detenciones locs."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A100",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    IntervencionTipoModel.objects.create(codigo="RA", descripcion="Revision")
    LugarModel.objects.create(codigo=10, descripcion="Taller")

    content = (
        "Locs;Fecha_desde;Fecha_hasta;Intervencion;Lugar;Observaciones;Fecha_est\n"
        "A100;01/01/2024;;RA;10;Obs;\n"
        "A100;01/01/2024;;RA;10;Obs;\n"
        "A100;;01/02/2024;RA;10;;\n"
    )
    (base_path / "Detenciones_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyNovedadImporter()
    stats = importer.import_detenciones(base_path=base_path)

    assert stats.processed == 3
    assert stats.inserted == 1
    assert stats.duplicates == 1
    assert stats.invalid == 1
    assert NovedadModel.objects.count() == 1


@pytest.mark.django_db
def test_import_detenciones_ccrr_counts(tmp_path):
    """Importa detenciones CCRR y registra conteos."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="U200",
        unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
    )
    IntervencionTipoModel.objects.create(codigo="AL", descripcion="Alistamiento")
    LugarModel.objects.create(codigo=20, descripcion="Taller CCRR")

    content = (
        "Coche;Fecha_desde;Fecha_hasta;Intervencion;Lugar;Observaciones;Fecha_est\n"
        "U200;05/01/2024;;AL;20;;\n"
    )
    (base_path / "Detenciones_CCRR.txt").write_text(content, encoding="latin-1")

    importer = LegacyNovedadImporter()
    stats = importer.import_detenciones_ccrr(base_path=base_path)

    assert stats.processed == 1
    assert stats.inserted == 1
    assert stats.duplicates == 0
    assert stats.invalid == 0
    assert NovedadModel.objects.count() == 1


@pytest.mark.django_db
def test_import_detenciones_dedup_con_fecha_hasta(tmp_path):
    """Incluye fecha_hasta en la clave de deduplicacion."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A200",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    intervencion = IntervencionTipoModel.objects.create(
        codigo="IN",
        descripcion="Inspeccion",
    )
    lugar = LugarModel.objects.create(codigo=30, descripcion="Taller Norte")
    NovedadModel.objects.create(
        id=uuid4(),
        maintenance_unit=unit,
        fecha_desde=date(2024, 1, 1),
        fecha_hasta=date(2024, 1, 10),
        intervencion=intervencion,
        lugar=lugar,
        is_legacy=True,
    )

    content = (
        "Locs;Fecha_desde;Fecha_hasta;Intervencion;Lugar;Observaciones;Fecha_est\n"
        "A200;01/01/2024;10/01/2024;IN;30;;\n"
    )
    (base_path / "Detenciones_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyNovedadImporter()
    stats = importer.import_detenciones(base_path=base_path)

    assert stats.processed == 1
    assert stats.inserted == 0
    assert stats.duplicates == 1
    assert stats.invalid == 0
    assert NovedadModel.objects.count() == 1


@pytest.mark.django_db
def test_import_detenciones_normaliza_fecha_hasta_vacia(tmp_path):
    """Normaliza fecha_hasta vacia para deduplicar."""
    base_path = tmp_path / "context" / "db-legacy"
    base_path.mkdir(parents=True)

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A201",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    intervencion = IntervencionTipoModel.objects.create(
        codigo="RE",
        descripcion="Reparacion",
    )
    lugar = LugarModel.objects.create(codigo=31, descripcion="Taller Sur")
    NovedadModel.objects.create(
        id=uuid4(),
        maintenance_unit=unit,
        fecha_desde=date(2024, 2, 1),
        fecha_hasta=None,
        intervencion=intervencion,
        lugar=lugar,
        is_legacy=True,
    )

    content = (
        "Locs;Fecha_desde;Fecha_hasta;Intervencion;Lugar;Observaciones;Fecha_est\n"
        "A201;01/02/2024;;RE;31;;\n"
    )
    (base_path / "Detenciones_Locs.txt").write_text(content, encoding="latin-1")

    importer = LegacyNovedadImporter()
    stats = importer.import_detenciones(base_path=base_path)

    assert stats.processed == 1
    assert stats.inserted == 0
    assert stats.duplicates == 1
    assert stats.invalid == 0
    assert NovedadModel.objects.count() == 1
