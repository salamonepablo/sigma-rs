"""Pruebas del endpoint de sincronizacion en Home."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.tickets.application.use_cases.legacy_sync_use_case import (
    LegacySyncResult,
    SyncStats,
)


@pytest.mark.django_db
def test_home_sync_sets_session(client):
    """Guarda estado y conteos en sesion tras sincronizar."""
    user = get_user_model().objects.create_user(
        username="sync-user", password="secret123"
    )
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
        "apps.tickets.presentation.views.ticket_views.LegacySyncUseCase.run",
        return_value=result,
    ):
        response = client.post(reverse("tickets:legacy_sync"))

    assert response.status_code == 302
    session = client.session
    assert session["legacy_sync_status"] == "success"
    assert session["legacy_sync_counts"]["novedades"]["inserted"] == 3
    assert session["legacy_sync_counts"]["kilometrage"]["inserted"] == 4


@pytest.mark.django_db
def test_home_sync_error_sets_message(client):
    """Guarda mensaje de error cuando falla la sincronizacion."""
    user = get_user_model().objects.create_user(
        username="sync-error", password="secret123"
    )
    client.force_login(user)

    with patch(
        "apps.tickets.presentation.views.ticket_views.LegacySyncUseCase.run",
        side_effect=ValueError("fail"),
    ):
        response = client.post(reverse("tickets:legacy_sync"))

    assert response.status_code == 302
    session = client.session
    assert session["legacy_sync_status"] == "error"
    assert "fail" in session["legacy_sync_message"]
