"""Tests para la migración 0033 de deduplicación de novedades."""

import uuid
from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class TestNovedadBusinessKeyMigration:
    """Valida deduplicación y prioridad manual vs legacy."""

    migrate_from = ("tickets", "0032_novedadmodel_is_exported_novedadmodel_legacy_id")
    migrate_to = ("tickets", "0033_dedupe_novedad_business_key_and_unique")
    auth_target = ("auth", "0012_alter_user_first_name_max_length")

    @pytest.mark.django_db(transaction=True)
    def test_deduplicacion_conserva_manual_sobre_legacy(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.auth_target, self.migrate_from])
        old_apps = executor.loader.project_state(
            [self.auth_target, self.migrate_from]
        ).apps

        maintenance_unit_model = old_apps.get_model("tickets", "MaintenanceUnitModel")
        intervencion_model = old_apps.get_model("tickets", "IntervencionTipoModel")
        novedad_model = old_apps.get_model("tickets", "NovedadModel")

        maintenance_unit = maintenance_unit_model.objects.create(
            id=uuid.uuid4(),
            number="A900",
            unit_type="locomotora",
        )
        intervencion = intervencion_model.objects.create(
            id=uuid.uuid4(),
            codigo="RA",
            descripcion="Revision",
        )

        legacy_novedad = novedad_model.objects.create(
            id=uuid.uuid4(),
            maintenance_unit_id=maintenance_unit.id,
            fecha_desde=date(2024, 3, 1),
            intervencion_id=intervencion.id,
            is_legacy=True,
        )
        manual_novedad = novedad_model.objects.create(
            id=uuid.uuid4(),
            maintenance_unit_id=maintenance_unit.id,
            fecha_desde=date(2024, 3, 1),
            intervencion_id=intervencion.id,
            is_legacy=False,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.auth_target, self.migrate_to])
        new_apps = executor.loader.project_state(
            [self.auth_target, self.migrate_to]
        ).apps
        migrated_novedad_model = new_apps.get_model("tickets", "NovedadModel")

        novedades = list(
            migrated_novedad_model.objects.filter(
                maintenance_unit_id=maintenance_unit.id,
                fecha_desde=date(2024, 3, 1),
                intervencion_id=intervencion.id,
            )
        )

        assert len(novedades) == 1
        assert novedades[0].id == manual_novedad.id
        assert novedades[0].is_legacy is False
        assert legacy_novedad.id != novedades[0].id
