"""Domain entity for Brand (Marca).

Represents a manufacturer brand for rolling stock.
Known brands: GM (General Motors), CNR (Dalian), Materfer.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class Brand:
    """A manufacturer brand for rolling stock.

    Brands identify the manufacturer of locomotives, railcars, or motorcoaches.

    Known brands:
        - GM (General Motors): Manufactures locomotives in Argentina.
        - CNR (China CNR Corporation - Dalian): Manufactures locomotives,
          railcars, and motorcoaches.
        - Materfer (Material Ferroviario S.A.): Manufactures railcars.

    Attributes:
        id: Unique identifier for the brand.
        name: Short display name (e.g., 'GM', 'CNR', 'Materfer').
        code: Unique code for the brand (e.g., 'GM', 'CNR', 'MAT').
        full_name: Full legal or descriptive name (optional).
        is_active: Whether the brand is currently active.
    """

    id: UUID
    name: str
    code: str
    full_name: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the short display name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Two brands are equal if they have the same ID."""
        if not isinstance(other, Brand):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
