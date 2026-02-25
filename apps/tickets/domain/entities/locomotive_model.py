"""Domain entity for LocomotiveModel (Modelo de Locomotora).

Represents a locomotive model associated with a brand.
Known GM models: GT22CW, GT22CW-2, G22CW, G22CU, GR12, G12.
Known CNR models: 8G, 8H.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class LocomotiveModel:
    """A locomotive model specification.

    Models are associated with a specific brand and define the
    technical characteristics of a locomotive type.

    Known models by brand:
        - GM: GT22CW, GT22CW-2, G22CW, G22CU, GR12, G12
        - CNR (Dalian): 8G, 8H

    Attributes:
        id: Unique identifier for the model.
        name: Display name (e.g., 'GT22CW', '8G').
        code: Unique code for the model (e.g., 'GT22CW', 'GT22CW2').
        brand_id: Foreign key to the Brand entity.
        description: Optional description of the model.
        is_active: Whether the model is currently active.
    """

    id: UUID
    name: str
    code: str
    brand_id: UUID
    description: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the display name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Two models are equal if they have the same ID."""
        if not isinstance(other, LocomotiveModel):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
