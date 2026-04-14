from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation


def format_km_eu(value: object) -> str:
    """Format kilometer values using dot as thousands separator."""
    if value is None:
        return ""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)

    quantized = number.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    integer_part = int(quantized)
    formatted_int = f"{integer_part:,}".replace(",", ".")

    decimal_part = abs(quantized - Decimal(integer_part)).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    if decimal_part == 0:
        return formatted_int

    decimal_str = f"{decimal_part:.2f}".split(".")[1].rstrip("0")
    return f"{formatted_int},{decimal_str}"
