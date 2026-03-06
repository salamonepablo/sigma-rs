"""Add maintenance entry, cycles, and email recipients."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create maintenance entry, cycle and recipient models."""

    dependencies = [
        ("tickets", "0011_add_intervencion_nov"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceCycleModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rolling_stock_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("locomotora", "Locomotora"),
                            ("coche_remolcado", "Coche Remolcado"),
                            ("coche_motor", "Coche Motor"),
                        ],
                        verbose_name="Tipo de unidad",
                    ),
                ),
                (
                    "intervention_code",
                    models.CharField(
                        max_length=20,
                        verbose_name="Código de intervención",
                        help_text="Código alineado con Tipos de Intervención",
                    ),
                ),
                (
                    "intervention_name",
                    models.CharField(
                        max_length=100,
                        verbose_name="Nombre de intervención",
                    ),
                ),
                (
                    "trigger_type",
                    models.CharField(
                        max_length=10,
                        choices=[("km", "Kilometers"), ("time", "Time")],
                        verbose_name="Tipo de disparador",
                    ),
                ),
                (
                    "trigger_value",
                    models.PositiveIntegerField(
                        verbose_name="Valor de disparador",
                    ),
                ),
                (
                    "trigger_unit",
                    models.CharField(
                        max_length=10,
                        choices=[("km", "Kilometers"), ("month", "Month")],
                        verbose_name="Unidad de disparador",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Activo"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Fecha de actualización"
                    ),
                ),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_cycles",
                        to="tickets.brandmodel",
                        verbose_name="Marca",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_cycles",
                        to="tickets.locomotivemodelmodel",
                        null=True,
                        blank=True,
                        verbose_name="Modelo",
                        help_text="Modelo específico cuando aplica",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ciclo de mantenimiento",
                "verbose_name_plural": "Ciclos de mantenimiento",
                "db_table": "maintenance_cycle",
                "ordering": ["rolling_stock_type", "brand", "trigger_value"],
            },
        ),
        migrations.CreateModel(
            name="LugarEmailRecipientModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "unit_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("locomotora", "Locomotora"),
                            ("coche_remolcado", "Coche Remolcado"),
                            ("coche_motor", "Coche Motor"),
                        ],
                        verbose_name="Tipo de unidad",
                    ),
                ),
                (
                    "recipient_type",
                    models.CharField(
                        max_length=5,
                        choices=[("to", "Para"), ("cc", "Copia")],
                        verbose_name="Tipo de destinatario",
                    ),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="Email"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Activo"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Fecha de actualización"
                    ),
                ),
                (
                    "lugar",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="mail_recipients",
                        to="tickets.lugarmodel",
                        null=True,
                        blank=True,
                        verbose_name="Lugar",
                        help_text="Lugar específico. Si está vacío, aplica como default.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Destinatario por lugar",
                "verbose_name_plural": "Destinatarios por lugar",
                "db_table": "lugar_email_recipient",
                "ordering": ["unit_type", "recipient_type", "email"],
            },
        ),
        migrations.CreateModel(
            name="MaintenanceEntryModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "entry_datetime",
                    models.DateTimeField(verbose_name="Fecha y hora de ingreso"),
                ),
                (
                    "exit_datetime",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        verbose_name="Fecha y hora de egreso",
                    ),
                ),
                (
                    "trigger_type",
                    models.CharField(
                        max_length=10,
                        choices=[("km", "Kilometers"), ("time", "Time")],
                        null=True,
                        blank=True,
                        verbose_name="Tipo de disparador",
                    ),
                ),
                (
                    "trigger_value",
                    models.PositiveIntegerField(
                        null=True,
                        blank=True,
                        verbose_name="Valor de disparador",
                    ),
                ),
                (
                    "trigger_unit",
                    models.CharField(
                        max_length=10,
                        choices=[("km", "Kilometers"), ("month", "Month")],
                        null=True,
                        blank=True,
                        verbose_name="Unidad de disparador",
                    ),
                ),
                (
                    "suggested_intervention_code",
                    models.CharField(
                        max_length=20,
                        null=True,
                        blank=True,
                        verbose_name="Intervención sugerida",
                    ),
                ),
                (
                    "checklist_tasks",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="Checklist de tareas",
                        help_text="Lista de tareas (una por línea)",
                    ),
                ),
                (
                    "observations",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="Observaciones",
                    ),
                ),
                (
                    "pdf_path",
                    models.CharField(
                        max_length=255,
                        blank=True,
                        null=True,
                        verbose_name="Ruta del PDF",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Fecha de actualización"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_entries",
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        blank=True,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "lugar",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_entries",
                        to="tickets.lugarmodel",
                        null=True,
                        blank=True,
                        verbose_name="Lugar",
                    ),
                ),
                (
                    "maintenance_unit",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_entries",
                        to="tickets.maintenanceunitmodel",
                        null=True,
                        blank=True,
                        verbose_name="Unidad de mantenimiento",
                    ),
                ),
                (
                    "novedad",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_entries",
                        to="tickets.novedadmodel",
                        verbose_name="Novedad",
                    ),
                ),
                (
                    "selected_intervention",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="maintenance_entries",
                        to="tickets.intervenciontipomodel",
                        null=True,
                        blank=True,
                        verbose_name="Intervención seleccionada",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ingreso a mantenimiento",
                "verbose_name_plural": "Ingresos a mantenimiento",
                "db_table": "maintenance_entry",
                "ordering": ["-entry_datetime", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="maintenancecyclemodel",
            index=models.Index(
                fields=["rolling_stock_type", "brand", "model"],
                name="maintenanc_rolling_5b0ce7_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="maintenancecyclemodel",
            index=models.Index(
                fields=["intervention_code"],
                name="maintenanc_interve_0b42c1_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="maintenancecyclemodel",
            constraint=models.UniqueConstraint(
                fields=[
                    "rolling_stock_type",
                    "brand",
                    "model",
                    "intervention_code",
                    "trigger_type",
                    "trigger_value",
                    "trigger_unit",
                ],
                name="uniq_cycle_definition",
            ),
        ),
        migrations.AddIndex(
            model_name="lugaremailrecipientmodel",
            index=models.Index(
                fields=["lugar", "unit_type"],
                name="lugar_emai_lugar_i_4d4b73_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="lugaremailrecipientmodel",
            index=models.Index(
                fields=["email"],
                name="lugar_emai_email_7c3b5c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="maintenanceentrymodel",
            index=models.Index(
                fields=["entry_datetime"],
                name="maintenanc_entry_d_7ad0b3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="maintenanceentrymodel",
            index=models.Index(
                fields=["maintenance_unit"],
                name="maintenanc_mainten_6ddc8a_idx",
            ),
        ),
    ]
