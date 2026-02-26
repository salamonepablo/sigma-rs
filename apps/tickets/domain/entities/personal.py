"""Personal (Interviniente) domain entity.

Represents maintenance personnel who intervene in ticket resolution.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Sector(StrEnum):
    """Sector where personnel works."""

    LOCOMOTORAS = "locomotora"
    COCHES_REMOLCADOS = "coche_remolcado"


@dataclass(frozen=True)
class Personal:
    """Maintenance personnel entity.

    Attributes:
        id: Unique identifier.
        legajo_sap: SAP employee number.
        full_name: Full name of the employee.
        sector: Work sector (Locomotoras or Coches Remolcados).
        cuit: Argentine tax identification number (optional).
        sector_simaf: SIMAF system sector code (optional).
        is_active: Whether the employee is currently active.
    """

    id: UUID
    legajo_sap: str
    full_name: str
    sector: Sector
    cuit: str | None = None
    sector_simaf: str | None = None
    is_active: bool = True

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.full_name} ({self.legajo_sap})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Personal):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Return hash based on ID."""
        return hash(self.id)
