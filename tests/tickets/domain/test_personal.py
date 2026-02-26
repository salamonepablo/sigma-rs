"""Tests para la entidad Personal (Interviniente).

Pruebas de dominio para el personal de mantenimiento.
El personal interviene en la resolución de tickets y está
asignado a un sector (Locomotoras o Coches Remolcados).
"""

from uuid import uuid4

from apps.tickets.domain.entities.personal import Personal, Sector


class TestPersonal:
    """Pruebas para la entidad Personal."""

    def test_create_personal_with_required_fields(self):
        """Verifica que se puede crear personal con campos requeridos."""
        personal_id = uuid4()
        personal = Personal(
            id=personal_id,
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )

        assert personal.id == personal_id
        assert personal.legajo_sap == "12345"
        assert personal.full_name == "Juan Pérez"
        assert personal.sector == Sector.LOCOMOTORAS

    def test_create_personal_sector_coches_remolcados(self):
        """Verifica que se puede crear personal del sector Coches Remolcados."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="54321",
            full_name="María García",
            sector=Sector.COCHES_REMOLCADOS,
        )

        assert personal.sector == Sector.COCHES_REMOLCADOS

    def test_create_personal_with_cuit(self):
        """Verifica que se puede crear personal con CUIT."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12346",
            full_name="Carlos López",
            sector=Sector.LOCOMOTORAS,
            cuit="20123456789",
        )

        assert personal.cuit == "20123456789"

    def test_cuit_defaults_to_none(self):
        """Verifica que cuit es opcional y por defecto es None."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12347",
            full_name="Ana Rodríguez",
            sector=Sector.LOCOMOTORAS,
        )

        assert personal.cuit is None

    def test_create_personal_with_sector_simaf(self):
        """Verifica que se puede crear personal con sector SIMAF."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12348",
            full_name="Pedro Martínez",
            sector=Sector.COCHES_REMOLCADOS,
            sector_simaf="CCRR Operativa CNR-MTF",
        )

        assert personal.sector_simaf == "CCRR Operativa CNR-MTF"

    def test_sector_simaf_defaults_to_none(self):
        """Verifica que sector_simaf es opcional y por defecto es None."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12349",
            full_name="Laura Fernández",
            sector=Sector.LOCOMOTORAS,
        )

        assert personal.sector_simaf is None

    def test_is_active_defaults_to_true(self):
        """Verifica que el personal está activo por defecto."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12350",
            full_name="Roberto González",
            sector=Sector.LOCOMOTORAS,
        )

        assert personal.is_active is True

    def test_create_inactive_personal(self):
        """Verifica que se puede crear personal inactivo."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12351",
            full_name="Diego Fernández",
            sector=Sector.LOCOMOTORAS,
            is_active=False,
        )

        assert personal.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string del personal."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )

        assert str(personal) == "Juan Pérez (12345)"

    def test_equality_based_on_id(self):
        """Dos personales con el mismo ID son iguales."""
        personal_id = uuid4()
        p1 = Personal(
            id=personal_id,
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )
        p2 = Personal(
            id=personal_id,
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )

        assert p1 == p2

    def test_inequality_for_different_ids(self):
        """Dos personales con diferente ID no son iguales."""
        p1 = Personal(
            id=uuid4(),
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )
        p2 = Personal(
            id=uuid4(),
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )

        assert p1 != p2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        personal_id = uuid4()
        p1 = Personal(
            id=personal_id,
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )
        p2 = Personal(
            id=personal_id,
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
        )

        assert hash(p1) == hash(p2)

    def test_create_personal_with_all_fields(self):
        """Verifica que se puede crear personal con todos los campos."""
        personal = Personal(
            id=uuid4(),
            legajo_sap="12345",
            full_name="Juan Pérez",
            sector=Sector.LOCOMOTORAS,
            cuit="20123456789",
            sector_simaf="Deposito - PMRE Locomotoras",
            is_active=True,
        )

        assert personal.legajo_sap == "12345"
        assert personal.full_name == "Juan Pérez"
        assert personal.sector == Sector.LOCOMOTORAS
        assert personal.cuit == "20123456789"
        assert personal.sector_simaf == "Deposito - PMRE Locomotoras"
        assert personal.is_active is True


class TestSector:
    """Pruebas para el enum Sector."""

    def test_sector_locomotoras_value(self):
        """Verifica el valor del sector Locomotoras."""
        assert Sector.LOCOMOTORAS.value == "locomotora"

    def test_sector_coches_remolcados_value(self):
        """Verifica el valor del sector Coches Remolcados."""
        assert Sector.COCHES_REMOLCADOS.value == "coche_remolcado"

    def test_sector_is_string_enum(self):
        """Verifica que Sector es un string enum."""
        assert isinstance(Sector.LOCOMOTORAS, str)
        assert Sector.LOCOMOTORAS == "locomotora"
