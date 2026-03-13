from django import template

from apps.tickets.domain.services.maintenance_labels import (
    resolve_maintenance_display_rules,
)

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
    return resolve_maintenance_display_rules(unit_type, brand_code).history_label
