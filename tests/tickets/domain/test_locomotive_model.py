"""Tests para la entidad LocomotiveModel (Modelo de Locomotora).

Pruebas de dominio para modelos de locomotoras.
Modelos conocidos GM: GT22CW, GT22CW-2, G22CW, G22CU, GR12, G12.
Modelos conocidos CNR: 8G, 8H.
"""

from uuid import uuid4

import pytest

from apps.tickets.domain.entities.locomotive_model import LocomotiveModel


class TestLocomotiveModel:
    """Pruebas para la entidad LocomotiveModel."""

    def test_create_model_with_required_fields(self):
        """Verifica que se puede crear un modelo con campos requeridos."""
        model_id = uuid4()
        brand_id = uuid4()
        model = LocomotiveModel(
            id=model_id, name="GT22CW", code="GT22CW", brand_id=brand_id
        )

        assert model.id == model_id
        assert model.name == "GT22CW"
        assert model.code == "GT22CW"
        assert model.brand_id == brand_id

    def test_create_model_with_description(self):
        """Verifica que se puede crear un modelo con descripción."""
        model = LocomotiveModel(
            id=uuid4(),
            name="GT22CW",
            code="GT22CW",
            brand_id=uuid4(),
            description="Locomotora diésel-eléctrica de 2200 HP",
        )

        assert model.description == "Locomotora diésel-eléctrica de 2200 HP"

    def test_description_defaults_to_none(self):
        """Verifica que description es opcional y por defecto es None."""
        model = LocomotiveModel(
            id=uuid4(), name="GT22CW", code="GT22CW", brand_id=uuid4()
        )

        assert model.description is None

    def test_is_active_defaults_to_true(self):
        """Verifica que los modelos están activos por defecto."""
        model = LocomotiveModel(id=uuid4(), name="8G", code="8G", brand_id=uuid4())

        assert model.is_active is True

    def test_create_inactive_model(self):
        """Verifica que se puede crear un modelo inactivo."""
        model = LocomotiveModel(
            id=uuid4(), name="G12", code="G12", brand_id=uuid4(), is_active=False
        )

        assert model.is_active is False

    def test_str_representation(self):
        """Verifica la representación en string de un modelo."""
        model = LocomotiveModel(
            id=uuid4(), name="GT22CW", code="GT22CW", brand_id=uuid4()
        )

        assert str(model) == "GT22CW"

    def test_equality_based_on_id(self):
        """Dos modelos con el mismo ID son iguales."""
        model_id = uuid4()
        brand_id = uuid4()
        model1 = LocomotiveModel(
            id=model_id, name="GT22CW", code="GT22CW", brand_id=brand_id
        )
        model2 = LocomotiveModel(
            id=model_id, name="GT22CW", code="GT22CW", brand_id=brand_id
        )

        assert model1 == model2

    def test_inequality_for_different_ids(self):
        """Dos modelos con diferente ID no son iguales."""
        brand_id = uuid4()
        model1 = LocomotiveModel(
            id=uuid4(), name="GT22CW", code="GT22CW", brand_id=brand_id
        )
        model2 = LocomotiveModel(
            id=uuid4(), name="GT22CW", code="GT22CW", brand_id=brand_id
        )

        assert model1 != model2

    def test_hash_based_on_id(self):
        """El hash se basa en el ID."""
        model_id = uuid4()
        brand_id = uuid4()
        model1 = LocomotiveModel(
            id=model_id, name="GT22CW", code="GT22CW", brand_id=brand_id
        )
        model2 = LocomotiveModel(
            id=model_id, name="GT22CW", code="GT22CW", brand_id=brand_id
        )

        assert hash(model1) == hash(model2)


class TestLocomotiveModelKnownValues:
    """Pruebas con valores conocidos del dominio ferroviario."""

    @pytest.mark.parametrize(
        "name,code",
        [
            ("GT22CW", "GT22CW"),
            ("GT22CW-2", "GT22CW2"),
            ("G22CW", "G22CW"),
            ("G22CU", "G22CU"),
            ("GR12", "GR12"),
            ("G12", "G12"),
        ],
    )
    def test_create_gm_models(self, name: str, code: str):
        """Verifica que se pueden crear modelos GM conocidos."""
        model = LocomotiveModel(
            id=uuid4(),
            name=name,
            code=code,
            brand_id=uuid4(),  # GM brand ID
        )

        assert model.name == name
        assert model.code == code

    @pytest.mark.parametrize(
        "name,code",
        [
            ("8G", "8G"),
            ("8H", "8H"),
        ],
    )
    def test_create_cnr_models(self, name: str, code: str):
        """Verifica que se pueden crear modelos CNR conocidos."""
        model = LocomotiveModel(
            id=uuid4(),
            name=name,
            code=code,
            brand_id=uuid4(),  # CNR brand ID
        )

        assert model.name == name
        assert model.code == code
