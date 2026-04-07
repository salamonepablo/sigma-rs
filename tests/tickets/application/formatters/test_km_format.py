"""Pruebas de formato de kilometraje."""

from decimal import Decimal

from apps.tickets.application.formatters.km_format import format_km_eu


def test_format_km_eu_con_decimales():
    """Convierte decimales a formato europeo sin forzar ceros."""
    assert format_km_eu(Decimal("1000.5")) == "1.000,5"


def test_format_km_eu_sin_decimales():
    """No agrega decimales cuando no existen."""
    assert format_km_eu(1000) == "1.000"


def test_format_km_eu_permanece_en_formato_eu():
    """Conserva valores ya en formato europeo."""
    assert format_km_eu("1.000,50") == "1.000,50"


def test_format_km_eu_trunca_decimales():
    """Trunca decimales a dos posiciones sin redondear."""
    assert format_km_eu(Decimal("1000.567")) == "1.000,56"
    assert format_km_eu("1.000,567") == "1.000,56"


def test_format_km_eu_con_nulos():
    """Devuelve cadena vacia para valores nulos."""
    assert format_km_eu(None) == ""
    assert format_km_eu("") == ""
