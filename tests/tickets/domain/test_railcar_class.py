"""Tests para la entidad RailcarClass (Clase de Coche Remolcado).

Pruebas de dominio para clases de coches remolcados.
Clases conocidas Materfer: U, FU, F.
Clases conocidas CNR: CPA, CRA, PUA, PUAD, FS, FG.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.railcar_class import RailcarClass


class TestRailcarClass:
    """Pruebas para la entidad RailcarClass."""

    def test_create_class_with_required_fields(self):
        """Verifica que se puede crear una clase con campos requeridos."""
        class_id = uuid4()
        brand_id = uuid4()
        railcar_class = RailcarClass(
            id=class_id,
            name="U",
            code="U",
            brand_id=brand_id
        )

        assert railcar_class.id == class_id
        assert railcar_class.name == "U"
        assert railcar_class.code == "U"
        assert railcar_class.brand_id == brand_id

    def test_create_class_with_description(self):
        """Verifica que se puede crear una clase con descripción."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name="CPA",
            code="CPA",
            brand_id=uuid4(),
            description="Coche con aire acondicionado, primera clase"
        )

        assert railcar_class.description == "Coche con aire acondicionado, primera clase"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name="U",
            code="U",
            brand_id=uuid4()
        )

        assert railcar_class.description is None

    def test_is_active_defaults_to_true(self):
        """Verifica que las clases están activas por defecto."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name="FU",
            code="FU",
            brand_id=uuid4()
        )

        assert railcar_class.is_active is True

    def test_create_inactive_class(self):
        """Verifica que se puede crear una clase inactiva."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name="F",
            code="F",
            brand_id=uuid4(),
            is_active=False
        )

        assert railcar_class.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de una clase."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name="CPA",
            code="CPA",
            brand_id=uuid4()
        )

        assert str(railcar_class) == "CPA"

    def test_equality_based_on_id(self):
        """Dos clases con el mismo ID son iguales."""
        class_id = uuid4()
        brand_id = uuid4()
        class1 = RailcarClass(id=class_id, name="U", code="U", brand_id=brand_id)
        class2 = RailcarClass(id=class_id, name="U", code="U", brand_id=brand_id)

        assert class1 == class2

    def test_inequality_for_different_ids(self):
        """Dos clases con diferente ID no son iguales."""
        brand_id = uuid4()
        class1 = RailcarClass(id=uuid4(), name="U", code="U", brand_id=brand_id)
        class2 = RailcarClass(id=uuid4(), name="U", code="U", brand_id=brand_id)

        assert class1 != class2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        class_id = uuid4()
        brand_id = uuid4()
        class1 = RailcarClass(id=class_id, name="U", code="U", brand_id=brand_id)
        class2 = RailcarClass(id=class_id, name="U", code="U", brand_id=brand_id)

        assert hash(class1) == hash(class2)


class TestRailcarClassKnownValues:
    """Pruebas con valores conocidos del dominio ferroviario."""

    @pytest.mark.parametrize(
        "name,code,description",
        [
            ("U", "U", "Coche Materfer clase U"),
            ("FU", "FU", "Coche Materfer clase FU (furgón)"),
            ("F", "F", "Coche Materfer clase F"),
        ],
    )
    def test_create_materfer_classes(self, name: str, code: str, description: str):
        """Verifica que se pueden crear clases Materfer conocidas."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name=name,
            code=code,
            brand_id=uuid4(),  # Materfer brand ID
            description=description
        )

        assert railcar_class.name == name
        assert railcar_class.code == code

    @pytest.mark.parametrize(
        "name,code,description",
        [
            ("CPA", "CPA", "Coche CNR primera clase con aire"),
            ("CRA", "CRA", "Coche CNR remolque con aire"),
            ("PUA", "PUA", "Coche CNR pullman con aire"),
            ("PUAD", "PUAD", "Coche CNR pullman con aire - discapacitados"),
            ("FS", "FS", "Coche CNR furgón"),
            ("FG", "FG", "Coche CNR furgón generador"),
        ],
    )
    def test_create_cnr_classes(self, name: str, code: str, description: str):
        """Verifica que se pueden crear clases CNR conocidas."""
        railcar_class = RailcarClass(
            id=uuid4(),
            name=name,
            code=code,
            brand_id=uuid4(),  # CNR brand ID
            description=description
        )

        assert railcar_class.name == name
        assert railcar_class.code == code
