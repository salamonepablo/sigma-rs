"""Domain entity for TrainNumber (Número de Tren).

Represents a train service number identifier.
Train numbers are typically 4-digit identifiers for railway services.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class TrainNumber:
    """A train service number.

    Train numbers identify specific railway services.
    They are typically 4-digit numbers that identify routes and schedules.

    Attributes:
        id: Unique identifier for the train number.
        number: The train number (typically 4 digits, e.g., '1234').
        description: Optional description of the service.
        route: Optional route description (e.g., 'Constitución - La Plata').
        is_active: Whether the train number is currently active.
    """

    id: UUID
    number: str
    description: str | None = field(default=None)
    route: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the train number."""
        return self.number

    def __eq__(self, other: object) -> bool:
        """Two train numbers are equal if they have the same ID."""
        if not isinstance(other, TrainNumber):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
