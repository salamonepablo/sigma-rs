"""Domain entity for Locomotive (Locomotora).

Represents a diesel locomotive used in the Roca Line.
"""

from dataclasses import dataclass

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


@dataclass(kw_only=True, eq=False)
class Locomotive(MaintenanceUnit):
    """A diesel locomotive maintenance unit.

    Locomotives are identified by their number (e.g., 'A904') and have
    a specific brand and model combination.

    Known brands and models:
        - GM: GT22CW, GT22CW-2, G22CW, G22CU, GR12, G12
        - CNR (Dalian): 8G, 8H

    Attributes:
        id: Unique identifier for the locomotive.
        number: Locomotive identification number (e.g., 'A904', 'CKD0001').
        brand: Manufacturer brand (e.g., 'GM', 'CNR').
        model: Locomotive model (e.g., 'GT22CW', '8G').
        is_active: Whether the locomotive is currently active in service.
    """

    brand: str
    model: str

    @property
    def unit_type(self) -> str:
        """Return the unit type identifier.

        Returns:
            'Locomotora' as the type identifier.
        """
        return "Locomotora"
