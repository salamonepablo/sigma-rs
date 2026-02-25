"""Tests para la entidad Locomotive (Locomotora)."""

import pytest
from uuid import uuid4

from apps.tickets.domain.entities.locomotive import Locomotive
from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit


class TestLocomotive:
    """Pruebas para la entidad Locomotive."""

    def test_is_maintenance_unit_subclass(self):
        """Locomotive es subclase de MaintenanceUnit."""
        assert issubclass(Locomotive, MaintenanceUnit)

    def test_create_locomotive_with_required_fields(self):
        """Se puede crear una locomotora con los campos requeridos."""
        loc_id = uuid4()
        loc = Locomotive(
            id=loc_id,
            number="A904",
            brand="GM",
            model="GT22CW",
        )

        assert loc.id == loc_id
        assert loc.number == "A904"
        assert loc.brand == "GM"
        assert loc.model == "GT22CW"
        assert loc.is_active is True  # default

    def test_unit_type_returns_locomotora(self):
        """La propiedad unit_type devuelve 'Locomotora'."""
        loc = Locomotive(
            id=uuid4(),
            number="A904",
            brand="GM",
            model="GT22CW",
        )

        assert loc.unit_type == "Locomotora"

    def test_str_representation(self):
        """La representación string muestra 'Locomotora' y número."""
        loc = Locomotive(
            id=uuid4(),
            number="CKD0001",
            brand="CNR",
            model="8G",
        )

        assert str(loc) == "Locomotora CKD0001"

    def test_create_inactive_locomotive(self):
        """Se puede crear una locomotora inactiva."""
        loc = Locomotive(
            id=uuid4(),
            number="A904",
            brand="GM",
            model="GT22CW",
            is_active=False,
        )

        assert loc.is_active is False

    def test_equality_based_on_id(self):
        """Dos locomotoras son iguales si tienen el mismo ID."""
        same_id = uuid4()
        loc1 = Locomotive(id=same_id, number="A904", brand="GM", model="GT22CW")
        loc2 = Locomotive(id=same_id, number="A905", brand="CNR", model="8G")

        assert loc1 == loc2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        same_id = uuid4()
        loc1 = Locomotive(id=same_id, number="A904", brand="GM", model="GT22CW")
        loc2 = Locomotive(id=same_id, number="A905", brand="CNR", model="8G")

        assert hash(loc1) == hash(loc2)
        assert len({loc1, loc2}) == 1


class TestLocomotiveBrands:
    """Pruebas para validar marcas de locomotoras conocidas."""

    @pytest.mark.parametrize(
        "brand,model,number",
        [
            ("GM", "GT22CW", "A904"),
            ("GM", "GT22CW-2", "A950"),
            ("GM", "G22CW", "A801"),
            ("GM", "G22CU", "A701"),
            ("GM", "GR12", "A501"),
            ("GM", "G12", "A401"),
            ("CNR", "8G", "CKD0001"),
            ("CNR", "8H", "CKD0100"),
        ],
    )
    def test_create_locomotive_with_known_brands(self, brand: str, model: str, number: str):
        """Se pueden crear locomotoras con marcas y modelos conocidos."""
        loc = Locomotive(
            id=uuid4(),
            number=number,
            brand=brand,
            model=model,
        )

        assert loc.brand == brand
        assert loc.model == model
        assert loc.number == number
