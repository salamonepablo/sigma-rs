"""Pruebas de aplicación para ingreso a mantenimiento."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryDraft,
    MaintenanceEntryRequestCache,
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
        last_abc_code=None,
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
        model_code=None,
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
        last_abc_code=None,
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
        model_code=None,
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


@pytest.mark.django_db
def test_prepare_draft_reuses_request_cache(settings):
    settings.INGRESO_REQUEST_CACHE_ENABLED = True

    brand, _ = BrandModel.objects.get_or_create(
        code="GM",
        defaults={
            "id": uuid.uuid4(),
            "name": "GM",
            "full_name": "General Motors",
        },
    )
    model, _ = LocomotiveModelModel.objects.get_or_create(
        code="GT22-CW",
        defaults={"id": uuid.uuid4(), "name": "GT22-CW", "brand": brand},
    )
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A990", unit_type="locomotora"
    )
    LocomotiveModel.objects.create(maintenance_unit=unit, brand=brand, model=model)
    intervencion, _ = IntervencionTipoModel.objects.get_or_create(
        codigo="A",
        defaults={"id": uuid.uuid4(), "descripcion": "Revision A"},
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 1).date(),
        intervencion=intervencion,
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

    use_case = MaintenanceEntryUseCase()
    cache = MaintenanceEntryRequestCache()

    first = use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=20000,
        trigger_type="km",
        trigger_unit="km",
        entry_date=datetime(2026, 3, 6).date(),
        request_cache=cache,
    )

    with patch.object(
        use_case, "_load_history", side_effect=AssertionError("cache miss")
    ):
        second = use_case.prepare_draft(
            novedad_id=str(novedad.pk),
            trigger_value=20000,
            trigger_type="km",
            trigger_unit="km",
            entry_date=datetime(2026, 3, 6).date(),
            request_cache=cache,
        )

    assert second is first


def test_km_lookup_uses_request_cache(settings):
    settings.INGRESO_REQUEST_CACHE_ENABLED = True

    use_case = MaintenanceEntryUseCase()
    cache = MaintenanceEntryRequestCache()
    calls: list[tuple[str, date]] = []

    def fake_get_km_since(unit_number: str, from_date: date):
        calls.append((unit_number, from_date))
        return Decimal("10")

    use_case._kilometrage_repo.get_km_since = fake_get_km_since

    value_one = use_case._get_km_since_cached("A1", date(2026, 3, 1), cache)
    value_two = use_case._get_km_since_cached("A1", date(2026, 3, 1), cache)

    assert value_one == Decimal("10")
    assert value_two == Decimal("10")
    assert len(calls) == 1


@pytest.mark.django_db
def test_prepare_draft_ignores_cache_when_flag_disabled(settings):
    settings.INGRESO_REQUEST_CACHE_ENABLED = False

    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A991", unit_type="locomotora"
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        maintenance_unit=unit,
        fecha_desde=datetime(2026, 3, 5).date(),
        is_legacy=False,
    )

    use_case = MaintenanceEntryUseCase()
    cache = MaintenanceEntryRequestCache()

    use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=None,
        trigger_type=None,
        trigger_unit=None,
        entry_date=datetime(2026, 3, 6).date(),
        request_cache=cache,
    )

    with patch.object(use_case, "_load_history", wraps=use_case._load_history) as spy:
        use_case.prepare_draft(
            novedad_id=str(novedad.pk),
            trigger_value=None,
            trigger_type=None,
            trigger_unit=None,
            entry_date=datetime(2026, 3, 6).date(),
            request_cache=cache,
        )

    assert spy.call_count == 1
    assert cache.drafts == {}


@pytest.mark.django_db
def test_cache_telemetry_failure_does_not_break_request(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    settings.INGRESO_REQUEST_CACHE_ENABLED = True

    brand, _ = BrandModel.objects.get_or_create(
        code="GM",
        defaults={
            "id": uuid.uuid4(),
            "name": "GM",
            "full_name": "General Motors",
        },
    )
    model, _ = LocomotiveModelModel.objects.get_or_create(
        code="GT22-CW",
        defaults={"id": uuid.uuid4(), "name": "GT22-CW", "brand": brand},
    )
    unit = MaintenanceUnitModel.objects.create(
        id=uuid.uuid4(), number="A992", unit_type="locomotora"
    )
    LocomotiveModel.objects.create(maintenance_unit=unit, brand=brand, model=model)
    lugar, _ = LugarModel.objects.get_or_create(
        codigo=130,
        defaults={"id": uuid.uuid4(), "descripcion": "PMRE"},
    )
    intervencion, _ = IntervencionTipoModel.objects.get_or_create(
        codigo="A",
        defaults={"id": uuid.uuid4(), "descripcion": "Revision A"},
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
    user = get_user_model().objects.create_user(
        username="tester2", email="tester2@trenesargentinos.gob.ar", password="x"
    )

    use_case = MaintenanceEntryUseCase()
    cache = MaintenanceEntryRequestCache()
    entry_datetime = timezone.make_aware(datetime(2026, 3, 6, 10, 30))

    use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=20000,
        trigger_type="km",
        trigger_unit="km",
        entry_date=entry_datetime.date(),
        request_cache=cache,
    )
    use_case.prepare_draft(
        novedad_id=str(novedad.pk),
        trigger_value=20000,
        trigger_type="km",
        trigger_unit="km",
        entry_date=entry_datetime.date(),
        request_cache=cache,
    )

    with patch(
        "apps.tickets.application.use_cases.maintenance_entry_use_case.logger.info",
        side_effect=RuntimeError("boom"),
    ):
        result = use_case.create_entry(
            novedad_id=str(novedad.pk),
            entry_datetime=entry_datetime,
            trigger_type="km",
            trigger_value=20000,
            trigger_unit="km",
            lugar_id=str(lugar.pk),
            selected_intervention_code=None,
            checklist_tasks=None,
            observations=None,
            user=user,
            request_cache=cache,
        )

    assert result.entry is not None


@pytest.mark.django_db
def test_delete_entry_removes_dispatches_and_resets_novedad():
    user = get_user_model().objects.create_user(
        username="admin", password="secret", is_staff=True
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        fecha_desde=datetime(2026, 3, 7).date(),
        is_legacy=False,
        ingreso_generado=True,
    )
    entry = MaintenanceEntryModel.objects.create(
        id=uuid.uuid4(),
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

    use_case = MaintenanceEntryUseCase()

    result = use_case.delete_entry(novedad_id=str(novedad.pk), user=user)

    assert not MaintenanceEntryEmailDispatchModel.objects.filter(
        entry_id=entry.id
    ).exists()
    assert not MaintenanceEntryModel.objects.filter(id=entry.id).exists()
    novedad.refresh_from_db()
    assert novedad.ingreso_generado is False
    assert result.had_sent_dispatch is False


@pytest.mark.django_db
def test_delete_entry_blocks_when_sent_without_confirmation():
    user = get_user_model().objects.create_user(
        username="admin", password="secret", is_staff=True
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        fecha_desde=datetime(2026, 3, 7).date(),
        is_legacy=False,
        ingreso_generado=True,
    )
    entry = MaintenanceEntryModel.objects.create(
        id=uuid.uuid4(),
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

    use_case = MaintenanceEntryUseCase()

    with pytest.raises(ValueError, match="confirmation"):
        use_case.delete_entry(novedad_id=str(novedad.pk), user=user)

    assert MaintenanceEntryModel.objects.filter(id=entry.id).exists()


@pytest.mark.django_db
def test_delete_entry_allows_sent_with_confirmation(tmp_path):
    user = get_user_model().objects.create_user(
        username="admin", password="secret", is_staff=True
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        fecha_desde=datetime(2026, 3, 7).date(),
        is_legacy=False,
        ingreso_generado=True,
    )
    missing_pdf = tmp_path / "ingreso_missing.pdf"
    entry = MaintenanceEntryModel.objects.create(
        id=uuid.uuid4(),
        novedad=novedad,
        entry_datetime=timezone.now(),
        pdf_path=str(missing_pdf),
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

    use_case = MaintenanceEntryUseCase()

    result = use_case.delete_entry(
        novedad_id=str(novedad.pk), user=user, confirm_sent=True
    )

    assert not MaintenanceEntryModel.objects.filter(id=entry.id).exists()
    assert result.pdf_deleted is False


@pytest.mark.django_db
def test_delete_entry_rejects_non_admin():
    user = get_user_model().objects.create_user(
        username="user", password="secret", is_staff=False
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        fecha_desde=datetime(2026, 3, 7).date(),
        is_legacy=False,
        ingreso_generado=True,
    )
    MaintenanceEntryModel.objects.create(
        id=uuid.uuid4(),
        novedad=novedad,
        entry_datetime=timezone.now(),
    )

    use_case = MaintenanceEntryUseCase()

    with pytest.raises(PermissionError):
        use_case.delete_entry(novedad_id=str(novedad.pk), user=user)


@pytest.mark.django_db
def test_delete_entry_removes_pdf_and_dispatches_when_present(tmp_path):
    user = get_user_model().objects.create_user(
        username="admin", password="secret", is_staff=True
    )
    novedad = NovedadModel.objects.create(
        id=uuid.uuid4(),
        fecha_desde=datetime(2026, 3, 7).date(),
        is_legacy=False,
        ingreso_generado=True,
    )
    pdf_path = tmp_path / "ingreso.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    entry = MaintenanceEntryModel.objects.create(
        id=uuid.uuid4(),
        novedad=novedad,
        entry_datetime=timezone.now(),
        pdf_path=str(pdf_path),
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

    use_case = MaintenanceEntryUseCase()

    def run_on_commit(callback):
        callback()

    with patch(
        "apps.tickets.application.use_cases.maintenance_entry_use_case."
        "transaction.on_commit",
        side_effect=run_on_commit,
    ):
        use_case.delete_entry(novedad_id=str(novedad.pk), user=user)

    assert not MaintenanceEntryEmailDispatchModel.objects.filter(
        entry_id=entry.id
    ).exists()
    assert not MaintenanceEntryModel.objects.filter(id=entry.id).exists()
    assert not pdf_path.exists()
