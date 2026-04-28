"""Deduplicate novedades by business key and add uniqueness constraint."""

from django.db import migrations, models


def dedupe_novedad_business_key(apps, schema_editor):
    """Keep one row per business key, prioritizing manual records."""

    NovedadModel = apps.get_model("tickets", "NovedadModel")

    rows = (
        NovedadModel.objects.filter(
            maintenance_unit_id__isnull=False,
            fecha_desde__isnull=False,
            intervencion_id__isnull=False,
        )
        .order_by(
            "maintenance_unit_id",
            "fecha_desde",
            "intervencion_id",
            "is_legacy",
            "created_at",
            "id",
        )
        .values_list(
            "id",
            "maintenance_unit_id",
            "fecha_desde",
            "intervencion_id",
        )
    )

    seen_keys = set()
    ids_to_delete = []
    for (
        novedad_id,
        maintenance_unit_id,
        fecha_desde,
        intervencion_id,
    ) in rows.iterator():
        key = (maintenance_unit_id, fecha_desde, intervencion_id)
        if key in seen_keys:
            ids_to_delete.append(novedad_id)
            continue
        seen_keys.add(key)

    if ids_to_delete:
        NovedadModel.objects.filter(id__in=ids_to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0032_novedadmodel_is_exported_novedadmodel_legacy_id"),
    ]

    operations = [
        migrations.RunPython(
            dedupe_novedad_business_key,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="novedadmodel",
            constraint=models.UniqueConstraint(
                fields=["maintenance_unit", "fecha_desde", "intervencion"],
                condition=models.Q(
                    maintenance_unit__isnull=False,
                    fecha_desde__isnull=False,
                    intervencion__isnull=False,
                ),
                name="uniq_novedad_business_key",
            ),
        ),
    ]
