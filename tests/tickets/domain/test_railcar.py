"""Tests para la entidad Railcar (Coche Remolcado)."""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit
from apps.tickets.domain.entities.railcar import Railcar


class TestRailcar:
    """Pruebas para la entidad Railcar (Coche Remolcado)."""

    def test_is_maintenance_unit_subclass(self):
        """Railcar es subclase de MaintenanceUnit."""
        assert issubclass(Railcar, MaintenanceUnit)

    def test_create_railcar_with_required_fields(self):
        """Se puede crear un coche remolcado con los campos requeridos."""
        rc_id = uuid4()
        rc = Railcar(
            id=rc_id,
            number="U3001",
            brand="Materfer",
            coach_type="U",
        )

        assert rc.id == rc_id
        assert rc.number == "U3001"
        assert rc.brand == "Materfer"
        assert rc.coach_type == "U"
        assert rc.is_active is True  # default

    def test_unit_type_returns_coche_remolcado(self):
        """La propiedad unit_type devuelve 'Coche Remolcado'."""
        rc = Railcar(
            id=uuid4(),
            number="U3001",
            brand="Materfer",
            coach_type="U",
        )

        assert rc.unit_type == "Coche Remolcado"

    def test_str_representation(self):
        """La representación string muestra 'Coche Remolcado' y número."""
        rc = Railcar(
            id=uuid4(),
            number="CPA001",
            brand="CNR",
            coach_type="CPA",
        )

        assert str(rc) == "Coche Remolcado CPA001"

    def test_create_inactive_railcar(self):
        """Se puede crear un coche remolcado inactivo."""
        rc = Railcar(
            id=uuid4(),
            number="U3001",
            brand="Materfer",
            coach_type="U",
            is_active=False,
        )

        assert rc.is_active is False

    def test_equality_based_on_id(self):
        """Dos coches remolcados son iguales si tienen el mismo ID."""
        same_id = uuid4()
        rc1 = Railcar(id=same_id, number="U3001", brand="Materfer", coach_type="U")
        rc2 = Railcar(id=same_id, number="U3002", brand="CNR", coach_type="CPA")

        assert rc1 == rc2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        same_id = uuid4()
        rc1 = Railcar(id=same_id, number="U3001", brand="Materfer", coach_type="U")
        rc2 = Railcar(id=same_id, number="U3002", brand="CNR", coach_type="CPA")

        assert hash(rc1) == hash(rc2)
        assert len({rc1, rc2}) == 1


class TestRailcarTypes:
    """Pruebas para validar tipos de coches remolcados conocidos."""

    @pytest.mark.parametrize(
        "brand,coach_type,number",
        [
            # Materfer
            ("Materfer", "U", "U3001"),
            ("Materfer", "FU", "FU3001"),
            ("Materfer", "F", "F3001"),
            # CNR
            ("CNR", "CPA", "CPA001"),
            ("CNR", "CRA", "CRA001"),
            ("CNR", "PUA", "PUA001"),
            ("CNR", "PUAD", "PUAD001"),
            ("CNR", "FS", "FS001"),
            ("CNR", "FG", "FG001"),
        ],
    )
    def test_create_railcar_with_known_types(
        self, brand: str, coach_type: str, number: str
    ):
        """Se pueden crear coches remolcados con tipos conocidos."""
        rc = Railcar(
            id=uuid4(),
            number=number,
            brand=brand,
            coach_type=coach_type,
        )

        assert rc.brand == brand
        assert rc.coach_type == coach_type
        assert rc.number == number
