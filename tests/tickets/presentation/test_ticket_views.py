"""Tests de vistas para tickets (presentación)."""

from datetime import date
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.tickets.infrastructure.models import (
    GOPModel,
    MaintenanceUnitModel,
    TicketModel,
)


@pytest.mark.django_db
class TestTicketViews:
    """Pruebas básicas de vistas de tickets."""

    def _create_user(self):
        user_model = get_user_model()
        return user_model.objects.create_user(
            username="tester",
            password="secret123",
        )

    def _create_ticket(self):
        maintenance_unit = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A101",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )
        gop = GOPModel.objects.create(id=uuid4(), name="GOP 1", code="G1")
        ticket = TicketModel.objects.create(
            id=uuid4(),
            ticket_number="",
            date=date.today(),
            maintenance_unit=maintenance_unit,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            status=TicketModel.Status.PENDING,
            reported_failure="Falla de prueba",
        )
        return ticket

    def test_ticket_list_view_requires_login(self, client):
        """La lista de tickets debe requerir login."""
        response = client.get(reverse("tickets:ticket_list"))

        assert response.status_code == 302

    def test_ticket_list_view_renders_for_logged_user(self, client):
        """La lista de tickets responde 200 para usuarios autenticados."""
        user = self._create_user()
        self._create_ticket()
        client.force_login(user)

        response = client.get(reverse("tickets:ticket_list"))

        assert response.status_code == 200

    def test_ticket_status_update_marks_completed(self, client):
        """Permite marcar el ticket como finalizado desde el listado."""
        user = self._create_user()
        ticket = self._create_ticket()
        client.force_login(user)

        response = client.post(
            reverse("tickets:ticket_status_update", kwargs={"pk": ticket.pk}),
            HTTP_REFERER=reverse("tickets:ticket_list"),
        )

        ticket.refresh_from_db()

        assert response.status_code == 302
        assert ticket.status == TicketModel.Status.COMPLETED

    def test_ticket_list_vagones_filters_cargo_category(self, client):
        """La lista de vagones solo incluye tickets de carga."""
        user = self._create_user()
        gop = GOPModel.objects.create(id=uuid4(), name="GOP 2", code="G2")
        unit_wagon = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="V100",
            unit_type=MaintenanceUnitModel.UnitType.WAGON,
            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
        )
        unit_rail = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="U300",
            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
            rolling_stock_category=MaintenanceUnitModel.Category.RAILCAR,
        )
        TicketModel.objects.create(
            id=uuid4(),
            ticket_number="",
            date=date.today(),
            maintenance_unit=unit_wagon,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            status=TicketModel.Status.PENDING,
            reported_failure="Falla en vagon",
        )
        TicketModel.objects.create(
            id=uuid4(),
            ticket_number="",
            date=date.today(),
            maintenance_unit=unit_rail,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            status=TicketModel.Status.PENDING,
            reported_failure="Falla en coche",
        )
        client.force_login(user)

        response = client.get(reverse("tickets:ticket_list_vagones"))

        assert response.status_code == 200
        page = response.context["page_obj"]
        assert page.paginator.count == 1
        assert page.object_list[0].maintenance_unit == unit_wagon

    def test_ticket_list_ccrr_excludes_cargo_category(self, client):
        """La lista de coches remolcados excluye vagones."""
        user = self._create_user()
        gop = GOPModel.objects.create(id=uuid4(), name="GOP 3", code="G3")
        unit_wagon = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="V200",
            unit_type=MaintenanceUnitModel.UnitType.WAGON,
            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
        )
        unit_rail = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="U301",
            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
            rolling_stock_category=MaintenanceUnitModel.Category.RAILCAR,
        )
        TicketModel.objects.create(
            id=uuid4(),
            ticket_number="",
            date=date.today(),
            maintenance_unit=unit_wagon,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            status=TicketModel.Status.PENDING,
            reported_failure="Falla en vagon",
        )
        TicketModel.objects.create(
            id=uuid4(),
            ticket_number="",
            date=date.today(),
            maintenance_unit=unit_rail,
            gop=gop,
            entry_type=TicketModel.EntryType.IMMEDIATE,
            status=TicketModel.Status.PENDING,
            reported_failure="Falla en coche",
        )
        client.force_login(user)

        response = client.get(reverse("tickets:ticket_list_ccrr"))

        assert response.status_code == 200
        page = response.context["page_obj"]
        assert page.paginator.count == 1
        assert page.object_list[0].maintenance_unit == unit_rail

    def test_ticket_create_vagones_limits_unit_selector(self, client):
        """El alta de tickets para vagones filtra unidades."""
        user = self._create_user()
        unit_wagon = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="V300",
            unit_type=MaintenanceUnitModel.UnitType.WAGON,
            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
        )
        MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="A999",
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
            rolling_stock_category=MaintenanceUnitModel.Category.TRACTION,
        )
        client.force_login(user)

        response = client.get(reverse("tickets:ticket_create_vagones"))

        assert response.status_code == 200
        form = response.context["form"]
        units = list(form.fields["maintenance_unit"].queryset)
        assert units == [unit_wagon]

    def test_ticket_create_vagon_creates_and_lists_ticket(self, client):
        """Alta de ticket vagon crea y aparece en listado."""
        user = self._create_user()
        gop = GOPModel.objects.create(id=uuid4(), name="GOP 4", code="G4")
        unit_wagon = MaintenanceUnitModel.objects.create(
            id=uuid4(),
            number="V500",
            unit_type=MaintenanceUnitModel.UnitType.WAGON,
            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
        )
        client.force_login(user)

        response = client.post(
            reverse("tickets:ticket_create_vagones"),
            data={
                "date": date.today().isoformat(),
                "maintenance_unit": str(unit_wagon.id),
                "gop": str(gop.id),
                "entry_type": TicketModel.EntryType.IMMEDIATE,
                "status": TicketModel.Status.PENDING,
                "reported_failure": "Falla de vagon",
            },
        )

        assert response.status_code == 302
        ticket = TicketModel.objects.get(maintenance_unit=unit_wagon)
        assert ticket.maintenance_unit.unit_type == MaintenanceUnitModel.UnitType.WAGON

        list_response = client.get(reverse("tickets:ticket_list_vagones"))

        assert list_response.status_code == 200
        page = list_response.context["page_obj"]
        assert ticket in page.object_list


@pytest.mark.django_db
class TestAuthViews:
    """Pruebas de login/logout."""

    def _create_user(self):
        user_model = get_user_model()
        return user_model.objects.create_user(
            username="tester",
            password="secret123",
        )

    def test_login_get_redirects_when_authenticated(self, client):
        """Si el usuario está autenticado, redirige al home."""
        user = self._create_user()
        client.force_login(user)

        response = client.get(reverse("tickets:login"))

        assert response.status_code == 302

    def test_login_post_valid_credentials(self, client):
        """Permite iniciar sesión con credenciales válidas."""
        self._create_user()

        response = client.post(
            reverse("tickets:login"),
            data={"username": "tester", "password": "secret123"},
        )

        assert response.status_code == 302

    def test_login_post_invalid_credentials(self, client):
        """Muestra error cuando credenciales son inválidas."""
        response = client.post(
            reverse("tickets:login"),
            data={"username": "nope", "password": "bad"},
        )

        assert response.status_code == 200
        assert "Usuario o contraseña incorrectos" in response.content.decode()

    def test_logout_redirects_to_login(self, client):
        """Logout redirige al login."""
        user = self._create_user()
        client.force_login(user)

        response = client.get(reverse("tickets:logout"))

        assert response.status_code == 302
