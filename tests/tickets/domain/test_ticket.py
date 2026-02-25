"""Tests para la entidad Ticket (Avería).

Pruebas de dominio para tickets de averías en material rodante.
El ticket es la entidad principal del sistema SIGMA-RS.
"""

from datetime import date, time
from uuid import uuid4

import pytest

from apps.tickets.domain.entities.ticket import Ticket
from apps.tickets.domain.value_objects.ticket_enums import EntryType, TicketStatus


class TestTicketCreation:
    """Pruebas de creación de tickets."""

    def test_create_ticket_with_required_fields(self):
        """Verifica que se puede crear un ticket con campos requeridos."""
        ticket_id = uuid4()
        maintenance_unit_id = uuid4()
        gop_id = uuid4()

        ticket = Ticket(
            id=ticket_id,
            ticket_number="2024-001",
            date=date(2024, 1, 15),
            maintenance_unit_id=maintenance_unit_id,
            gop_id=gop_id,
            entry_type=EntryType.IMMEDIATE,
            status=TicketStatus.PENDING,
            reported_failure="Motor no arranca",
        )

        assert ticket.id == ticket_id
        assert ticket.ticket_number == "2024-001"
        assert ticket.date == date(2024, 1, 15)
        assert ticket.maintenance_unit_id == maintenance_unit_id
        assert ticket.gop_id == gop_id
        assert ticket.entry_type == EntryType.IMMEDIATE
        assert ticket.status == TicketStatus.PENDING
        assert ticket.reported_failure == "Motor no arranca"

    def test_create_ticket_with_all_fields(self):
        """Verifica que se puede crear un ticket con todos los campos."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-002",
            date=date(2024, 1, 16),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.SCHEDULED,
            status=TicketStatus.PENDING,
            reported_failure="Fuga de aceite en motor diésel",
            work_order_number="OT-2024-100",
            supervisor_id=uuid4(),
            train_number_id=uuid4(),
            failure_type_id=uuid4(),
            affected_system_id=uuid4(),
            notification_time=time(8, 30),
            intervention_time=time(9, 0),
            delivery_time=time(12, 0),
            observations="Se reemplazó empaquetadura",
        )

        assert ticket.work_order_number == "OT-2024-100"
        assert ticket.notification_time == time(8, 30)
        assert ticket.intervention_time == time(9, 0)
        assert ticket.delivery_time == time(12, 0)
        assert ticket.observations == "Se reemplazó empaquetadura"


class TestTicketDefaults:
    """Pruebas de valores por defecto."""

    def test_status_defaults_to_pending(self):
        """Verifica que el estado por defecto es Pendiente."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-003",
            date=date(2024, 1, 17),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.NO,
            reported_failure="Luz de tablero apagada",
        )

        assert ticket.status == TicketStatus.PENDING

    def test_optional_fields_default_to_none(self):
        """Verifica que los campos opcionales son None por defecto."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-004",
            date=date(2024, 1, 18),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla en frenos",
        )

        assert ticket.work_order_number is None
        assert ticket.supervisor_id is None
        assert ticket.train_number_id is None
        assert ticket.failure_type_id is None
        assert ticket.affected_system_id is None
        assert ticket.notification_time is None
        assert ticket.intervention_time is None
        assert ticket.delivery_time is None
        assert ticket.observations is None


class TestTicketStatus:
    """Pruebas de estados del ticket."""

    def test_create_pending_ticket(self):
        """Verifica que se puede crear un ticket pendiente."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-005",
            date=date(2024, 1, 19),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            status=TicketStatus.PENDING,
            reported_failure="Problema eléctrico",
        )

        assert ticket.status == TicketStatus.PENDING
        assert ticket.is_pending is True
        assert ticket.is_completed is False

    def test_create_completed_ticket(self):
        """Verifica que se puede crear un ticket finalizado."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-006",
            date=date(2024, 1, 20),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.SCHEDULED,
            status=TicketStatus.COMPLETED,
            reported_failure="Sistema ATS fallando",
        )

        assert ticket.status == TicketStatus.COMPLETED
        assert ticket.is_pending is False
        assert ticket.is_completed is True


class TestTicketEntryType:
    """Pruebas de tipos de ingreso."""

    @pytest.mark.parametrize(
        "entry_type,expected_value",
        [
            (EntryType.IMMEDIATE, "inmediato"),
            (EntryType.SCHEDULED, "programado"),
            (EntryType.NO, "no"),
        ],
    )
    def test_create_ticket_with_different_entry_types(
        self, entry_type: EntryType, expected_value: str
    ):
        """Verifica que se pueden crear tickets con diferentes tipos de ingreso."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-007",
            date=date(2024, 1, 21),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=entry_type,
            reported_failure="Falla de prueba",
        )

        assert ticket.entry_type == entry_type
        assert ticket.entry_type.value == expected_value


