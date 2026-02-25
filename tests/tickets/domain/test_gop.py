"""Tests para la entidad GOP (Guardia Operativa).

Pruebas de dominio para guardias operativas (turnos de trabajo).
Las GOPs representan los turnos de personal de mantenimiento.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.gop import GOP


class TestGOP:
    """Pruebas para la entidad GOP."""

    def test_create_gop_with_required_fields(self):
        """Verifica que se puede crear una GOP con campos requeridos."""
        gop_id = uuid4()
        gop = GOP(
            id=gop_id,
            name="GOP 1",
            code="GOP1"
        )

        assert gop.id == gop_id
        assert gop.name == "GOP 1"
        assert gop.code == "GOP1"

    def test_create_gop_with_description(self):
        """Verifica que se puede crear una GOP con descripción."""
        gop = GOP(
            id=uuid4(),
            name="GOP 1",
            code="GOP1",
            description="Guardia Operativa turno mañana"
        )

        assert gop.description == "Guardia Operativa turno mañana"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        gop = GOP(
            id=uuid4(),
            name="GOP 2",
            code="GOP2"
        )

        assert gop.description is None

    def test_is_active_defaults_to_true(self):
        """Verifica que las GOPs están activas por defecto."""
        gop = GOP(
            id=uuid4(),
            name="GOP 3",
            code="GOP3"
        )

        assert gop.is_active is True

    def test_create_inactive_gop(self):
        """Verifica que se puede crear una GOP inactiva."""
        gop = GOP(
            id=uuid4(),
            name="GOP Antigua",
            code="GOPA",
            is_active=False
        )

        assert gop.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de una GOP."""
        gop = GOP(
            id=uuid4(),
            name="GOP 1",
            code="GOP1"
        )

        assert str(gop) == "GOP 1"

    def test_equality_based_on_id(self):
        """Dos GOPs con el mismo ID son iguales."""
        gop_id = uuid4()
        gop1 = GOP(id=gop_id, name="GOP 1", code="GOP1")
        gop2 = GOP(id=gop_id, name="GOP 1", code="GOP1")

        assert gop1 == gop2

    def test_inequality_for_different_ids(self):
        """Dos GOPs con diferente ID no son iguales."""
        gop1 = GOP(id=uuid4(), name="GOP 1", code="GOP1")
        gop2 = GOP(id=uuid4(), name="GOP 1", code="GOP1")

        assert gop1 != gop2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        gop_id = uuid4()
        gop1 = GOP(id=gop_id, name="GOP 1", code="GOP1")
        gop2 = GOP(id=gop_id, name="GOP 1", code="GOP1")

        assert hash(gop1) == hash(gop2)


class TestGOPKnownValues:
    """Pruebas con valores de GOPs típicas."""

    @pytest.mark.parametrize(
        "name,code",
        [
            ("GOP 1", "GOP1"),
            ("GOP 2", "GOP2"),
            ("GOP 3", "GOP3"),
            ("GOP 4", "GOP4"),
        ],
    )
    def test_create_typical_gops(self, name: str, code: str):
        """Verifica que se pueden crear GOPs con nombres típicos."""
        gop = GOP(
            id=uuid4(),
            name=name,
            code=code
        )

        assert gop.name == name
        assert gop.code == code
