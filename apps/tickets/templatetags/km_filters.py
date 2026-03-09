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
