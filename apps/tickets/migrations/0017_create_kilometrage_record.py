"""Create kilometrage records and backfill from legacy files."""

import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import migrations, models


def _parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


def load_kilometrage_from_legacy(apps, schema_editor):
    if os.environ.get("SKIP_KILOMETRAGE_IMPORT") == "1":
        return
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    record_model = apps.get_model("tickets", "KilometrageRecordModel")
    maintenance_unit = apps.get_model("tickets", "MaintenanceUnitModel")

    base_path = Path(settings.BASE_DIR) / "context" / "db-legacy"
    file_specs = [
        ("KilometrajeLocs.txt", "Locs"),
        ("Kilometraje_CCRR.txt", "Coche"),
    ]
    batch_size = 1000

    for file_name, unit_field in file_specs:
        file_path = base_path / file_name
        if not file_path.exists():
            continue
        batch = []
        processed = 0
        inserted = 0
        with open(file_path, encoding="latin-1") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                processed += 1
                unit_number = (row.get(unit_field) or "").strip().upper()
                if not unit_number:
                    continue
                parsed_date = _parse_date((row.get("Fecha") or "").strip())
                if not parsed_date:
                    continue
                raw_km = (row.get("Kms_diario") or "").strip()
                try:
                    km_value = int(float(raw_km))
                except ValueError:
                    continue

                unit = maintenance_unit.objects.filter(
                    number__iexact=unit_number
                ).first()
                batch.append(
                    record_model(
                        maintenance_unit_id=unit.id if unit else None,
                        unit_number=unit_number,
                        record_date=parsed_date,
                        km_value=km_value,
                        source="legacy_csv",
                    )
                )

                if len(batch) >= batch_size:
                    record_model.objects.bulk_create(batch, ignore_conflicts=True)
                    inserted += len(batch)
                    print(
                        f"Imported {inserted} rows from {file_name} "
                        f"(processed {processed})"
                    )
                    batch = []

        if batch:
            record_model.objects.bulk_create(batch, ignore_conflicts=True)
            inserted += len(batch)

        if inserted or processed:
            print(f"Finished {file_name}: imported {inserted}, processed {processed}")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("tickets", "0016_backfill_rolling_stock_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="KilometrageRecordModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        editable=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Fecha de creación",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Fecha de actualización",
                    ),
                ),
                (
                    "unit_number",
                    models.CharField(
                        max_length=50,
                        verbose_name="Número de unidad",
                    ),
                ),
                (
                    "record_date",
                    models.DateField(verbose_name="Fecha"),
                ),
                (
                    "km_value",
                    models.PositiveIntegerField(verbose_name="Kilometraje"),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=30,
                        verbose_name="Origen",
                    ),
                ),
                (
                    "maintenance_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="kilometrage_records",
                        to="tickets.maintenanceunitmodel",
                        verbose_name="Unidad de mantenimiento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de kilometraje",
                "verbose_name_plural": "Registros de kilometraje",
                "db_table": "kilometrage_record",
                "ordering": ["-record_date"],
            },
        ),
        migrations.AddConstraint(
            model_name="kilometragerecordmodel",
            constraint=models.UniqueConstraint(
                fields=("unit_number", "record_date"),
                name="uniq_kilometrage_unit_date",
            ),
        ),
        migrations.AddIndex(
            model_name="kilometragerecordmodel",
            index=models.Index(
                fields=["unit_number", "record_date"],
                name="km_unit_date_idx",
            ),
        ),
        migrations.RunPython(load_kilometrage_from_legacy, migrations.RunPython.noop),
    ]
