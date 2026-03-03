"""Pruebas de formularios para novedades."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
)
from apps.tickets.presentation.forms import NovedadForm


@pytest.mark.django_db
class TestNovedadForm:
    """Pruebas de validación para NovedadForm."""

    def _dependencies(self):
        unit = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A200",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        intervencion = IntervencionTipoModel.objects.create(
            codigo="AL",
            descripcion="Alineación",
        )
        lugar = LugarModel.objects.create(codigo=10, descripcion="Taller Quilmes")
        return unit, intervencion, lugar

    def _base_data(self, unit, intervencion, lugar):
        return {
            "unit_input": unit.number,
            "intervencion_input": intervencion.codigo,
            "lugar_input": str(lugar.codigo),
            "fecha_desde": date.today().isoformat(),
        }

    def test_requires_unit_input(self):
        """Debe exigir un dato de unidad."""
        unit, intervencion, lugar = self._dependencies()
        data = self._base_data(unit, intervencion, lugar)
        data["unit_input"] = ""

        form = NovedadForm(data=data)

        assert not form.is_valid()
        assert form.has_error("unit_input")

    def test_allows_manual_unit_code_when_not_found(self):
        """Permite registrar unidades sin maestro usando código manual."""
        unit, intervencion, lugar = self._dependencies()
        data = {
            "unit_input": "X999",
            "intervencion_input": intervencion.codigo,
            "lugar_input": str(lugar.codigo),
            "fecha_desde": date.today().isoformat(),
        }

        form = NovedadForm(data=data)

        assert form.is_valid()
        instance = form.save()
        assert instance.maintenance_unit is None
        assert instance.legacy_unit_code == "X999"
        assert instance.fecha_hasta == date.today()

    def test_date_range_validation(self):
        """La fecha hasta no puede ser anterior a la desde."""
        unit, intervencion, lugar = self._dependencies()
        today = date.today()
        data = self._base_data(unit, intervencion, lugar)
        data.update(
            {
                "fecha_desde": today.isoformat(),
                "fecha_hasta": (today - timedelta(days=1)).isoformat(),
            }
        )

        form = NovedadForm(data=data)

        assert not form.is_valid()
        assert form.has_error("fecha_hasta")

    def test_requires_existing_lugar(self):
        """El lugar debe existir en el maestro."""
        unit, intervencion, _ = self._dependencies()
        data = {
            "unit_input": unit.number,
            "intervencion_input": intervencion.codigo,
            "lugar_input": "NOPE",
            "fecha_desde": date.today().isoformat(),
        }

        form = NovedadForm(data=data)

        assert not form.is_valid()
        assert form.has_error("lugar_input")

    def test_save_marks_manual_records_as_non_legacy(self):
        """Guardar desde el formulario crea registros manuales (no legacy)."""
        unit, intervencion, lugar = self._dependencies()
        data = self._base_data(unit, intervencion, lugar)
        data["observaciones"] = "Verificación manual"

        form = NovedadForm(data=data)

        assert form.is_valid()

        instance = form.save()

        assert instance.is_legacy is False

    def test_sets_fecha_hasta_when_missing(self):
        """Si no informan fecha hasta se iguala a fecha desde."""
        unit, intervencion, lugar = self._dependencies()
        today = date.today()
        data = self._base_data(unit, intervencion, lugar)
        data["fecha_desde"] = today.isoformat()
        data["fecha_hasta"] = ""

        form = NovedadForm(data=data)

        assert form.is_valid()
        instance = form.save()
        assert instance.fecha_hasta == today
