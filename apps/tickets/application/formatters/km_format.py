"""Kilometrage formatting helpers."""

from __future__ import annotations

from decimal import Decimal


def format_km_eu(value: Decimal | int | str | None) -> str:
    """Return kilometrage formatted with EU separators.

    Args:
        value: Raw kilometrage value (Decimal, int, str, or None).

    Returns:
        Formatted value using dot thousands and comma decimals. Empty input
        returns an empty string.
    """

    if value is None:
        return ""

    if isinstance(value, Decimal):
        return _format_decimal(value)

    if isinstance(value, int):
        return _format_parts(str(value), None)

    if isinstance(value, str):
        return _format_str(value)

    return str(value)


def _format_decimal(value: Decimal) -> str:
    raw = format(value, "f")
    return _format_numeric_string(raw)


def _format_str(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""

    raw = raw.replace(" ", "")

    if "," in raw:
        integer_part, decimal_part = raw.split(",", 1)
        formatted = _format_parts(integer_part.replace(".", ""), decimal_part)
        return formatted if formatted else raw

    if raw.count(".") == 1 and raw.replace(".", "").isdigit():
        integer_part, decimal_part = raw.split(".", 1)
        formatted = _format_parts(integer_part, decimal_part)
        return formatted if formatted else raw

    integer_only = raw.replace(".", "")
    if integer_only.isdigit():
        formatted = _format_parts(integer_only, None)
        return formatted if formatted else raw

    return raw


def _format_numeric_string(raw: str) -> str:
    sign = ""
    normalized = raw.strip()
    if normalized.startswith("-"):
        sign = "-"
        normalized = normalized[1:]

    if "." in normalized:
        integer_part, decimal_part = normalized.split(".", 1)
    else:
        integer_part, decimal_part = normalized, ""

    formatted = _format_parts(integer_part, decimal_part or None)
    return f"{sign}{formatted}" if formatted else ""


def _format_parts(integer_part: str, decimal_part: str | None) -> str:
    integer_part = integer_part.strip()
    decimal_part = decimal_part.strip() if decimal_part is not None else None

    sign = ""
    if integer_part.startswith("-"):
        sign = "-"
        integer_part = integer_part[1:]

    if integer_part and not integer_part.isdigit():
        return ""
    if decimal_part and not decimal_part.isdigit():
        return ""

    integer_value = int(integer_part or "0")
    formatted_integer = f"{integer_value:,}".replace(",", ".")

    if decimal_part:
        return f"{sign}{formatted_integer},{decimal_part}"
    return f"{sign}{formatted_integer}"
