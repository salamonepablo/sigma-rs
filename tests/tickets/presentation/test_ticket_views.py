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
