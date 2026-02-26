"""Domain entity for MaintenanceUnit (Unidad de Mantenimiento).

Base abstract class for all maintenance units: Locomotives, Railcars, and Motorcoaches.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class MaintenanceUnit(ABC):
    """Abstract base class for maintenance units.

    Represents any rolling stock unit that can be maintained.
    Subclasses: Locomotive, Railcar, Motorcoach.

    Attributes:
        id: Unique identifier for the unit.
        number: Unit identification number (e.g., 'A904', 'U3001').
        is_active: Whether the unit is currently active in service.
    """

    id: UUID
    number: str
    is_active: bool = field(default=True)

    @property
    @abstractmethod
    def unit_type(self) -> str:
        """Return the type of maintenance unit.

        Must be implemented by subclasses.

        Returns:
            String identifying the unit type.
        """
        ...  # pragma: no cover

    def __str__(self) -> str:
        """Return string representation with type and number."""
        return f"{self.unit_type} {self.number}"

    def __eq__(self, other: object) -> bool:
        """Two units are equal if they have the same ID."""
        if not isinstance(other, MaintenanceUnit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
