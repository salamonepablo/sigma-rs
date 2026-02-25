"""Tests para la entidad Brand (Marca).

Pruebas de dominio para marcas de material rodante.
Marcas conocidas: CNR (Dalian), GM (General Motors), Materfer.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.brand import Brand


class TestBrand:
    """Pruebas para la entidad Brand."""

    def test_create_brand_with_required_fields(self):
        """Verifica que se puede crear una marca con campos requeridos."""
        brand_id = uuid4()
        brand = Brand(id=brand_id, name="GM", code="GM")

        assert brand.id == brand_id
        assert brand.name == "GM"
        assert brand.code == "GM"

    def test_create_brand_with_full_name(self):
        """Verifica que se puede crear una marca con nombre completo."""
        brand = Brand(
            id=uuid4(),
            name="CNR",
            code="CNR",
            full_name="China CNR Corporation (Dalian)"
        )

        assert brand.full_name == "China CNR Corporation (Dalian)"

    def test_full_name_defaults_to_none(self):
        """Verifica que full_name es opcional y por defecto es None."""
        brand = Brand(id=uuid4(), name="GM", code="GM")

        assert brand.full_name is None

    def test_is_active_defaults_to_true(self):
        """Verifica que las marcas están activas por defecto."""
        brand = Brand(id=uuid4(), name="Materfer", code="MAT")

        assert brand.is_active is True

    def test_create_inactive_brand(self):
        """Verifica que se puede crear una marca inactiva."""
        brand = Brand(id=uuid4(), name="OtraMarca", code="OM", is_active=False)

        assert brand.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de una marca."""
        brand = Brand(id=uuid4(), name="GM", code="GM")

        assert str(brand) == "GM"

    def test_str_with_full_name(self):
        """Verifica que str usa el nombre corto, no el completo."""
        brand = Brand(
            id=uuid4(),
            name="CNR",
            code="CNR",
            full_name="China CNR Corporation"
        )

        assert str(brand) == "CNR"

    def test_equality_based_on_id(self):
        """Dos marcas con el mismo ID son iguales."""
        brand_id = uuid4()
        brand1 = Brand(id=brand_id, name="GM", code="GM")
        brand2 = Brand(id=brand_id, name="GM", code="GM")

        assert brand1 == brand2

    def test_inequality_for_different_ids(self):
        """Dos marcas con diferente ID no son iguales."""
        brand1 = Brand(id=uuid4(), name="GM", code="GM")
        brand2 = Brand(id=uuid4(), name="GM", code="GM")

        assert brand1 != brand2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        brand_id = uuid4()
        brand1 = Brand(id=brand_id, name="GM", code="GM")
        brand2 = Brand(id=brand_id, name="GM", code="GM")

        assert hash(brand1) == hash(brand2)


class TestBrandKnownValues:
    """Pruebas con valores conocidos del dominio ferroviario."""

    @pytest.mark.parametrize(
        "name,code,full_name",
        [
            ("GM", "GM", "General Motors"),
            ("CNR", "CNR", "China CNR Corporation (Dalian)"),
            ("Materfer", "MAT", "Material Ferroviario S.A."),
        ],
    )
    def test_create_known_brands(self, name: str, code: str, full_name: str):
        """Verifica que se pueden crear las marcas conocidas del sistema."""
        brand = Brand(id=uuid4(), name=name, code=code, full_name=full_name)

        assert brand.name == name
        assert brand.code == code
        assert brand.full_name == full_name
