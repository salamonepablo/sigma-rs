"""Value objects for Ticket domain entity.

Contains enums for ticket status and entry type.
"""

from enum import StrEnum


class TicketStatus(StrEnum):
    """Status of a maintenance ticket.

    Tickets can be in one of two states:
        - PENDING: The ticket is open and awaiting resolution.
        - COMPLETED: The ticket has been resolved and closed.
    """

    PENDING = "pendiente"
    COMPLETED = "finalizado"

    @property
    def label(self) -> str:
        """Return the display label for this status."""
        labels = {
            TicketStatus.PENDING: "Pendiente",
            TicketStatus.COMPLETED: "Finalizado",
        }
        return labels[self]


class EntryType(StrEnum):
    """Type of maintenance entry for a ticket.

    Defines how the maintenance unit will be handled:
        - IMMEDIATE: Immediate entry to maintenance.
        - SCHEDULED: Scheduled entry for later maintenance.
        - NO: No entry required (repair done on the spot or deferred).
    """

    IMMEDIATE = "inmediato"
    SCHEDULED = "programado"
    NO = "no"

    @property
    def label(self) -> str:
        """Return the display label for this entry type."""
        labels = {
            EntryType.IMMEDIATE: "Inmediato",
            EntryType.SCHEDULED: "Programado",
            EntryType.NO: "NO",
        }
        return labels[self]
