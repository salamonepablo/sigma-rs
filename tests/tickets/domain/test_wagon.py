"""Tests para la entidad Wagon (Vagon)."""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit
from apps.tickets.domain.entities.wagon import Wagon


class TestWagon:
    """Pruebas para la entidad Wagon (Vagon)."""

    def test_is_maintenance_unit_subclass(self):
        """Wagon es subclase de MaintenanceUnit."""
        assert issubclass(Wagon, MaintenanceUnit)

    def test_create_wagon_with_required_fields(self):
        """Se puede crear un vagon con los campos requeridos."""
        wagon_id = uuid4()
        wagon = Wagon(
            id=wagon_id,
            number="BK001",
            wagon_type="BK",
            brand="Carga",
        )

        assert wagon.id == wagon_id
        assert wagon.number == "BK001"
        assert wagon.wagon_type == "BK"
        assert wagon.brand == "Carga"
        assert wagon.is_active is True

    def test_unit_type_returns_vagon(self):
        """La propiedad unit_type devuelve 'Vagon'."""
        wagon = Wagon(
            id=uuid4(),
            number="HOP001",
            wagon_type="Hopper",
            brand="Carga",
        )

        assert wagon.unit_type == "Vagon"

    def test_str_representation(self):
        """La representación string muestra 'Vagon' y número."""
        wagon = Wagon(
            id=uuid4(),
            number="CH001",
            wagon_type="Chata",
            brand="Carga",
        )

        assert str(wagon) == "Vagon CH001"

    def test_create_inactive_wagon(self):
        """Se puede crear un vagon inactivo."""
        wagon = Wagon(
            id=uuid4(),
            number="PL001",
            wagon_type="Plataforma",
            brand="Carga",
            is_active=False,
        )

        assert wagon.is_active is False

    def test_equality_based_on_id(self):
        """Dos vagones son iguales si tienen el mismo ID."""
        same_id = uuid4()
        wagon1 = Wagon(id=same_id, number="BK001", wagon_type="BK", brand="Carga")
        wagon2 = Wagon(id=same_id, number="BK002", wagon_type="BK", brand="Carga")

        assert wagon1 == wagon2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        same_id = uuid4()
        wagon1 = Wagon(id=same_id, number="BK001", wagon_type="BK", brand="Carga")
        wagon2 = Wagon(id=same_id, number="BK002", wagon_type="BK", brand="Carga")

        assert hash(wagon1) == hash(wagon2)
        assert len({wagon1, wagon2}) == 1


class TestWagonTypes:
    """Pruebas para validar tipos de vagones conocidos."""

    @pytest.mark.parametrize(
        "wagon_type,number",
        [
            ("BK", "BK001"),
            ("Hopper", "HOP001"),
            ("Chata", "CHA001"),
            ("Cubierto", "CUB001"),
            ("Plataforma", "PLA001"),
            ("Automovilera", "AUT001"),
            ("Tanque", "TAN001"),
        ],
    )
    def test_create_wagon_with_known_types(self, wagon_type: str, number: str):
        """Se pueden crear vagones con tipos conocidos."""
        wagon = Wagon(
            id=uuid4(),
            number=number,
            wagon_type=wagon_type,
            brand="Carga",
        )

        assert wagon.wagon_type == wagon_type
        assert wagon.number == number
