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
    GOPModel,
    IntervencionTipoModel,
    LocomotiveModel,
    LocomotiveModelModel,
    LugarEmailRecipientModel,
    LugarModel,
    MaintenanceCycleModel,
    MaintenanceEntryEmailDispatchModel,
    MaintenanceUnitModel,
    NovedadModel,
    TicketModel,
)


@pytest.mark.django_db
def test_create_entry_creates_email_dispatch(tmp_path, settings):
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

    use_case = MaintenanceEntryUseCase()

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
    dispatch = MaintenanceEntryEmailDispatchModel.objects.get(entry=result.entry)
    assert dispatch.status == MaintenanceEntryEmailDispatchModel.Status.PENDING
    assert dispatch.to_recipients == ["to@example.com"]
    assert str(result.entry.id)[:8] in dispatch.subject


@pytest.mark.django_db
def test_prepare_draft_includes_pending_ticket_tasks():
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A910", unit_type="locomotora"
    )
    other_unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A911", unit_type="locomotora"
    )
    gop = GOPModel.objects.create(id=uuid.uuid4(), name="GOP 1", code="GOP1")
    lugar = LugarModel.objects.create(
        id=uuid.uuid4(), codigo=99, descripcion="Deposito"
    )
    intervencion = IntervencionTipoModel.objects.create(
        id=uuid.uuid4(), codigo="RG", descripcion="Revision General"
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 10).date(),
        intervencion=intervencion,
        lugar=lugar,
        is_legacy=False,
    )

    pending_ticket = TicketModel.objects.create(
        id=uuid.uuid4(),
        ticket_number="2026-0001",
        date=datetime(2026, 3, 8).date(),
        maintenance_unit=unit,
        gop=gop,
        entry_type=TicketModel.EntryType.IMMEDIATE,
        status=TicketModel.Status.PENDING,
        reported_failure="Falla motor",
    )
    TicketModel.objects.create(
        id=uuid.uuid4(),
        ticket_number="2026-0002",
        date=datetime(2026, 3, 7).date(),
        maintenance_unit=unit,
        gop=gop,
        entry_type=TicketModel.EntryType.IMMEDIATE,
        status=TicketModel.Status.COMPLETED,
        reported_failure="Falla resuelta",
    )
    TicketModel.objects.create(
        id=uuid.uuid4(),
        ticket_number="2026-0003",
        date=datetime(2026, 3, 9).date(),
        maintenance_unit=other_unit,
        gop=gop,
        entry_type=TicketModel.EntryType.IMMEDIATE,
        status=TicketModel.Status.PENDING,
        reported_failure="Otra falla",
    )

    use_case = MaintenanceEntryUseCase()

    draft = use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=None,
        trigger_type=None,
        trigger_unit=None,
    )

    expected = f"Ticket {pending_ticket.ticket_number} - Falla motor"
    assert draft.pending_ticket_tasks == [expected]