class TestTicketStringRepresentation:
    """Pruebas de representación en string."""

    def test_str_representation(self):
        """Verifica la representación en string de un ticket."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-008",
            date=date(2024, 1, 22),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Motor recalentado",
        )

        assert str(ticket) == "Ticket 2024-008"

    def test_repr_contains_key_info(self):
        """Verifica que repr contiene información clave."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-009",
            date=date(2024, 1, 23),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.SCHEDULED,
            status=TicketStatus.COMPLETED,
            reported_failure="Falla neumática",
        )

        repr_str = repr(ticket)
        assert "2024-009" in repr_str
        assert "2024-01-23" in repr_str


class TestTicketEquality:
    """Pruebas de igualdad y hash."""

    def test_equality_based_on_id(self):
        """Dos tickets con el mismo ID son iguales."""
        ticket_id = uuid4()
        ticket1 = Ticket(
            id=ticket_id,
            ticket_number="2024-010",
            date=date(2024, 1, 24),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla 1",
        )
        ticket2 = Ticket(
            id=ticket_id,
            ticket_number="2024-010",
            date=date(2024, 1, 24),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla 1",
        )

        assert ticket1 == ticket2

    def test_inequality_for_different_ids(self):
        """Dos tickets con diferente ID no son iguales."""
        ticket1 = Ticket(
            id=uuid4(),
            ticket_number="2024-011",
            date=date(2024, 1, 25),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.NO,
            reported_failure="Falla A",
        )
        ticket2 = Ticket(
            id=uuid4(),
            ticket_number="2024-011",
            date=date(2024, 1, 25),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.NO,
            reported_failure="Falla A",
        )

        assert ticket1 != ticket2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        ticket_id = uuid4()
        ticket1 = Ticket(
            id=ticket_id,
            ticket_number="2024-012",
            date=date(2024, 1, 26),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla X",
        )
        ticket2 = Ticket(
            id=ticket_id,
            ticket_number="2024-012",
            date=date(2024, 1, 26),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla X",
        )

        assert hash(ticket1) == hash(ticket2)


class TestTicketTimeTracking:
    """Pruebas de seguimiento de tiempos."""

    def test_all_times_can_be_set(self):
        """Verifica que se pueden establecer todos los tiempos."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-013",
            date=date(2024, 1, 27),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.IMMEDIATE,
            reported_failure="Falla urgente",
            notification_time=time(6, 0),
            intervention_time=time(6, 30),
            delivery_time=time(10, 0),
        )

        assert ticket.notification_time == time(6, 0)
        assert ticket.intervention_time == time(6, 30)
        assert ticket.delivery_time == time(10, 0)

    def test_partial_times_allowed(self):
        """Verifica que se pueden establecer tiempos parciales."""
        ticket = Ticket(
            id=uuid4(),
            ticket_number="2024-014",
            date=date(2024, 1, 28),
            maintenance_unit_id=uuid4(),
            gop_id=uuid4(),
            entry_type=EntryType.SCHEDULED,
            reported_failure="Falla programada",
            notification_time=time(14, 0),
            # intervention_time and delivery_time are None
        )

        assert ticket.notification_time == time(14, 0)
        assert ticket.intervention_time is None
        assert ticket.delivery_time is None
