"""Backfill rolling_stock_category for existing maintenance units."""

from django.db import migrations
from django.db.models import Q


def backfill_rolling_stock_category(apps, schema_editor):
    maintenance_unit = apps.get_model("tickets", "MaintenanceUnitModel")

    traction_types = ["locomotora", "coche_motor"]
    railcar_type = "coche_remolcado"

    missing_category = Q(rolling_stock_category__isnull=True) | Q(
        rolling_stock_category=""
    )

    maintenance_unit.objects.filter(
        missing_category, unit_type__in=traction_types
    ).update(rolling_stock_category="traccion")
    maintenance_unit.objects.filter(missing_category, unit_type=railcar_type).update(
        rolling_stock_category="ccrr"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0015_add_rolling_stock_category"),
    ]

    operations = [
        migrations.RunPython(
            backfill_rolling_stock_category, migrations.RunPython.noop
        ),
    ]
