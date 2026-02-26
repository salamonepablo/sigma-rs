"""Tests para la entidad Motorcoach (Coche Motor)."""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit
from apps.tickets.domain.entities.motorcoach import Motorcoach


class TestMotorcoach:
    """Pruebas para la entidad Motorcoach (Coche Motor)."""

    def test_is_maintenance_unit_subclass(self):
        """Motorcoach es subclase de MaintenanceUnit."""
        assert issubclass(Motorcoach, MaintenanceUnit)

    def test_create_motorcoach_with_required_fields(self):
        """Se puede crear un coche motor con los campos requeridos."""
        cm_id = uuid4()
        cm = Motorcoach(
            id=cm_id,
            number="CM001",
            brand="CNR",
            model="CKD",
            configuration="CM-CM",
        )

        assert cm.id == cm_id
        assert cm.number == "CM001"
        assert cm.brand == "CNR"
        assert cm.model == "CKD"
        assert cm.configuration == "CM-CM"
        assert cm.is_active is True  # default

    def test_unit_type_returns_coche_motor(self):
        """La propiedad unit_type devuelve 'Coche Motor'."""
        cm = Motorcoach(
            id=uuid4(),
            number="CM001",
            brand="CNR",
            model="CKD",
            configuration="CM-CM",
        )

        assert cm.unit_type == "Coche Motor"

    def test_str_representation(self):
        """La representación string muestra 'Coche Motor' y número."""
        cm = Motorcoach(
            id=uuid4(),
            number="CM002",
            brand="CNR",
            model="CKD",
            configuration="CM-R-CM",
        )

        assert str(cm) == "Coche Motor CM002"

    def test_create_inactive_motorcoach(self):
        """Se puede crear un coche motor inactivo."""
        cm = Motorcoach(
            id=uuid4(),
            number="CM001",
            brand="CNR",
            model="CKD",
            configuration="CM-CM",
            is_active=False,
        )

        assert cm.is_active is False

    def test_equality_based_on_id(self):
        """Dos coches motor son iguales si tienen el mismo ID."""
        same_id = uuid4()
        cm1 = Motorcoach(
            id=same_id, number="CM001", brand="CNR", model="CKD", configuration="CM-CM"
        )
        cm2 = Motorcoach(
            id=same_id,
            number="CM002",
            brand="CNR",
            model="CKD",
            configuration="CM-R-CM",
        )

        assert cm1 == cm2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        same_id = uuid4()
        cm1 = Motorcoach(
            id=same_id, number="CM001", brand="CNR", model="CKD", configuration="CM-CM"
        )
        cm2 = Motorcoach(
            id=same_id,
            number="CM002",
            brand="CNR",
            model="CKD",
            configuration="CM-R-CM",
        )

        assert hash(cm1) == hash(cm2)
        assert len({cm1, cm2}) == 1


class TestMotorcoachConfigurations:
    """Pruebas para validar configuraciones de coches motor conocidas."""

    @pytest.mark.parametrize(
        "configuration,description",
        [
            ("CM-CM", "Dos coches motor acoplados"),
            ("CM-R-CM", "Dos coches motor con remolque intermedio"),
        ],
    )
    def test_create_motorcoach_with_known_configurations(
        self, configuration: str, description: str
    ):
        """Se pueden crear coches motor con configuraciones conocidas."""
        cm = Motorcoach(
            id=uuid4(),
            number="CM001",
            brand="CNR",
            model="CKD",
            configuration=configuration,
        )

        assert cm.configuration == configuration
