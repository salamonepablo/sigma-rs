"""Tests para formularios de tickets en la capa de presentación."""

from datetime import date
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.models import GOPModel, MaintenanceUnitModel
from apps.tickets.presentation.forms import TicketForm


@pytest.mark.django_db
class TestTicketForm:
    """Pruebas de validación para TicketForm."""

    def _create_base_objects(self):
        maintenance_unit = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A100",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        gop = GOPModel.objects.create(
            id=uuid4(),
            name="GOP 1",
            code="G1",
        )
        return maintenance_unit, gop

    def _base_form_data(self, maintenance_unit, gop):
        return {
            "date": date.today().isoformat(),
            "maintenance_unit": str(maintenance_unit.id),
            "gop": str(gop.id),
            "entry_type": "inmediato",
            "status": "pendiente",
            "reported_failure": "Falla de prueba",
        }

    def test_resolution_required_when_service_affected(self):
        """Debe requerir resolución cuando afectó al servicio."""
        maintenance_unit, gop = self._create_base_objects()
        data = self._base_form_data(maintenance_unit, gop)
        data.update({"affected_service": "si", "resolution": ""})

        form = TicketForm(data=data)

        assert not form.is_valid()
        assert "resolution" in form.errors

    def test_resolution_cleared_when_service_not_affected(self):
        """Debe limpiar resolución cuando no afectó al servicio."""
        maintenance_unit, gop = self._create_base_objects()
        data = self._base_form_data(maintenance_unit, gop)
        data.update({"affected_service": "no", "resolution": "aceptada"})

        form = TicketForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data["resolution"] is None

    def test_default_work_order_number_initial(self):
        """El campo de OT debe iniciar con S/OT en alta."""
        form = TicketForm()

        assert form.fields["work_order_number"].initial == "S/OT"
