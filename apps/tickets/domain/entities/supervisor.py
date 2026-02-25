"""Domain entity for Supervisor.

Represents a maintenance supervisor who oversees GOP work.
Supervisors are responsible for coordinating ticket resolution.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class Supervisor:
    """A maintenance supervisor.

    Supervisors oversee and coordinate the work of maintenance
    personnel (GOPs) in resolving tickets.

    Attributes:
        id: Unique identifier for the supervisor.
        name: Full name of the supervisor.
        employee_number: Unique employee identification number.
        email: Contact email address (optional).
        phone: Contact phone number (optional).
        is_active: Whether the supervisor is currently active.
    """

    id: UUID
    name: str
    employee_number: str
    email: str | None = field(default=None)
    phone: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the supervisor's name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Two supervisors are equal if they have the same ID."""
        if not isinstance(other, Supervisor):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
