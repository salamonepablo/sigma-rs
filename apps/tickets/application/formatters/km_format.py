from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation


def format_km_eu(value: object) -> str:
    """Format kilometer values using dot as thousands separator and comma as decimal."""
    if value is None:
        return ""
    raw = str(value)
    if not raw:
        return ""

    if "," in raw:
        # European-format string: "1.000,567" — count original decimal places
        decimal_digits = len(raw.split(",")[1])
        try:
            number = Decimal(raw.replace(".", "").replace(",", "."))
        except (InvalidOperation, ValueError):
            return raw
    else:
        try:
            number = Decimal(raw)
        except (InvalidOperation, ValueError):
            return raw
        sign, digits, exponent = number.as_tuple()
        decimal_digits = -exponent if exponent < 0 else 0

    precision = min(decimal_digits, 2)

    integer_part = int(number.to_integral_value(rounding=ROUND_DOWN))
    formatted_int = f"{integer_part:,}".replace(",", ".")

    if precision == 0:
        return formatted_int

    quant_str = "0." + "0" * precision
    quantized = number.quantize(Decimal(quant_str), rounding=ROUND_DOWN)
    decimal_str = str(quantized).split(".")[1]
    return f"{formatted_int},{decimal_str}"
