"""Kilometer formatting helpers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def format_km_eu(value: object) -> str | None:
    """Format kilometer values using dot as thousands separator."""
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)

    if number == number.to_integral():
        return f"{int(number):,}".replace(",", ".")

    return f"{number:,}".replace(",", ".")
