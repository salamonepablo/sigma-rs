"""Pruebas para el importador de novedades desde Access."""

from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.services.access_novedad_importer import (
    AccessNovedadImporter,
    AccessNovedadSource,
)
from apps.tickets.models import (
    IntervencionTipoModel,
    MaintenanceUnitModel,
    NovedadModel,
)


class DummyExtractor:
    """Extractor doble para devolver registros predefinidos."""

    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records

    def extract(self, **kwargs) -> list[dict[str, object]]:  # noqa: ARG002
        return self._records


@pytest.mark.django_db
def test_importador_access_no_duplica_con_manual_existente():
    """No inserta legacy si ya existe una novedad manual con misma clave negocio."""

    unit = MaintenanceUnitModel.objects.create(
        id=uuid4(),
        number="A100",
        unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
    )
    intervencion = IntervencionTipoModel.objects.create(
        codigo="RA",
        descripcion="Revision",
    )
    NovedadModel.objects.create(
        id=uuid4(),
        maintenance_unit=unit,
        fecha_desde=date(2024, 1, 1),
        intervencion=intervencion,
        is_legacy=False,
    )

    importer = AccessNovedadImporter(
        extractor=DummyExtractor(
            records=[
                {
                    "Unidad": "A100",
                    "Fecha_desde": "2024-01-01",
                    "Fecha_hasta": "",
                    "Fecha_est": "",
                    "Intervencion": "RA",
                    "Lugar": "",
                    "Observaciones": "Legacy duplicada",
                }
            ]
        )
    )

    stats = importer.import_all(
        baselocs=AccessNovedadSource(db_path=Path("baselocs.mdb"), unit_field="Locs"),
        baseccrr=None,
    )

    assert stats.processed == 1
    assert stats.inserted == 0
    assert stats.duplicates == 1
    assert NovedadModel.objects.count() == 1


@pytest.mark.django_db
def test_importador_access_permiste_fallback_legacy_sin_mapeo():
    """Sigue importando cuando no hay unidad/intervencion mapeada."""

    importer = AccessNovedadImporter(
        extractor=DummyExtractor(
            records=[
                {
                    "Unidad": "ZZ999",
                    "Fecha_desde": "2024-02-15",
                    "Fecha_hasta": "",
                    "Fecha_est": "",
                    "Intervencion": "XX",
                    "Lugar": "",
                    "Observaciones": "Sin mapeo",
                }
            ]
        )
    )

    stats = importer.import_all(
        baselocs=AccessNovedadSource(db_path=Path("baselocs.mdb"), unit_field="Locs"),
        baseccrr=None,
    )

    assert stats.processed == 1
    assert stats.inserted == 1
    assert stats.duplicates == 0

    novedad = NovedadModel.objects.get()
    assert novedad.maintenance_unit_id is None
    assert novedad.legacy_unit_code == "ZZ999"
    assert novedad.intervencion_id is None
    assert novedad.legacy_intervencion_codigo == "XX"
    assert novedad.is_legacy is True
