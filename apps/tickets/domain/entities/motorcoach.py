"""Domain entity for Motorcoach (Coche Motor).

Represents a diesel motorcoach (self-propelled train) used in the Roca Line.
"""

from dataclasses import dataclass
from uuid import UUID

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


@dataclass(kw_only=True, eq=False)
class Motorcoach(MaintenanceUnit):
    """A motorcoach (self-propelled train) maintenance unit.

    Motorcoaches are diesel multiple units (DMU) identified by their number
    and have a specific brand, model, and configuration.

    Known brands and models:
        - CNR (Dalian): CKD

    Known configurations:
        - CM-CM: Two motor coaches coupled together
        - CM-R-CM: Two motor coaches with an intermediate trailer

    Attributes:
        id: Unique identifier for the motorcoach.
        number: Motorcoach identification number (e.g., 'CM001').
        brand: Manufacturer brand (e.g., 'CNR').
        model: Motorcoach model (e.g., 'CKD').
        configuration: Train configuration (e.g., 'CM-CM', 'CM-R-CM').
        is_active: Whether the motorcoach is currently active in service.
    """

    brand: str
    model: str
    configuration: str

    @property
    def unit_type(self) -> str:
        """Return the unit type identifier.

        Returns:
            'Coche Motor' as the type identifier.
        """
        return "Coche Motor"
