"""Domain entity for RailcarClass (Clase de Coche Remolcado).

Represents a railcar class associated with a brand.
Known Materfer classes: U, FU, F.
Known CNR classes: CPA, CRA, PUA, PUAD, FS, FG.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class RailcarClass:
    """A railcar class specification.

    Classes are associated with a specific brand and define the
    type and characteristics of a railcar.

    Known classes by brand:
        - Materfer: U, FU, F
        - CNR (Dalian): CPA, CRA, PUA, PUAD, FS, FG

    Attributes:
        id: Unique identifier for the class.
        name: Display name (e.g., 'U', 'CPA').
        code: Unique code for the class (e.g., 'U', 'CPA').
        brand_id: Foreign key to the Brand entity.
        description: Optional description of the class.
        is_active: Whether the class is currently active.
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
        """Two classes are equal if they have the same ID."""
        if not isinstance(other, RailcarClass):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
