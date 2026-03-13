"""Pruebas de aplicación para ingreso a mantenimiento."""

import uuid
from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryUseCase,
)
from apps.tickets.models import (
    BrandModel,
    IntervencionTipoModel,
    LocomotiveModel,
    LocomotiveModelModel,
    LugarEmailRecipientModel,
    LugarModel,
    MaintenanceCycleModel,
    MaintenanceUnitModel,
    NovedadModel,
)


class FakeOutlookClient:
    """Fake Outlook client for tests."""

    def __init__(self):
        self.calls = []

    def create_draft(
        self,
        to_recipients,
        cc_recipients,
        subject,
        body,
        body_html,
        attachment_path,
        sender_email,
    ):
        self.calls.append(
            {
                "to": to_recipients,
                "cc": cc_recipients,
                "subject": subject,
                "body": body,
                "body_html": body_html,
                "attachment_path": attachment_path,
                "sender_email": sender_email,
            }
        )


@pytest.mark.django_db
def test_create_entry_builds_outlook_draft(tmp_path, settings):
    settings.BASE_DIR = tmp_path

    brand, _ = BrandModel.objects.get_or_create(
        code="GM",
        defaults={
            "id": uuid.uuid4(),
            "name": "GM",
            "full_name": "General Motors",
        },
    )
    model = LocomotiveModelModel.objects.create(
        id=uuid.uuid4(), name="GT22-CW", code="GT22-CW", brand=brand
    )
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A904", unit_type="locomotora"
    )
    LocomotiveModel.objects.create(maintenance_unit=unit, brand=brand, model=model)

    lugar = LugarModel.objects.create(
        id=uuid.uuid4(), codigo=120, descripcion="PMRE", short_desc="PMRE"
    )
    intervencion = IntervencionTipoModel.objects.create(
        id=uuid.uuid4(), codigo="A", descripcion="Revision A"
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 1).date(),
        intervencion=intervencion,
        lugar=lugar,
        is_legacy=False,
    )

    MaintenanceCycleModel.objects.create(
        id=uuid.uuid4(),
        rolling_stock_type="locomotora",
        brand=brand,
        model=None,
        intervention_code="A",
        intervention_name="Revision A",
        trigger_type="km",
        trigger_value=16000,
        trigger_unit="km",
        is_active=True,
    )

    LugarEmailRecipientModel.objects.create(
        id=uuid.uuid4(),
        lugar=lugar,
        unit_type="locomotora",
        recipient_type="to",
        email="to@example.com",
        is_active=True,
    )

    user = get_user_model().objects.create_user(
        username="tester", email="tester@trenesargentinos.gob.ar", password="test"
    )

    fake_outlook = FakeOutlookClient()
    use_case = MaintenanceEntryUseCase(outlook_client=fake_outlook)

    entry_datetime = timezone.make_aware(datetime(2026, 3, 6, 10, 30))

    result = use_case.create_entry(
        novedad_id=str(novedad.pk),
        entry_datetime=entry_datetime,
        trigger_type="km",
        trigger_value=20000,
        trigger_unit="km",
        lugar_id=str(lugar.pk),
        selected_intervention_code=None,
        checklist_tasks="Tarea 1\nTarea 2",
        observations="Observaciones",
        user=user,
    )

    assert result.entry.pdf_path is not None
    assert fake_outlook.calls
    assert fake_outlook.calls[0]["to"] == ["to@example.com"]
