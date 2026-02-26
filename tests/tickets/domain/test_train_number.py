"""Tests para la entidad TrainNumber (Número de Tren).

Pruebas de dominio para números de tren.
Los números de tren identifican los servicios ferroviarios.
En principio puede ser cualquier número de 4 dígitos.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.train_number import TrainNumber


class TestTrainNumber:
    """Pruebas para la entidad TrainNumber."""

    def test_create_train_number_with_required_fields(self):
        """Verifica que se puede crear un número de tren con campos requeridos."""
        train_id = uuid4()
        train = TrainNumber(id=train_id, number="1234")

        assert train.id == train_id
        assert train.number == "1234"

    def test_create_train_number_with_description(self):
        """Verifica que se puede crear un número de tren con descripción."""
        train = TrainNumber(
            id=uuid4(), number="5678", description="Servicio Constitución - La Plata"
        )

        assert train.description == "Servicio Constitución - La Plata"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        train = TrainNumber(id=uuid4(), number="9012")

        assert train.description is None

    def test_create_train_number_with_route(self):
        """Verifica que se puede crear un número de tren con ruta."""
        train = TrainNumber(id=uuid4(), number="3456", route="Bosques - Constitución")

        assert train.route == "Bosques - Constitución"

    def test_route_defaults_to_none(self):
        """Verifica que route es opcional y por defecto es None."""
        train = TrainNumber(id=uuid4(), number="7890")

        assert train.route is None

    def test_is_active_defaults_to_true(self):
        """Verifica que los números de tren están activos por defecto."""
        train = TrainNumber(id=uuid4(), number="1111")

        assert train.is_active is True

    def test_create_inactive_train_number(self):
        """Verifica que se puede crear un número de tren inactivo."""
        train = TrainNumber(id=uuid4(), number="2222", is_active=False)

        assert train.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de un número de tren."""
        train = TrainNumber(id=uuid4(), number="1234")

        assert str(train) == "1234"

    def test_equality_based_on_id(self):
        """Dos números de tren con el mismo ID son iguales."""
        train_id = uuid4()
        train1 = TrainNumber(id=train_id, number="1234")
        train2 = TrainNumber(id=train_id, number="1234")

        assert train1 == train2

    def test_inequality_for_different_ids(self):
        """Dos números de tren con diferente ID no son iguales."""
        train1 = TrainNumber(id=uuid4(), number="1234")
        train2 = TrainNumber(id=uuid4(), number="1234")

        assert train1 != train2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        train_id = uuid4()
        train1 = TrainNumber(id=train_id, number="1234")
        train2 = TrainNumber(id=train_id, number="1234")

        assert hash(train1) == hash(train2)


class TestTrainNumberFormats:
    """Pruebas con diferentes formatos de números de tren."""

    @pytest.mark.parametrize(
        "number",
        [
            "0001",
            "1234",
            "5678",
            "9999",
        ],
    )
    def test_create_four_digit_train_numbers(self, number: str):
        """Verifica que se pueden crear números de tren de 4 dígitos."""
        train = TrainNumber(id=uuid4(), number=number)

        assert train.number == number
        assert len(train.number) == 4

    def test_create_train_number_with_all_fields(self):
        """Verifica que se puede crear un número de tren con todos los campos."""
        train = TrainNumber(
            id=uuid4(),
            number="1234",
            description="Tren expreso",
            route="Constitución - Alejandro Korn",
            is_active=True,
        )

        assert train.number == "1234"
        assert train.description == "Tren expreso"
        assert train.route == "Constitución - Alejandro Korn"
        assert train.is_active is True
