"""Pruebas para el importador de kilometraje Access."""

from decimal import Decimal

import pytest

from apps.tickets.infrastructure.services.access_kilometrage_importer import (
    AccessKilometrageImporter,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("204.8", Decimal("204.8")),
        ("266.4", Decimal("266.4")),
        ("204,80", Decimal("204.80")),
        ("1.234,56", Decimal("1234.56")),
        ("1234", Decimal("1234")),
        ("", None),
        (None, None),
        ("abc", None),
    ],
)
def test_parse_decimal_regresion(raw_value, expected):
    """Parsea decimales con formatos US y europeo sin romper regresiones."""
    assert AccessKilometrageImporter._parse_decimal(raw_value) == expected
