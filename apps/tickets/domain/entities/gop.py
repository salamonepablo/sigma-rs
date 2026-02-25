"""Domain entity for GOP (Guardia Operativa).

Represents an operational guard shift for maintenance personnel.
GOPs are work shifts that handle maintenance tickets.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class GOP:
    """An operational guard shift (Guardia Operativa).

    GOPs represent the work shifts of maintenance personnel who
    handle and resolve tickets. Each ticket is assigned to a GOP.

    Typical GOPs: GOP 1, GOP 2, GOP 3, GOP 4.

    Attributes:
        id: Unique identifier for the GOP.
        name: Display name (e.g., 'GOP 1', 'GOP 2').
        code: Unique code for the GOP (e.g., 'GOP1', 'GOP2').
        description: Optional description of the shift.
        is_active: Whether the GOP is currently active.
    """

    id: UUID
    name: str
    code: str
    description: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the display name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Two GOPs are equal if they have the same ID."""
        if not isinstance(other, GOP):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
