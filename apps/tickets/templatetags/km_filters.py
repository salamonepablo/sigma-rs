from django import template

register = template.Library()


@register.filter
def km_format(value):
    """Format number with European thousands separator (dots)."""
    if value is None:
        return ""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value


@register.simple_tag
def get_maintenance_label(unit_type: str | None, brand_code: str | None):
    """Return the appropriate maintenance label based on unit type and brand."""
    if not unit_type or not brand_code:
        return "Última Intervención"

    brand = (brand_code or "").strip().upper()

    if unit_type == "locomotora":
        if brand.startswith("CKD") or brand == "CNR":
            return "Última Revisión (R1-R6)"
        return "Última Numeral (N1-N11)"

    if unit_type == "coche_remolcado":
        if brand in {"CNR"}:
            return "Última Revisión (A1-A4)"
        if brand in {"MATERFER", "MTF"}:
            return "Última RP"
        return "Última Intervención"

    if unit_type == "coche_motor":
        if brand in {"NOHAB"}:
            return "Última RP"
        return "Última Intervención"

    return "Última Intervención"
