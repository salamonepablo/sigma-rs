"""Add NOV intervention type for manual novedades."""

from django.db import migrations


def add_nov_intervencion(apps, schema_editor):
    intervencion_model = apps.get_model("tickets", "IntervencionTipoModel")
    intervencion_model.objects.get_or_create(
        codigo="NOV",
        defaults={
            "descripcion": "Novedad",
            "clase": "DET",
        },
    )


def remove_nov_intervencion(apps, schema_editor):
    intervencion_model = apps.get_model("tickets", "IntervencionTipoModel")
    intervencion_model.objects.filter(codigo="NOV").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0010_remove_brand_from_railcar_class"),
    ]

    operations = [
        migrations.RunPython(add_nov_intervencion, remove_nov_intervencion),
    ]
