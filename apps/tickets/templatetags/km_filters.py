from django import template

from apps.tickets.application.formatters.km_format import format_km_eu
from apps.tickets.domain.services.maintenance_labels import (
    resolve_maintenance_display_rules,
)

register = template.Library()


@register.filter
def km_format(value):
    """Format number with European thousands separator (dots)."""
    return format_km_eu(value)


@register.simple_tag
def get_maintenance_label(
    unit_type: str | None, brand_code: str | None, model_code: str | None = None
):
    """Return the appropriate maintenance label based on unit type and brand."""
    return resolve_maintenance_display_rules(
        unit_type, brand_code, model_code
    ).history_label


@register.simple_tag
def get_maintenance_display_rules(
    unit_type: str | None,
    brand_code: str | None,
    model_code: str | None = None,
    brand_name: str | None = None,
    unit_number: str | None = None,
):
    """Return maintenance display rules for the unit."""
    return resolve_maintenance_display_rules(
        unit_type,
        brand_code,
        model_code,
        brand_name=brand_name,
        unit_number=unit_number,
    )
