"""Tests para la entidad MaintenanceUnit (Unidad de Mantenimiento)."""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


# Subclase concreta para testing - NO usar @dataclass para heredar __eq__ y __hash__
class ConcreteUnit(MaintenanceUnit):
    """Subclase concreta de MaintenanceUnit para testing."""

    @property
    def unit_type(self) -> str:
        return "TestUnit"


class TestMaintenanceUnit:
    """Pruebas para la clase base abstracta MaintenanceUnit."""

    def test_cannot_instantiate_directly(self):
        """No se puede instanciar MaintenanceUnit directamente por ser abstracta."""
        with pytest.raises(TypeError):
            MaintenanceUnit(
                id=uuid4(),
                number="A001",
                is_active=True,
            )

    def test_subclass_must_implement_unit_type(self):
        """Las subclases deben implementar la propiedad unit_type."""
        unit = ConcreteUnit(
            id=uuid4(),
            number="TEST001",
            is_active=True,
        )

        assert unit.unit_type == "TestUnit"

    def test_has_required_attributes(self):
        """Las subclases tienen los atributos requeridos: id, number, is_active."""
        unit_id = uuid4()
        unit = ConcreteUnit(
            id=unit_id,
            number="TEST001",
            is_active=True,
        )

        assert unit.id == unit_id
        assert unit.number == "TEST001"
        assert unit.is_active is True

    def test_is_active_defaults_to_true(self):
        """El atributo is_active debe tener valor por defecto True."""
        unit = ConcreteUnit(
            id=uuid4(),
            number="TEST001",
        )

        assert unit.is_active is True

    def test_str_representation(self):
        """La representación string muestra tipo y número de unidad."""
        unit = ConcreteUnit(
            id=uuid4(),
            number="TEST001",
        )

        assert str(unit) == "TestUnit TEST001"

    def test_equality_based_on_id(self):
        """Dos unidades son iguales si tienen el mismo ID."""
        same_id = uuid4()
        unit1 = ConcreteUnit(id=same_id, number="TEST001")
        unit2 = ConcreteUnit(id=same_id, number="TEST002")

        assert unit1 == unit2

    def test_inequality_for_different_ids(self):
        """Dos unidades con diferente ID no son iguales."""
        unit1 = ConcreteUnit(id=uuid4(), number="TEST001")
        unit2 = ConcreteUnit(id=uuid4(), number="TEST001")

        assert unit1 != unit2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID para poder usar en sets y dicts."""
        same_id = uuid4()
        unit1 = ConcreteUnit(id=same_id, number="TEST001")
        unit2 = ConcreteUnit(id=same_id, number="TEST002")

        # Si tienen mismo ID, deberían poder estar en un set como uno solo
        units_set = {unit1, unit2}
        assert len(units_set) == 1
