"""Domain entity for Wagon (Vagon).

Represents a freight wagon unit.
"""

from dataclasses import dataclass

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


@dataclass(kw_only=True, eq=False)
class Wagon(MaintenanceUnit):
    """A freight wagon maintenance unit.

    Wagons are identified by their number and have a type and brand.

    Attributes:
        id: Unique identifier for the wagon.
        number: Wagon identification number (e.g., 'BK001').
        wagon_type: Wagon type code or name (e.g., 'BK', 'Hopper').
        brand: Manufacturer brand (e.g., 'Carga').
        is_active: Whether the wagon is currently active in service.
    """

    wagon_type: str
    brand: str

    @property
    def unit_type(self) -> str:
        """Return the unit type identifier.

        Returns:
            'Vagon' as the type identifier.
        """
        return "Vagon"
