"""Pruebas de vistas para novedades."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.tickets.application.use_cases.legacy_sync_use_case import (
    LegacySyncResult,
    SyncStats,
)
from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryUseCase,
)
from apps.tickets.infrastructure.models import (
    IntervencionTipoModel,
    KilometrageRecordModel,
    LugarModel,
    MaintenanceEntryEmailDispatchModel,
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
)
from apps.tickets.presentation.views.novedad_views import MaintenanceEntryCreateView


@pytest.mark.django_db
class TestNovedadViews:
    """Pruebas básicas para el CRUD de novedades."""

    def _user(self, is_staff=False):
        user_model = get_user_model()
        import uuid
        username = f"user_{uuid.uuid4().hex[:8]}"
        return user_model.objects.create_user(
            username=username, password="secret123", is_staff=is_staff
        )

    def _admin_user(self):
        user_model = get_user_model()
        return user_model.objects.create_user(
            username="admin", password="secret123", is_staff=True
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

        with (
            patch(
                "apps.tickets.presentation.views.novedad_views.AccessSyncUseCase.run",
                return_value=result,
            ),
            override_settings(
                ACCESS_BASELOCS_PATH="dummy",
                ACCESS_BASECCRR_PATH="dummy",
                ACCESS_EXTRACTOR_SCRIPT="dummy",
                ACCESS_POWERSHELL_PATH="dummy",
            ),
        ):
            response = client.post(reverse("tickets:novedad_sync"))

        assert response.status_code == 302
        messages_list = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        assert any("Novedades:" in message for message in messages_list)
        assert any("Km:" in message for message in messages_list)

    def test_sync_button_visible_only_for_staff(self, client):
        """El botón de sync manual solo aparece para usuarios staff."""
        staff_user = self._user(is_staff=True)
        regular_user = self._user()

        urls = [
            reverse("tickets:novedad_list_locomotoras"),
            reverse("tickets:novedad_list_ccrr"),
            reverse("tickets:novedad_list_vagones"),
        ]

        # Staff ve el botón de sync manual
        client.force_login(staff_user)
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200
            assert "Sync manual" in response.content.decode("utf-8")

        # Usuario regular no ve el botón de sync manual
        client.force_login(regular_user)
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200
            assert "Sync manual" not in response.content.decode("utf-8")

    def test_prefill_km_usa_formato_eu(self):
        """El prefill de km aplica formato europeo con decimales reales."""
        assert MaintenanceEntryCreateView._format_km(Decimal("1000.5")) == "1.000,5"
        assert MaintenanceEntryCreateView._format_km("1.000,5") == "1.000,5"

    def test_maintenance_entry_view_reuses_request_cache(self, client, settings):
        """La vista reutiliza el cache request-scoped del ingreso."""
        settings.INGRESO_REQUEST_CACHE_ENABLED = True

        user = self._user()
        client.force_login(user)

        unit = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A400",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        intervencion = IntervencionTipoModel.objects.create(
            codigo="RA",
            descripcion="Revisión anual",
        )
        novedad = NovedadModel.objects.create(
            maintenance_unit=unit,
            fecha_desde=date.today(),
            intervencion=intervencion,
            is_legacy=False,
        )
        KilometrageRecordModel.objects.create(
            maintenance_unit=unit,
            unit_number=unit.number,
            record_date=date.today(),
            km_value=Decimal("1000.00"),
            source="test",
        )

        with patch(
            "apps.tickets.application.use_cases.maintenance_entry_use_case."
            "MaintenanceEntryUseCase.prepare_draft",
            autospec=True,
            wraps=MaintenanceEntryUseCase.prepare_draft,
        ) as spy:
            response = client.get(
                reverse(
                    "tickets:maintenance_entry_create",
                    kwargs={"pk": novedad.pk},
                )
            )

        assert response.status_code == 200
        request_caches = [
            call.kwargs.get("request_cache") for call in spy.call_args_list
        ]
        assert request_caches
        assert request_caches[0] is not None
        assert all(cache is request_caches[0] for cache in request_caches)

    def test_delete_ingreso_view_post_deletes_and_redirects(self, client):
        """El POST de borrado elimina el ingreso y redirige."""
        admin = self._admin_user()
        client.force_login(admin)

        novedad = NovedadModel.objects.create(
            fecha_desde=date.today(),
            is_legacy=False,
            ingreso_generado=True,
        )
        entry = MaintenanceEntryModel.objects.create(
            novedad=novedad,
            entry_datetime=timezone.now(),
        )
        MaintenanceEntryEmailDispatchModel.objects.create(
            entry=entry,
            status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
            attempts=0,
            to_recipients=["to@example.com"],
            cc_recipients=[],
            subject="Ingreso",
            body="Cuerpo",
        )

        response = client.post(
            reverse("tickets:novedad_delete_ingreso", kwargs={"pk": novedad.pk})
        )

        assert response.status_code == 302
        assert not MaintenanceEntryModel.objects.filter(id=entry.id).exists()
        novedad.refresh_from_db()
        assert novedad.ingreso_generado is False

    def test_delete_ingreso_view_get_renders_confirm_when_sent(self, client):
        """El GET muestra confirmacion si el ingreso fue enviado."""
        admin = self._admin_user()
        client.force_login(admin)

        novedad = NovedadModel.objects.create(
            fecha_desde=date.today(),
            is_legacy=False,
            ingreso_generado=True,
        )
        entry = MaintenanceEntryModel.objects.create(
            novedad=novedad,
            entry_datetime=timezone.now(),
        )
        MaintenanceEntryEmailDispatchModel.objects.create(
            entry=entry,
            status=MaintenanceEntryEmailDispatchModel.Status.SENT,
            attempts=1,
            to_recipients=["to@example.com"],
            cc_recipients=[],
            subject="Ingreso",
            body="Cuerpo",
        )

        response = client.get(
            reverse("tickets:novedad_delete_ingreso", kwargs={"pk": novedad.pk})
        )

        assert response.status_code == 200
        assert any(
            template.name == "tickets/ingreso_confirm_delete.html"
            for template in response.templates
            if template.name
        )

    def test_delete_ingreso_list_action_visible_for_admin(self, client):
        """El listado muestra eliminar ingreso solo para admin."""
        admin = self._admin_user()
        client.force_login(admin)
        unit_loco, _, intervencion, lugar = self._references()
        novedad = NovedadModel.objects.create(
            maintenance_unit=unit_loco,
            fecha_desde=date.today(),
            intervencion=intervencion,
            lugar=lugar,
            ingreso_generado=True,
            is_legacy=False,
        )

        response = client.get(reverse("tickets:novedad_list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        delete_url = reverse(
            "tickets:novedad_delete_ingreso", kwargs={"pk": novedad.pk}
        )
        assert delete_url in content

    def test_delete_ingreso_detail_action_hidden_for_non_admin(self, client):
        """El detalle no muestra eliminar ingreso a no admin."""
        user = self._user()
        client.force_login(user)
        unit_loco, _, intervencion, lugar = self._references()
        novedad = NovedadModel.objects.create(
            maintenance_unit=unit_loco,
            fecha_desde=date.today(),
            intervencion=intervencion,
            lugar=lugar,
            ingreso_generado=True,
            is_legacy=False,
        )

        response = client.get(
            reverse("tickets:novedad_detail", kwargs={"pk": novedad.pk})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        delete_url = reverse(
            "tickets:novedad_delete_ingreso", kwargs={"pk": novedad.pk}
        )
        assert delete_url not in content

    def test_delete_ingreso_cancel_keeps_entry(self, client):
        """Cancelar la confirmacion no elimina el ingreso."""
        admin = self._admin_user()
        client.force_login(admin)

        novedad = NovedadModel.objects.create(
            fecha_desde=date.today(),
            is_legacy=False,
            ingreso_generado=True,
        )
        entry = MaintenanceEntryModel.objects.create(
            novedad=novedad,
            entry_datetime=timezone.now(),
        )
        MaintenanceEntryEmailDispatchModel.objects.create(
            entry=entry,
            status=MaintenanceEntryEmailDispatchModel.Status.SENT,
            attempts=1,
            to_recipients=["to@example.com"],
            cc_recipients=[],
            subject="Ingreso",
            body="Cuerpo",
        )

        response = client.get(
            reverse("tickets:novedad_delete_ingreso", kwargs={"pk": novedad.pk})
        )

        cancel_url = response.context["cancel_url"]
        cancel_response = client.get(cancel_url)

        assert cancel_response.status_code == 200
        assert MaintenanceEntryModel.objects.filter(id=entry.id).exists()

    def test_novedad_delete_protected_redirects_to_detail(self, client):
        """Eliminar una novedad con ingreso asociado redirige al detalle."""
        user = self._user()
        client.force_login(user)

        novedad = NovedadModel.objects.create(
            fecha_desde=date.today(),
            is_legacy=False,
            ingreso_generado=True,
        )
        MaintenanceEntryModel.objects.create(
            novedad=novedad,
            entry_datetime=timezone.now(),
        )

        response = client.post(
            reverse("tickets:novedad_delete", kwargs={"pk": novedad.pk})
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "tickets:novedad_detail", kwargs={"pk": novedad.pk}
        )
        messages_list = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        assert any(
            "eliminar el ingreso" in message.lower() for message in messages_list
        )
