"""Tests para el modelo TicketModel (infraestructura)."""

from datetime import date
from uuid import uuid4

import pytest

from apps.tickets.infrastructure.models import (
    GOPModel,
    MaintenanceUnitModel,
    TicketModel,
)


@pytest.mark.django_db
class TestTicketModel:
    """Pruebas de generación de número de ticket."""

    def _create_dependencies(self):
        maintenance_unit = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A200",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        gop = GOPModel.objects.create(id=uuid4(), name="GOP 1", code="G1")
        return maintenance_unit, gop

    def test_generates_ticket_number_when_missing(self):
        """Genera número cuando no se provee explícitamente."""
        maintenance_unit, gop = self._create_dependencies()
        today = date.today()

        ticket = TicketModel(
            id=uuid4(),
            ticket_number="",
            date=today,
            maintenance_unit=maintenance_unit,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            reported_failure="Falla de prueba",
        )
        ticket.save()

        assert ticket.ticket_number.startswith(f"{today.year}-")
        assert ticket.ticket_number.endswith("0001")

    def test_ticket_number_increments(self):
        """Incrementa el número cuando ya existe uno en el año."""
        maintenance_unit, gop = self._create_dependencies()
        today = date.today()

        first = TicketModel(
            id=uuid4(),
            ticket_number=f"{today.year}-0001",
            date=today,
            maintenance_unit=maintenance_unit,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            reported_failure="Falla A",
        )
        first.save()

        second = TicketModel(
            id=uuid4(),
            ticket_number="",
            date=today,
            maintenance_unit=maintenance_unit,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            reported_failure="Falla B",
        )
        second.save()

        assert second.ticket_number.endswith("0002")
