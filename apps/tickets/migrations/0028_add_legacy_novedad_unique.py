"""Add unique constraint for legacy novedades."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0027_alter_kilometragerecordmodel_km_value"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="novedadmodel",
            constraint=models.UniqueConstraint(
                fields=[
                    "maintenance_unit",
                    "legacy_unit_code",
                    "fecha_desde",
                    "fecha_hasta",
                    "intervencion",
                    "legacy_intervencion_codigo",
                    "lugar",
                    "legacy_lugar_codigo",
                ],
                condition=models.Q(is_legacy=True),
                name="uniq_legacy_novedad",
            ),
        ),
    ]
