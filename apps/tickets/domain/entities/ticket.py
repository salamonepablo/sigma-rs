"""Domain entity for Ticket (Avería).

Represents a maintenance ticket for rolling stock failures.
This is the main entity of the SIGMA-RS system.
"""

from dataclasses import dataclass, field
from datetime import date, time
from uuid import UUID

from apps.tickets.domain.value_objects.ticket_enums import EntryType, TicketStatus


@dataclass(kw_only=True, eq=False)
class Ticket:
    """A maintenance ticket for rolling stock failures.

    Tickets track reported failures on maintenance units (locomotives,
    railcars, or motorcoaches) and their resolution status.

    Attributes:
        id: Unique identifier for the ticket.
        ticket_number: Human-readable ticket number (e.g., '2024-001').
        date: Date when the failure was reported.
        maintenance_unit_id: FK to the affected maintenance unit.
        gop_id: FK to the GOP (operational guard) handling the ticket.
        entry_type: Type of maintenance entry (immediate, scheduled, no).
        status: Current status (pending, completed).
        reported_failure: Description of the failure reported by the driver.
        work_order_number: Optional work order number (Nro OT).
        supervisor_id: FK to the supervising supervisor (optional).
        train_number_id: FK to the train number (optional).
        failure_type_id: FK to the type of failure (optional).
        affected_system_id: FK to the affected system (optional).
        notification_time: Time when the failure was notified (optional).
        intervention_time: Time when intervention started (optional).
        delivery_time: Time when the unit was delivered (optional).
        observations: Work performed / observations by GOP (optional).
    """

    # Required fields
    id: UUID
    ticket_number: str
    date: date
    maintenance_unit_id: UUID
    gop_id: UUID
    entry_type: EntryType
    reported_failure: str

    # Status with default
    status: TicketStatus = field(default=TicketStatus.PENDING)

    # Optional foreign keys
    work_order_number: str | None = field(default=None)
    supervisor_id: UUID | None = field(default=None)
    train_number_id: UUID | None = field(default=None)
    failure_type_id: UUID | None = field(default=None)
    affected_system_id: UUID | None = field(default=None)

    # Optional time tracking
    notification_time: time | None = field(default=None)
    intervention_time: time | None = field(default=None)
    delivery_time: time | None = field(default=None)

    # Optional text fields
    observations: str | None = field(default=None)

    @property
    def is_pending(self) -> bool:
        """Check if the ticket is pending."""
        return self.status == TicketStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if the ticket is completed."""
        return self.status == TicketStatus.COMPLETED

    def __str__(self) -> str:
        """Return string representation with ticket number."""
        return f"Ticket {self.ticket_number}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"Ticket(number={self.ticket_number!r}, "
            f"date={self.date.isoformat()}, "
            f"status={self.status.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Two tickets are equal if they have the same ID."""
        if not isinstance(other, Ticket):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
