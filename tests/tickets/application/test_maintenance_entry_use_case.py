"""Pruebas de aplicación para ingreso a mantenimiento."""

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryDraft,
    MaintenanceEntryUseCase,
)
from apps.tickets.domain.services.intervention_suggestion import (
    InterventionSuggestion,
    UnitMaintenanceHistory,
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
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
    TicketModel,
    WagonModel,
    WagonTypeModel,
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


@pytest.mark.django_db
def test_prepare_draft_resolves_wagon_brand_model_and_cycles():
    brand = BrandModel.objects.create(
        id=uuid.uuid4(), code="Carga", name="Carga", full_name="Carga"
    )
    wagon_type = WagonTypeModel.objects.create(
        id=uuid.uuid4(), code="VAGON", name="Vagón"
    )
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(),
        number="V123",
        unit_type=MaintenanceUnitModel.UnitType.WAGON,
        rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
    )
    WagonModel.objects.create(
        maintenance_unit=unit,
        brand=brand,
        wagon_type=wagon_type,
    )
    intervencion = IntervencionTipoModel.objects.create(
        id=uuid.uuid4(), codigo="AL", descripcion="Alineación"
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 12).date(),
        intervencion=intervencion,
        is_legacy=False,
    )

    for code, value in zip(
        ["AL", "REV", "A", "B"], [1000, 2000, 3000, 4000], strict=True
    ):
        MaintenanceCycleModel.objects.create(
            id=uuid.uuid4(),
            rolling_stock_type=MaintenanceUnitModel.UnitType.WAGON,
            brand=brand,
            model=None,
            intervention_code=code,
            intervention_name=f"Revision {code}",
            trigger_type="km",
            trigger_value=value,
            trigger_unit="km",
            is_active=True,
        )

    use_case = MaintenanceEntryUseCase()

    draft = use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=2500,
        trigger_type="km",
        trigger_unit="km",
    )

    assert draft.unit_type == MaintenanceUnitModel.UnitType.WAGON
    assert draft.brand_label == brand.name
    assert draft.model_label == wagon_type.name
    assert draft.suggestion.suggested_code == "REV"


def test_email_content_formatea_km_en_eu():
    """El correo muestra kilometraje en formato europeo."""
    use_case = MaintenanceEntryUseCase()
    history = UnitMaintenanceHistory(
        last_rg_date=date(2026, 3, 1),
        last_rg_km_since=Decimal("1000.5"),
        last_numeral_code=None,
        last_numeral_date=None,
        last_numeral_km_since=None,
        last_rp_code=None,
        last_rp_date=None,
        last_rp_km_since=None,
        last_abc_date=None,
        last_abc_km_since=None,
    )
    suggestion = InterventionSuggestion(
        status="ok",
        reason=None,
        suggested_code=None,
        suggested_name=None,
        last_intervention_code=None,
        last_intervention_date=None,
        km_since_last=None,
        period_since_last=None,
    )
    draft = MaintenanceEntryDraft(
        novelty=NovedadModel(fecha_desde=date(2026, 3, 1)),
        maintenance_unit=None,
        unit_label="A904",
        brand_label="GM",
        model_label="GT22",
        unit_type="locomotora",
        brand_code="GM",
        trigger_value=None,
        trigger_type=None,
        trigger_unit=None,
        suggestion=suggestion,
        history=history,
        pending_ticket_tasks=[],
    )
    entry = MaintenanceEntryModel(
        id=uuid.uuid4(),
        novedad=draft.novelty,
        entry_datetime=datetime(2026, 3, 6, 10, 30),
        trigger_type="km",
        trigger_value=1000,
    )

    _, body, _ = use_case._build_email_content(entry, draft)

    assert "1.000,5 km" in body


def test_pdf_payload_formatea_km_en_eu(tmp_path, settings):
    """El PDF recibe kilometraje con formato europeo."""
    settings.BASE_DIR = tmp_path

    use_case = MaintenanceEntryUseCase()
    captured = {}

    def fake_generate(data):
        captured["data"] = data
        return b"%PDF-1.4"

    use_case._pdf_generator.generate = fake_generate

    history = UnitMaintenanceHistory(
        last_rg_date=date(2026, 3, 1),
        last_rg_km_since=Decimal("1000.5"),
        last_numeral_code=None,
        last_numeral_date=None,
        last_numeral_km_since=None,
        last_rp_code=None,
        last_rp_date=None,
        last_rp_km_since=None,
        last_abc_date=None,
        last_abc_km_since=None,
    )
    suggestion = InterventionSuggestion(
        status="ok",
        reason=None,
        suggested_code=None,
        suggested_name=None,
        last_intervention_code=None,
        last_intervention_date=None,
        km_since_last=None,
        period_since_last=None,
    )
    draft = MaintenanceEntryDraft(
        novelty=NovedadModel(fecha_desde=date(2026, 3, 1)),
        maintenance_unit=None,
        unit_label="A904",
        brand_label="GM",
        model_label="GT22",
        unit_type="locomotora",
        brand_code="GM",
        trigger_value=None,
        trigger_type=None,
        trigger_unit=None,
        suggestion=suggestion,
        history=history,
        pending_ticket_tasks=[],
    )
    entry = MaintenanceEntryModel(
        id=uuid.uuid4(),
        novedad=draft.novelty,
        entry_datetime=datetime(2026, 3, 6, 10, 30),
        trigger_type="km",
        trigger_value=1000,
    )

    use_case._generate_pdf(entry, draft, user=None)

    assert captured["data"].last_rg_km == "1.000,5"
    assert captured["data"].trigger_label == "KM RG: 1.000"
