"""Domain entity for AffectedSystem (Sistema Afectado).

Represents a specific system affected by a failure type.
Affected systems are categorized under failure types.
Example: Mecánicas -> Motor Diésel, Punta de eje.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True, eq=False)
class AffectedSystem:
    """A specific system that can be affected by a failure.

    Affected systems are categorized under failure types and represent
    the specific component or subsystem where the failure occurred.

    Known systems by failure type:
        - Mecánicas: Motor Diésel, Punta de eje
        - Eléctricas: Motor de tracción, Otros sistemas eléctricos
        - Neumáticas: Sistema de frenos, Otros sistemas neumáticos
        - Electrónicas: Sistema de control, Otros sistemas electrónicos
        - Otras: Sistema auxiliar, Otros sistemas
        - ATS: Sistema ATS
        - Hombre Vivo: Sistema Hombre Vivo
        - Hasler: Sistema Hasler

    Attributes:
        id: Unique identifier for the affected system.
        name: Display name (e.g., 'Motor Diésel', 'Sistema de frenos').
        code: Unique code for the system (e.g., 'MD', 'SF').
        failure_type_id: Foreign key to the FailureType entity.
        description: Optional description of the system.
        is_active: Whether the system is currently active.
    """

    id: UUID
    name: str
    code: str
    failure_type_id: UUID
    description: str | None = field(default=None)
    is_active: bool = field(default=True)

    def __str__(self) -> str:
        """Return the display name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Two systems are equal if they have the same ID."""
        if not isinstance(other, AffectedSystem):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)
