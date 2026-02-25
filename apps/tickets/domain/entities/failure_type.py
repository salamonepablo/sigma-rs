"""Domain entity for FailureType (Tipo de Falla).

Represents a failure type category for rolling stock issues.
Known types: Mecánicas, Eléctricas, Neumáticas, Electrónicas, Otras, ATS, Hombre Vivo, Hasler.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class FailureType:
    """A failure type category.

    Failure types categorize the nature of issues reported in tickets.
    Each failure type has associated affected systems.

    Known failure types:
        - Mecánicas: Diesel engine, axle tips
        - Eléctricas: Traction motor, electrical systems
        - Neumáticas: Braking system, pneumatic systems
        - Electrónicas: Control system, electronic systems
        - Otras: Auxiliary systems, other systems
        - ATS: ATS system
        - Hombre Vivo: Dead man's switch system
        - Hasler: Hasler system

    Attributes:
        id: Unique identifier for the failure type.
        name: Display name (e.g., 'Mecánicas', 'Eléctricas').
        code: Unique code for the failure type (e.g., 'MEC', 'ELE').
        description: Optional description of the failure type.
        is_active: Whether the failure type is currently active.
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
        """Two failure types are equal if they have the same ID."""
        if not isinstance(other, FailureType):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
