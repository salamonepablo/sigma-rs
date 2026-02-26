"""Tests para la entidad FailureType (Tipo de Falla).

Pruebas de dominio para tipos de fallas en material rodante.
Tipos conocidos: Mecánicas, Eléctricas, Neumáticas, Electrónicas,
Otras, ATS, Hombre Vivo, Hasler.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.failure_type import FailureType


class TestFailureType:
    """Pruebas para la entidad FailureType."""

    def test_create_failure_type_with_required_fields(self):
        """Verifica que se puede crear un tipo de falla con campos requeridos."""
        type_id = uuid4()
        failure_type = FailureType(
            id=type_id,
            name="Mecánicas",
            code="MEC"
        )

        assert failure_type.id == type_id
        assert failure_type.name == "Mecánicas"
        assert failure_type.code == "MEC"

    def test_create_failure_type_with_description(self):
        """Verifica que se puede crear un tipo de falla con descripción."""
        failure_type = FailureType(
            id=uuid4(),
            name="Eléctricas",
            code="ELE",
            description="Fallas relacionadas con sistemas eléctricos"
        )

        assert failure_type.description == "Fallas relacionadas con sistemas eléctricos"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        failure_type = FailureType(
            id=uuid4(),
            name="Neumáticas",
            code="NEU"
        )

        assert failure_type.description is None

    def test_is_active_defaults_to_true(self):
        """Verifica que los tipos de falla están activos por defecto."""
        failure_type = FailureType(
            id=uuid4(),
            name="ATS",
            code="ATS"
        )

        assert failure_type.is_active is True

    def test_create_inactive_failure_type(self):
        """Verifica que se puede crear un tipo de falla inactivo."""
        failure_type = FailureType(
            id=uuid4(),
            name="Obsoleto",
            code="OBS",
            is_active=False
        )

        assert failure_type.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de un tipo de falla."""
        failure_type = FailureType(
            id=uuid4(),
            name="Mecánicas",
            code="MEC"
        )

        assert str(failure_type) == "Mecánicas"

    def test_equality_based_on_id(self):
        """Dos tipos de falla con el mismo ID son iguales."""
        type_id = uuid4()
        type1 = FailureType(id=type_id, name="Mecánicas", code="MEC")
        type2 = FailureType(id=type_id, name="Mecánicas", code="MEC")

        assert type1 == type2

    def test_inequality_for_different_ids(self):
        """Dos tipos de falla con diferente ID no son iguales."""
        type1 = FailureType(id=uuid4(), name="Mecánicas", code="MEC")
        type2 = FailureType(id=uuid4(), name="Mecánicas", code="MEC")

        assert type1 != type2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        type_id = uuid4()
        type1 = FailureType(id=type_id, name="Mecánicas", code="MEC")
        type2 = FailureType(id=type_id, name="Mecánicas", code="MEC")

        assert hash(type1) == hash(type2)


class TestFailureTypeKnownValues:
    """Pruebas con valores conocidos del dominio ferroviario."""

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Mecánicas", "MEC"),
            ("Eléctricas", "ELE"),
            ("Neumáticas", "NEU"),
            ("Electrónicas", "ECO"),
            ("Otras", "OTR"),
            ("ATS", "ATS"),
            ("Hombre Vivo", "HV"),
            ("Hasler", "HAS"),
        ],
    )
    def test_create_known_failure_types(self, name: str, code: str):
        """Verifica que se pueden crear los tipos de falla conocidos."""
        failure_type = FailureType(
            id=uuid4(),
            name=name,
            code=code
        )

        assert failure_type.name == name
        assert failure_type.code == code
