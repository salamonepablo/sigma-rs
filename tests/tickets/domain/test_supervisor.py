"""Tests para la entidad Supervisor.

Pruebas de dominio para supervisores de mantenimiento.
Los supervisores son responsables de coordinar y supervisar
el trabajo de las GOPs.
"""

from uuid import uuid4

from apps.tickets.domain.entities.supervisor import Supervisor


class TestSupervisor:
    """Pruebas para la entidad Supervisor."""

    def test_create_supervisor_with_required_fields(self):
        """Verifica que se puede crear un supervisor con campos requeridos."""
        supervisor_id = uuid4()
        supervisor = Supervisor(
            id=supervisor_id, name="Juan Pérez", employee_number="12345"
        )

        assert supervisor.id == supervisor_id
        assert supervisor.name == "Juan Pérez"
        assert supervisor.employee_number == "12345"

    def test_create_supervisor_with_email(self):
        """Verifica que se puede crear un supervisor con email."""
        supervisor = Supervisor(
            id=uuid4(),
            name="María García",
            employee_number="12346",
            email="mgarcia@empresa.com",
        )

        assert supervisor.email == "mgarcia@empresa.com"

    def test_email_defaults_to_none(self):
        """Verifica que email es opcional y por defecto es None."""
        supervisor = Supervisor(
            id=uuid4(), name="Carlos López", employee_number="12347"
        )

        assert supervisor.email is None

    def test_create_supervisor_with_phone(self):
        """Verifica que se puede crear un supervisor con teléfono."""
        supervisor = Supervisor(
            id=uuid4(),
            name="Ana Rodríguez",
            employee_number="12348",
            phone="+54 11 1234-5678",
        )

        assert supervisor.phone == "+54 11 1234-5678"

    def test_phone_defaults_to_none(self):
        """Verifica que phone es opcional y por defecto es None."""
        supervisor = Supervisor(
            id=uuid4(), name="Pedro Martínez", employee_number="12349"
        )

        assert supervisor.phone is None

    def test_is_active_defaults_to_true(self):
        """Verifica que los supervisores están activos por defecto."""
        supervisor = Supervisor(
            id=uuid4(), name="Laura Fernández", employee_number="12350"
        )

        assert supervisor.is_active is True

    def test_create_inactive_supervisor(self):
        """Verifica que se puede crear un supervisor inactivo."""
        supervisor = Supervisor(
            id=uuid4(),
            name="Roberto González",
            employee_number="12351",
            is_active=False,
        )

        assert supervisor.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de un supervisor."""
        supervisor = Supervisor(id=uuid4(), name="Juan Pérez", employee_number="12345")

        assert str(supervisor) == "Juan Pérez"

    def test_equality_based_on_id(self):
        """Dos supervisores con el mismo ID son iguales."""
        supervisor_id = uuid4()
        sup1 = Supervisor(id=supervisor_id, name="Juan Pérez", employee_number="12345")
        sup2 = Supervisor(id=supervisor_id, name="Juan Pérez", employee_number="12345")

        assert sup1 == sup2

    def test_inequality_for_different_ids(self):
        """Dos supervisores con diferente ID no son iguales."""
        sup1 = Supervisor(id=uuid4(), name="Juan Pérez", employee_number="12345")
        sup2 = Supervisor(id=uuid4(), name="Juan Pérez", employee_number="12345")

        assert sup1 != sup2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        supervisor_id = uuid4()
        sup1 = Supervisor(id=supervisor_id, name="Juan Pérez", employee_number="12345")
        sup2 = Supervisor(id=supervisor_id, name="Juan Pérez", employee_number="12345")

        assert hash(sup1) == hash(sup2)

    def test_create_supervisor_with_all_fields(self):
        """Verifica que se puede crear un supervisor con todos los campos."""
        supervisor = Supervisor(
            id=uuid4(),
            name="Juan Pérez",
            employee_number="12345",
            email="jperez@empresa.com",
            phone="+54 11 1234-5678",
            is_active=True,
        )

        assert supervisor.name == "Juan Pérez"
        assert supervisor.employee_number == "12345"
        assert supervisor.email == "jperez@empresa.com"
        assert supervisor.phone == "+54 11 1234-5678"
        assert supervisor.is_active is True
