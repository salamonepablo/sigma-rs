"""Domain entity for Railcar (Coche Remolcado).

Represents a railcar (towed coach) used in the Roca Line.
"""

from dataclasses import dataclass
from uuid import UUID

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


@dataclass(kw_only=True, eq=False)
class Railcar(MaintenanceUnit):
    """A railcar (towed coach) maintenance unit.

    Railcars are identified by their number (e.g., 'U3001') and have
    a specific brand and coach type combination.

    Known brands and coach types:
        - Materfer: U (Única), FU (Furgón Única), F (Furgón)
        - CNR: CPA, CRA, PUA, PUAD, FS, FG

    Attributes:
        id: Unique identifier for the railcar.
        number: Railcar identification number (e.g., 'U3001', 'CPA001').
        brand: Manufacturer brand (e.g., 'Materfer', 'CNR').
        coach_type: Type of coach (e.g., 'U', 'CPA').
        is_active: Whether the railcar is currently active in service.
    """

    brand: str
    coach_type: str

    @property
    def unit_type(self) -> str:
        """Return the unit type identifier.

        Returns:
            'Coche Remolcado' as the type identifier.
        """
        return "Coche Remolcado"
