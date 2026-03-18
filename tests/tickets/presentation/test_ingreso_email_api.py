"""Tests de API para despacho de correos de ingreso."""

import json
import uuid
from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.tickets.domain.services.ingreso_email_signer import IngresoEmailSigner
from apps.tickets.models import (
    LugarModel,
    MaintenanceEntryEmailDispatchModel,
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
)


def _create_entry_with_pdf(tmp_path):
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A200", unit_type="locomotora"
    )
    lugar = LugarModel.objects.create(
        id=uuid.uuid4(), codigo=1, descripcion="Deposito", short_desc="DEP"
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 1).date(),
        lugar=lugar,
        is_legacy=False,
    )
    entry = MaintenanceEntryModel.objects.create(
        novedad=novedad,
        maintenance_unit=unit,
        lugar=lugar,
        entry_datetime=timezone.now(),
    )
    pdf_path = tmp_path / "ingreso_test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    entry.pdf_path = str(pdf_path)
    entry.save(update_fields=["pdf_path", "updated_at"])
    return entry


@pytest.mark.django_db
def test_pending_endpoint_returns_signed_payload(client, settings, tmp_path):
    settings.INGRESO_TRAY_TOKEN = "token"
    settings.INGRESO_EMAIL_SIGNING_SECRET = "secret"

    entry = _create_entry_with_pdf(tmp_path)
    MaintenanceEntryEmailDispatchModel.objects.create(
        entry=entry,
        status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
        attempts=0,
        to_recipients=["to@example.com"],
        cc_recipients=[],
        subject="Ingreso 123",
        body="Body",
        body_html=None,
    )

    response = client.get(
        reverse("tickets:ingreso_email_pending"),
        HTTP_X_TRAY_TOKEN="token",
    )

    assert response.status_code == 200
    payload = response.json()["payload"]
    signature = response.json()["signature"]
    assert IngresoEmailSigner.verify(payload, signature, "secret")


@pytest.mark.django_db
def test_result_endpoint_marks_sent(client, settings, tmp_path):
    settings.INGRESO_TRAY_TOKEN = "token"
    settings.INGRESO_EMAIL_SIGNING_SECRET = "secret"

    entry = _create_entry_with_pdf(tmp_path)
    dispatch = MaintenanceEntryEmailDispatchModel.objects.create(
        entry=entry,
        status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
        attempts=0,
        to_recipients=["to@example.com"],
        cc_recipients=[],
        subject="Ingreso 123",
        body="Body",
        body_html=None,
    )

    payload = {
        "dispatch_id": str(dispatch.id),
        "status": "sent",
        "windows_username": "TESTUSER",
    }
    response = client.post(
        reverse("tickets:ingreso_email_result"),
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_TRAY_TOKEN="token",
    )

    dispatch.refresh_from_db()

    assert response.status_code == 200
    assert dispatch.status == MaintenanceEntryEmailDispatchModel.Status.SENT
    assert dispatch.windows_username == "TESTUSER"
    assert dispatch.attempts == 1


@pytest.mark.django_db
def test_result_endpoint_marks_drafted(client, settings, tmp_path):
    settings.INGRESO_TRAY_TOKEN = "token"
    settings.INGRESO_EMAIL_SIGNING_SECRET = "secret"

    entry = _create_entry_with_pdf(tmp_path)
    dispatch = MaintenanceEntryEmailDispatchModel.objects.create(
        entry=entry,
        status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
        attempts=0,
        to_recipients=["to@example.com"],
        cc_recipients=[],
        subject="Ingreso 123",
        body="Body",
        body_html=None,
    )

    payload = {
        "dispatch_id": str(dispatch.id),
        "status": "drafted",
        "windows_username": "TESTUSER",
    }
    response = client.post(
        reverse("tickets:ingreso_email_result"),
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_TRAY_TOKEN="token",
    )

    dispatch.refresh_from_db()

    assert response.status_code == 200
    assert dispatch.status == MaintenanceEntryEmailDispatchModel.Status.DRAFTED
    assert dispatch.windows_username == "TESTUSER"
    assert dispatch.attempts == 1


@pytest.mark.django_db
def test_pdf_endpoint_serves_file(client, settings, tmp_path):
    settings.INGRESO_TRAY_TOKEN = "token"
    settings.INGRESO_EMAIL_SIGNING_SECRET = "secret"

    entry = _create_entry_with_pdf(tmp_path)
    MaintenanceEntryEmailDispatchModel.objects.create(
        entry=entry,
        status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
        attempts=0,
        to_recipients=["to@example.com"],
        cc_recipients=[],
        subject="Ingreso 123",
        body="Body",
        body_html=None,
    )

    pending_response = client.get(
        reverse("tickets:ingreso_email_pending"),
        HTTP_X_TRAY_TOKEN="token",
    )
    payload = pending_response.json()["payload"]
    signature = pending_response.json()["signature"]

    response = client.get(
        reverse("tickets:ingreso_email_pdf"),
        data={"dispatch_id": payload["dispatch_id"], "signature": signature},
        HTTP_X_TRAY_TOKEN="token",
    )

    content = b"".join(response.streaming_content)

    assert response.status_code == 200
    assert content == b"%PDF-1.4 test"
