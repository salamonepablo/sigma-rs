"""Pruebas de vistas para novedades."""

from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.tickets.application.use_cases.legacy_sync_use_case import (
    LegacySyncResult,
    SyncStats,
)
from apps.tickets.infrastructure.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)


@pytest.mark.django_db
class TestNovedadViews:
    """Pruebas básicas para el CRUD de novedades."""

    def _user(self):
        user_model = get_user_model()
        return user_model.objects.create_user(
            username="novedades", password="secret123"
        )

    def _references(self):
        unit_loco = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A300",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        unit_rail = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="U3001",
            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
        )
        intervencion = IntervencionTipoModel.objects.create(
            codigo="RA",
            descripcion="Revisión anual",
        )
        lugar = LugarModel.objects.create(codigo=20, descripcion="Taller Escalada")
        return unit_loco, unit_rail, intervencion, lugar

    def test_list_requires_login(self, client):
        """La lista de novedades exige autenticación."""
        response = client.get(reverse("tickets:novedad_list"))

        assert response.status_code == 302

    def test_list_filters_by_unit_type(self, client):
        """Puede filtrar por tipo de unidad desde la ruta."""
        user = self._user()
        unit_loco, unit_rail, intervencion, lugar = self._references()
        today = date.today()
        NovedadModel.objects.create(
            maintenance_unit=unit_loco,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
        )
        NovedadModel.objects.create(
            maintenance_unit=unit_rail,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
        )
        client.force_login(user)

        response = client.get(
            reverse("tickets:novedad_list_by_type", kwargs={"unit_type": "locomotora"})
        )

        assert response.status_code == 200
        page = response.context["page_obj"]
        assert page.paginator.count == 1
        assert page.object_list[0].maintenance_unit == unit_loco

    def test_create_view_creates_manual_entry(self, client):
        """La vista de creación almacena una novedad manual."""
        user = self._user()
        unit_loco, _, intervencion, lugar = self._references()
        client.force_login(user)

        response = client.post(
            reverse("tickets:novedad_create"),
            data={
                "unit_input": unit_loco.number,
                "intervencion_input": intervencion.codigo,
                "lugar_input": str(lugar.codigo),
                "fecha_desde": date.today().isoformat(),
                "observaciones": "Carga manual",
            },
        )

        assert response.status_code == 302
        novedad = NovedadModel.objects.get()
        assert novedad.is_legacy is False

    def test_list_excludes_al_by_default(self, client):
        """Los alistamientos (AL) quedan ocultos salvo que se pidan."""
        user = self._user()
        unit_loco, _, intervencion, lugar = self._references()
        interv_al = IntervencionTipoModel.objects.create(
            codigo="AL", descripcion="Alistamiento"
        )
        NovedadModel.objects.create(
            maintenance_unit=unit_loco,
            fecha_desde=date.today(),
            intervencion=interv_al,
            lugar=lugar,
        )
        NovedadModel.objects.create(
            maintenance_unit=unit_loco,
            fecha_desde=date.today(),
            intervencion=intervencion,
            lugar=lugar,
        )
        client.force_login(user)

        response = client.get(reverse("tickets:novedad_list"))
        page = response.context["page_obj"]
        assert page.paginator.count == 1

        response_with_al = client.get(
            reverse("tickets:novedad_list"), data={"include_alistamientos": "on"}
        )
        page_with_al = response_with_al.context["page_obj"]
        assert page_with_al.paginator.count == 2

    def test_list_vagones_includes_legacy_history(self, client):
        """La lista de vagones muestra novedades legacy y manuales."""
        user = self._user()
        unit_wagon = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="V600",
            unit_type=MaintenanceUnitModel.UnitType.WAGON,
            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
        )
        unit_rail = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="U600",
            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
            rolling_stock_category=MaintenanceUnitModel.Category.RAILCAR,
        )
        intervencion = IntervencionTipoModel.objects.create(
            codigo="RA",
            descripcion="Revisión",
        )
        lugar = LugarModel.objects.create(codigo=21, descripcion="Taller Junin")
        today = date.today()
        NovedadModel.objects.create(
            maintenance_unit=unit_wagon,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
            is_legacy=True,
        )
        NovedadModel.objects.create(
            maintenance_unit=unit_wagon,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
            is_legacy=False,
        )
        NovedadModel.objects.create(
            maintenance_unit=None,
            legacy_unit_code=unit_wagon.number,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
            is_legacy=True,
        )
        NovedadModel.objects.create(
            maintenance_unit=unit_rail,
            fecha_desde=today,
            intervencion=intervencion,
            lugar=lugar,
            is_legacy=False,
        )
        client.force_login(user)

        response = client.get(reverse("tickets:novedad_list_vagones"))

        assert response.status_code == 200
        page = response.context["page_obj"]
        assert page.paginator.count == 3
        assert any(item.is_legacy for item in page.object_list)
        assert all(
            item.maintenance_unit in [unit_wagon, None] for item in page.object_list
        )

    def test_sync_view_redirects_with_labeled_counts(self, client):
        """La sincronizacion redirige y muestra conteos etiquetados."""
        user = self._user()
        client.force_login(user)

        result = LegacySyncResult(
            novedades=SyncStats(
                processed=10, inserted=3, skipped_old=0, duplicates=1, invalid=0
            ),
            kilometrage=SyncStats(
                processed=6, inserted=4, skipped_old=2, duplicates=0, invalid=0
            ),
            duration_seconds=0.5,
        )

        with patch(
            "apps.tickets.presentation.views.novedad_views.LegacySyncUseCase.run",
            return_value=result,
        ):
            response = client.post(reverse("tickets:novedad_sync"))

        assert response.status_code == 302
        messages_list = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        assert any("Novedades:" in message for message in messages_list)
        assert any("Kilometraje:" in message for message in messages_list)

    def test_sync_button_is_single_across_unit_types(self, client):
        """El control de sync aparece una vez en cada vista por tipo."""
        user = self._user()
        client.force_login(user)

        urls = [
            reverse("tickets:novedad_list_locomotoras"),
            reverse("tickets:novedad_list_ccrr"),
            reverse("tickets:novedad_list_vagones"),
        ]

        for url in urls:
            response = client.get(url)
            assert response.status_code == 200
            content = response.content.decode("utf-8")
            assert content.count('data-sync-control="legacy-sync"') == 1
