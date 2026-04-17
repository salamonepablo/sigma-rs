"""Add AccessSyncLogModel to track scheduled and manual sync history."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0030_add_observaciones_egreso_to_novedad"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessSyncLogModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "ran_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Ejecutado"),
                ),
                (
                    "trigger",
                    models.CharField(max_length=20, verbose_name="Disparador"),
                ),
                (
                    "novedades_inserted",
                    models.IntegerField(default=0, verbose_name="Novedades nuevas"),
                ),
                (
                    "novedades_duplicates",
                    models.IntegerField(
                        default=0, verbose_name="Novedades duplicadas"
                    ),
                ),
                (
                    "kilometrage_inserted",
                    models.IntegerField(default=0, verbose_name="Km insertados"),
                ),
                (
                    "duration_seconds",
                    models.FloatField(default=0, verbose_name="Duración (s)"),
                ),
                (
                    "status",
                    models.CharField(
                        default="ok", max_length=20, verbose_name="Estado"
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, default="", verbose_name="Error"),
                ),
            ],
            options={
                "verbose_name": "Log de sync Access",
                "verbose_name_plural": "Logs de sync Access",
                "db_table": "access_sync_log",
                "ordering": ["-ran_at"],
            },
        ),
    ]
