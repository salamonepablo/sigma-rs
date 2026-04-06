"""Pruebas de filtros de kilometraje."""

from decimal import Decimal

from apps.tickets.templatetags.km_filters import km_format


def test_km_format_con_decimal():
    """Formatea decimales con separadores europeos."""
    assert km_format(Decimal("1000.5")) == "1.000,5"


def test_km_format_con_enteros():
    """Formatea enteros sin agregar decimales."""
    assert km_format(1000) == "1.000"


def test_km_format_con_formato_eu():
    """Respeta valores ya formateados en EU."""
    assert km_format("1.000,50") == "1.000,50"


def test_km_format_con_nulos():
    """Devuelve cadena vacia para nulos."""
    assert km_format(None) == ""
    assert km_format("") == ""
