"""Tests para enums de Ticket.

Pruebas de dominio para los enums TicketStatus y EntryType.
"""

from apps.tickets.domain.value_objects.ticket_enums import EntryType, TicketStatus


class TestTicketStatus:
    """Pruebas para el enum TicketStatus."""

    def test_pending_status_exists(self):
        """Verifica que existe el estado Pendiente."""
        assert TicketStatus.PENDING.value == "pendiente"

    def test_completed_status_exists(self):
        """Verifica que existe el estado Finalizado."""
        assert TicketStatus.COMPLETED.value == "finalizado"

    def test_has_only_two_statuses(self):
        """Verifica que solo existen dos estados."""
        assert len(TicketStatus) == 2

    def test_status_labels(self):
        """Verifica las etiquetas de visualización de los estados."""
        assert TicketStatus.PENDING.label == "Pendiente"
        assert TicketStatus.COMPLETED.label == "Finalizado"

    def test_status_from_value(self):
        """Verifica que se puede obtener un estado desde su valor."""
        assert TicketStatus("pendiente") == TicketStatus.PENDING
        assert TicketStatus("finalizado") == TicketStatus.COMPLETED


class TestEntryType:
    """Pruebas para el enum EntryType (Tipo de Ingreso)."""

    def test_immediate_entry_exists(self):
        """Verifica que existe el tipo de ingreso Inmediato."""
        assert EntryType.IMMEDIATE.value == "inmediato"

    def test_scheduled_entry_exists(self):
        """Verifica que existe el tipo de ingreso Programado."""
        assert EntryType.SCHEDULED.value == "programado"

    def test_no_entry_exists(self):
        """Verifica que existe el tipo de ingreso NO (sin ingreso)."""
        assert EntryType.NO.value == "no"

    def test_has_only_three_entry_types(self):
        """Verifica que solo existen tres tipos de ingreso."""
        assert len(EntryType) == 3

    def test_entry_type_labels(self):
        """Verifica las etiquetas de visualización de los tipos de ingreso."""
        assert EntryType.IMMEDIATE.label == "Inmediato"
        assert EntryType.SCHEDULED.label == "Programado"
        assert EntryType.NO.label == "NO"

    def test_entry_type_from_value(self):
        """Verifica que se puede obtener un tipo desde su valor."""
        assert EntryType("inmediato") == EntryType.IMMEDIATE
        assert EntryType("programado") == EntryType.SCHEDULED
        assert EntryType("no") == EntryType.NO
