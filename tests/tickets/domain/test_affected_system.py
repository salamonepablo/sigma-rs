"""Tests para la entidad AffectedSystem (Sistema Afectado).

Pruebas de dominio para sistemas afectados en fallas de material rodante.
Los sistemas afectados están asociados a un tipo de falla específico.
Ejemplo: Mecánicas -> Motor Diésel, Punta de eje.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.affected_system import AffectedSystem


class TestAffectedSystem:
    """Pruebas para la entidad AffectedSystem."""

    def test_create_affected_system_with_required_fields(self):
        """Verifica que se puede crear un sistema con campos requeridos."""
        system_id = uuid4()
        failure_type_id = uuid4()
        system = AffectedSystem(
            id=system_id,
            name="Motor Diésel",
            code="MD",
            failure_type_id=failure_type_id
        )

        assert system.id == system_id
        assert system.name == "Motor Diésel"
        assert system.code == "MD"
        assert system.failure_type_id == failure_type_id

    def test_create_affected_system_with_description(self):
        """Verifica que se puede crear un sistema con descripción."""
        system = AffectedSystem(
            id=uuid4(),
            name="Motor de tracción",
            code="MT",
            failure_type_id=uuid4(),
            description="Motor eléctrico de tracción principal"
        )

        assert system.description == "Motor eléctrico de tracción principal"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        system = AffectedSystem(
            id=uuid4(),
            name="Sistema de frenos",
            code="SF",
            failure_type_id=uuid4()
        )

        assert system.description is None

    def test_is_active_defaults_to_true(self):
        """Verifica que los sistemas están activos por defecto."""
        system = AffectedSystem(
            id=uuid4(),
            name="Sistema ATS",
            code="ATS",
            failure_type_id=uuid4()
        )

        assert system.is_active is True

    def test_create_inactive_affected_system(self):
        """Verifica que se puede crear un sistema inactivo."""
        system = AffectedSystem(
            id=uuid4(),
            name="Sistema obsoleto",
            code="OBS",
            failure_type_id=uuid4(),
            is_active=False
        )

        assert system.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de un sistema."""
        system = AffectedSystem(
            id=uuid4(),
            name="Motor Diésel",
            code="MD",
            failure_type_id=uuid4()
        )

        assert str(system) == "Motor Diésel"

    def test_equality_based_on_id(self):
        """Dos sistemas con el mismo ID son iguales."""
        system_id = uuid4()
        failure_type_id = uuid4()
        system1 = AffectedSystem(
            id=system_id, name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )
        system2 = AffectedSystem(
            id=system_id, name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )

        assert system1 == system2

    def test_inequality_for_different_ids(self):
        """Dos sistemas con diferente ID no son iguales."""
        failure_type_id = uuid4()
        system1 = AffectedSystem(
            id=uuid4(), name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )
        system2 = AffectedSystem(
            id=uuid4(), name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )

        assert system1 != system2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        system_id = uuid4()
        failure_type_id = uuid4()
        system1 = AffectedSystem(
            id=system_id, name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )
        system2 = AffectedSystem(
            id=system_id, name="Motor Diésel", code="MD", failure_type_id=failure_type_id
        )

        assert hash(system1) == hash(system2)


class TestAffectedSystemByFailureType:
    """Pruebas con sistemas agrupados por tipo de falla."""

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Motor Diésel", "MD"),
            ("Punta de eje", "PE"),
        ],
    )
    def test_create_mechanical_systems(self, name: str, code: str):
        """Verifica sistemas asociados a fallas Mecánicas."""
        system = AffectedSystem(
            id=uuid4(),
            name=name,
            code=code,
            failure_type_id=uuid4()  # Mecánicas failure type ID
        )

        assert system.name == name
        assert system.code == code

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Motor de tracción", "MT"),
            ("Otros sistemas eléctricos", "OSE"),
        ],
    )
    def test_create_electrical_systems(self, name: str, code: str):
        """Verifica sistemas asociados a fallas Eléctricas."""
        system = AffectedSystem(
            id=uuid4(),
            name=name,
            code=code,
            failure_type_id=uuid4()  # Eléctricas failure type ID
        )

        assert system.name == name
        assert system.code == code

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Sistema de frenos", "SF"),
            ("Otros sistemas neumáticos", "OSN"),
        ],
    )
    def test_create_pneumatic_systems(self, name: str, code: str):
        """Verifica sistemas asociados a fallas Neumáticas."""
        system = AffectedSystem(
            id=uuid4(),
            name=name,
            code=code,
            failure_type_id=uuid4()  # Neumáticas failure type ID
        )

        assert system.name == name
        assert system.code == code

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Sistema de control", "SC"),
            ("Otros sistemas electrónicos", "OSEC"),
        ],
    )
    def test_create_electronic_systems(self, name: str, code: str):
        """Verifica sistemas asociados a fallas Electrónicas."""
        system = AffectedSystem(
            id=uuid4(),
            name=name,
            code=code,
            failure_type_id=uuid4()  # Electrónicas failure type ID
        )

        assert system.name == name
        assert system.code == code

    @pytest.mark.parametrize(
        "name,code",
        [
            ("Sistema auxiliar", "SA"),
            ("Otros sistemas", "OS"),
        ],
    )
    def test_create_other_systems(self, name: str, code: str):
        """Verifica sistemas asociados a fallas Otras."""
        system = AffectedSystem(
            id=uuid4(),
            name=name,
            code=code,
            failure_type_id=uuid4()  # Otras failure type ID
        )

        assert system.name == name
        assert system.code == code

    @pytest.mark.parametrize(
        "failure_type_name,system_name,system_code",
        [
            ("ATS", "Sistema ATS", "SATS"),
            ("Hombre Vivo", "Sistema Hombre Vivo", "SHV"),
            ("Hasler", "Sistema Hasler", "SHAS"),
        ],
    )
    def test_create_specialized_systems(
        self, failure_type_name: str, system_name: str, system_code: str
    ):
        """Verifica sistemas especializados (ATS, Hombre Vivo, Hasler)."""
        system = AffectedSystem(
            id=uuid4(),
            name=system_name,
            code=system_code,
            failure_type_id=uuid4()
        )

        assert system.name == system_name
        assert system.code == system_code
