"""Use cases for maintenance entry workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.tickets.domain.services.intervention_suggestion import (
    InterventionHistoryItem,
    InterventionSuggestion,
    InterventionSuggestionService,
    MaintenanceCycle,
    UnitMaintenanceHistory,
)
from apps.tickets.domain.services.maintenance_labels import (
    resolve_maintenance_display_rules,
)
from apps.tickets.domain.services.recipient_resolution import (
    RecipientConfig,
    RecipientResolver,
)
from apps.tickets.infrastructure.models import (
    IntervencionTipoModel,
    LugarEmailRecipientModel,
    MaintenanceCycleModel,
    MaintenanceEntryModel,
    MaintenanceUnitModel,
    NovedadModel,
)
from apps.tickets.infrastructure.services.kilometrage_repository import (
    KilometrageRepository,
)
from apps.tickets.infrastructure.services.outlook_client import OutlookDraftClient
from apps.tickets.infrastructure.services.pdf_generator import (
    MaintenanceEntryPdfData,
    MaintenanceEntryPdfGenerator,
)


@dataclass(frozen=True)
class MaintenanceEntryDraft:
    """Draft data for the maintenance entry screen."""

    novelty: NovedadModel
    maintenance_unit: MaintenanceUnitModel | None
    unit_label: str
    brand_label: str
    model_label: str
    unit_type: str | None
    brand_code: str | None
    trigger_value: int | None
    trigger_type: str | None
    trigger_unit: str | None
    suggestion: InterventionSuggestion
    history: UnitMaintenanceHistory


@dataclass(frozen=True)
class MaintenanceEntryResult:
    """Result of maintenance entry creation."""

    entry: MaintenanceEntryModel
    pdf_path: str
    recipients_status: str
    recipients_reason: str | None
    outlook_status: str
    outlook_reason: str | None


class MaintenanceEntryUseCase:
    """Orchestrate maintenance entry creation workflow."""

    def __init__(
        self,
        suggestion_service: InterventionSuggestionService | None = None,
        recipient_resolver: RecipientResolver | None = None,
        pdf_generator: MaintenanceEntryPdfGenerator | None = None,
        outlook_client: OutlookDraftClient | None = None,
        kilometrage_repo: KilometrageRepository | None = None,
    ) -> None:
        self._suggestion_service = suggestion_service or InterventionSuggestionService()
        self._recipient_resolver = recipient_resolver or RecipientResolver()
        self._pdf_generator = pdf_generator or MaintenanceEntryPdfGenerator()
        self._outlook_client = outlook_client or OutlookDraftClient()
        self._kilometrage_repo = kilometrage_repo or KilometrageRepository()

    def prepare_draft(
        self,
        novedad_id: str,
        trigger_value: int | None,
        trigger_type: str | None,
        trigger_unit: str | None,
        entry_date: date | None = None,
    ) -> MaintenanceEntryDraft:
        """Prepare draft data and suggestion for a maintenance entry.

        Args:
            novedad_id: Novedad identifier.
            trigger_value: User trigger value (km or months).
            trigger_type: Trigger type (km or time).
            trigger_unit: Trigger unit (km or month).
            entry_date: Entry date for period calculations.

        Returns:
            Draft object with suggestion details.
        """

        novedad = (
            NovedadModel.objects.select_related(
                "maintenance_unit",
                "maintenance_unit__locomotive__brand",
                "maintenance_unit__locomotive__model",
                "maintenance_unit__railcar__brand",
                "maintenance_unit__railcar__railcar_class",
                "maintenance_unit__motorcoach__brand",
                "lugar",
            )
            .filter(pk=novedad_id)
            .first()
        )
        if not novedad:
            raise ValueError("Novedad not found")

        maintenance_unit = novedad.maintenance_unit
        unit_label = (
            maintenance_unit.number if maintenance_unit else novedad.legacy_unit_code
        )
        unit_label = unit_label or "-"

        brand_label, model_label, brand_code, model_code, unit_type = (
            self._unit_brand_model(maintenance_unit)
        )

        cycles = self._load_cycles(maintenance_unit, brand_code, model_code)
        history = self._load_history(maintenance_unit)

        suggestion = self._suggestion_service.suggest(
            unit_type=maintenance_unit.unit_type if maintenance_unit else None,
            brand_code=brand_code,
            model_code=model_code,
            cycles=cycles,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            history=history,
            current_km_value=trigger_value if trigger_type == "km" else None,
            current_period_value=trigger_value if trigger_type == "time" else None,
        )

        suggestion = self._enrich_suggestion_with_history(
            suggestion,
            maintenance_unit=maintenance_unit,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            entry_date=entry_date or timezone.now().date(),
        )

        history_summary = self._suggestion_service.get_maintenance_history(
            unit_type=maintenance_unit.unit_type if maintenance_unit else None,
            brand_code=brand_code,
            model_code=model_code,
            history=history,
            current_km_value=trigger_value if trigger_type == "km" else None,
            current_period_value=trigger_value if trigger_type == "time" else None,
            entry_date=entry_date or timezone.now().date(),
        )

        history_summary = self._enrich_history_with_km(
            history_summary,
            maintenance_unit=maintenance_unit,
            current_km_value=trigger_value if trigger_type == "km" else None,
        )

        return MaintenanceEntryDraft(
            novelty=novedad,
            maintenance_unit=maintenance_unit,
            unit_label=unit_label,
            brand_label=brand_label,
            model_label=model_label,
            unit_type=unit_type,
            brand_code=brand_code,
            trigger_value=trigger_value,
            trigger_type=trigger_type,
            trigger_unit=trigger_unit,
            suggestion=suggestion,
            history=history_summary,
        )

    def create_entry(
        self,
        novedad_id: str,
        entry_datetime: datetime,
        trigger_type: str | None,
        trigger_value: int | None,
        trigger_unit: str | None,
        lugar_id: str | None,
        selected_intervention_code: str | None,
        checklist_tasks: str | None,
        observations: str | None,
        user,
    ) -> MaintenanceEntryResult:
        """Create a maintenance entry, PDF, and Outlook draft.

        Args:
            novedad_id: Novedad identifier.
            entry_datetime: Entry timestamp.
            trigger_type: Trigger type.
            trigger_value: Trigger value.
            trigger_unit: Trigger unit.
            lugar_id: Lugar identifier.
            selected_intervention_code: Intervention code selected by user.
            checklist_tasks: Task list text.
            observations: Observations text.
            user: Django user executing the action.

        Returns:
            MaintenanceEntryResult with processing status.
        """

        draft = self.prepare_draft(
            novedad_id=novedad_id,
            trigger_value=trigger_value,
            trigger_type=trigger_type,
            trigger_unit=trigger_unit,
            entry_date=entry_datetime.date(),
        )

        selected_code = selected_intervention_code or draft.suggestion.suggested_code
        selected_intervention = None
        if selected_code:
            selected_intervention = IntervencionTipoModel.objects.filter(
                codigo__iexact=selected_code
            ).first()

        entry = MaintenanceEntryModel.objects.create(
            novedad=draft.novelty,
            maintenance_unit=draft.maintenance_unit,
            lugar_id=lugar_id
            or (draft.novelty.lugar_id if draft.novelty.lugar_id else None),
            entry_datetime=entry_datetime,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            trigger_unit=trigger_unit,
            suggested_intervention_code=draft.suggestion.suggested_code,
            selected_intervention=selected_intervention,
            checklist_tasks=checklist_tasks or None,
            observations=observations or None,
            created_by=user if user and user.is_authenticated else None,
        )

        pdf_path = self._generate_pdf(entry, draft, user)
        entry.pdf_path = pdf_path
        entry.save(update_fields=["pdf_path", "updated_at"])

        recipients = self._resolve_recipients(
            lugar_id=str(entry.lugar_id) if entry.lugar_id else None,
            unit_type=draft.maintenance_unit.unit_type
            if draft.maintenance_unit
            else None,
        )

        outlook_status = "skipped"
        outlook_reason = None
        if recipients.status == "ok":
            subject, body = self._build_email_content(entry, draft)
            try:
                self._outlook_client.create_draft(
                    to_recipients=recipients.to,
                    cc_recipients=recipients.cc,
                    subject=subject,
                    body=body,
                    attachment_path=pdf_path,
                    sender_email=getattr(user, "email", None),
                )
                outlook_status = "ok"
            except Exception as exc:  # pragma: no cover - integration error
                outlook_status = "error"
                outlook_reason = exc.args[0] if exc.args else str(exc)
        else:
            outlook_reason = recipients.reason

        return MaintenanceEntryResult(
            entry=entry,
            pdf_path=pdf_path,
            recipients_status=recipients.status,
            recipients_reason=recipients.reason,
            outlook_status=outlook_status,
            outlook_reason=outlook_reason,
        )

    def _load_cycles(
        self,
        maintenance_unit: MaintenanceUnitModel | None,
        brand_code: str | None,
        model_code: str | None,
    ) -> list[MaintenanceCycle]:
        if not maintenance_unit or not brand_code:
            return []

        cycles = MaintenanceCycleModel.objects.filter(
            rolling_stock_type=maintenance_unit.unit_type,
            brand__code__iexact=brand_code,
            is_active=True,
        )

        model_cycles = cycles.filter(model__code__iexact=model_code)
        if model_code and model_cycles.exists():
            cycles = model_cycles
        else:
            cycles = cycles.filter(model__isnull=True)

        return [
            MaintenanceCycle(
                intervention_code=cycle.intervention_code,
                intervention_name=cycle.intervention_name,
                trigger_type=cycle.trigger_type,
                trigger_value=cycle.trigger_value,
                trigger_unit=cycle.trigger_unit,
            )
            for cycle in cycles
        ]

    def _load_history(
        self, maintenance_unit: MaintenanceUnitModel | None
    ) -> list[InterventionHistoryItem]:
        if not maintenance_unit:
            return []

        items = (
            NovedadModel.objects.filter(
                maintenance_unit=maintenance_unit, fecha_hasta__isnull=False
            )
            .select_related("intervencion")
            .order_by("-fecha_desde")
        )
        history = []
        for item in items:
            code = item.intervencion.codigo if item.intervencion else None
            if code:
                history.append(
                    InterventionHistoryItem(
                        intervention_code=code,
                        date_from=item.fecha_desde,
                        date_until=item.fecha_hasta,
                    )
                )
        return history

    def _enrich_suggestion_with_history(
        self,
        suggestion: InterventionSuggestion,
        maintenance_unit: MaintenanceUnitModel | None,
        trigger_type: str | None,
        trigger_value: int | None,
        entry_date: date,
    ) -> InterventionSuggestion:
        if not maintenance_unit or not suggestion.last_intervention_date:
            return suggestion

        km_since = suggestion.km_since_last
        period_since = suggestion.period_since_last

        if trigger_type == "km" and trigger_value is not None:
            last_km = self._kilometrage_repo.get_km_at_or_before(
                maintenance_unit.number, suggestion.last_intervention_date
            )
            if last_km is not None:
                km_since = max(trigger_value - last_km, 0)

        if trigger_type == "time" and trigger_value is not None:
            period_since = self._months_between(
                suggestion.last_intervention_date, entry_date
            )

        return InterventionSuggestion(
            status=suggestion.status,
            reason=suggestion.reason,
            suggested_code=suggestion.suggested_code,
            suggested_name=suggestion.suggested_name,
            last_intervention_code=suggestion.last_intervention_code,
            last_intervention_date=suggestion.last_intervention_date,
            km_since_last=km_since,
            period_since_last=period_since,
        )

    def _enrich_history_with_km(
        self,
        history: UnitMaintenanceHistory,
        maintenance_unit: MaintenanceUnitModel | None,
        current_km_value: int | None,
    ) -> UnitMaintenanceHistory:
        if not maintenance_unit or current_km_value is None:
            return history

        unit_number = maintenance_unit.number

        history_items = self._load_history(maintenance_unit)

        def get_date_for_code(code: str) -> date | None:
            for item in history_items:
                if item.intervention_code.upper() == code:
                    return item.date_until or item.date_from
            return None

        def get_km_since_for_code(code: str) -> int | None:
            target_date = get_date_for_code(code)
            if target_date is None:
                return None
            return self._kilometrage_repo.get_km_since(unit_number, target_date)

        last_rg_km_since = get_km_since_for_code("RG")
        last_numeral_km_since = None
        if history.last_numeral_code:
            last_numeral_km_since = get_km_since_for_code(history.last_numeral_code)
        last_rp_km_since = None
        if history.last_rp_code:
            last_rp_km_since = get_km_since_for_code(history.last_rp_code)
        last_abc_km_since = get_km_since_for_code("ABC")

        return UnitMaintenanceHistory(
            last_rg_date=history.last_rg_date,
            last_rg_km_since=last_rg_km_since,
            last_numeral_code=history.last_numeral_code,
            last_numeral_date=history.last_numeral_date,
            last_numeral_km_since=last_numeral_km_since,
            last_rp_code=history.last_rp_code,
            last_rp_date=history.last_rp_date,
            last_rp_km_since=last_rp_km_since,
            last_abc_date=history.last_abc_date,
            last_abc_km_since=last_abc_km_since,
        )

    def _resolve_recipients(self, lugar_id: str | None, unit_type: str | None):
        if not unit_type:
            return self._recipient_resolver.resolve(None, "", [])

        recipients = [
            RecipientConfig(
                lugar_id=str(item.lugar_id) if item.lugar_id else None,
                unit_type=item.unit_type,
                recipient_type=item.recipient_type,
                email=item.email,
            )
            for item in LugarEmailRecipientModel.objects.filter(is_active=True)
        ]

        return self._recipient_resolver.resolve(lugar_id, unit_type, recipients)

    def _generate_pdf(
        self, entry: MaintenanceEntryModel, draft: MaintenanceEntryDraft, user
    ) -> str:
        entry_number = str(entry.id)[:8]
        unit_label = draft.unit_label
        user_label = getattr(user, "get_full_name", lambda: "")() or getattr(
            user, "username", ""
        )
        intervention_label = draft.suggestion.suggested_code or "-"
        if entry.selected_intervention:
            intervention_label = (
                f"{entry.selected_intervention.codigo} - "
                f"{entry.selected_intervention.descripcion}"
            )
        lugar_label = (
            entry.lugar.descripcion
            if entry.lugar
            else (draft.novelty.lugar.descripcion if draft.novelty.lugar else "-")
        )

        trigger_label = "-"
        if entry.trigger_type == "km" and entry.trigger_value is not None:
            formatted_km = f"{entry.trigger_value:,}".replace(",", ".")
            trigger_label = f"KM RG: {formatted_km}"
        if entry.trigger_type == "time" and entry.trigger_value is not None:
            trigger_label = f"Período: {entry.trigger_value} meses"

        # Format history dates and km with European separator
        def fmt_km(val):
            if val is None:
                return None
            return f"{val:,}".replace(",", ".")

        def fmt_date(val):
            if val is None:
                return None
            return val.strftime("%d/%m/%Y")

        history = draft.history
        data = MaintenanceEntryPdfData(
            entry_number=entry_number,
            unit_label=unit_label,
            unit_type=draft.unit_type or "",
            brand_label=draft.brand_label,
            brand_code=draft.brand_code,
            model_label=draft.model_label,
            user_label=user_label or "-",
            intervention_label=intervention_label,
            entry_datetime=entry.entry_datetime,
            exit_datetime="-",
            lugar_label=lugar_label,
            trigger_label=trigger_label,
            observations=entry.observations or "-",
            checklist_tasks=self._split_tasks(entry.checklist_tasks),
            # Historial
            last_rg_date=fmt_date(history.last_rg_date) if history else None,
            last_rg_km=fmt_km(history.last_rg_km_since) if history else None,
            last_numeral_code=history.last_numeral_code if history else None,
            last_numeral_date=fmt_date(history.last_numeral_date) if history else None,
            last_numeral_km=fmt_km(history.last_numeral_km_since) if history else None,
            last_rp_code=history.last_rp_code if history else None,
            last_rp_date=fmt_date(history.last_rp_date) if history else None,
            last_rp_km=fmt_km(history.last_rp_km_since) if history else None,
            last_abc_date=fmt_date(history.last_abc_date) if history else None,
            last_abc_km=fmt_km(history.last_abc_km_since) if history else None,
        )

        pdf_bytes = self._pdf_generator.generate(data)
        output_dir = Path(settings.BASE_DIR) / "generated" / "maintenance_entries"
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"ingreso_{entry.id}.pdf"
        file_path = output_dir / file_name
        file_path.write_bytes(pdf_bytes)
        return str(file_path)

    def _build_email_content(
        self, entry: MaintenanceEntryModel, draft: MaintenanceEntryDraft
    ):
        unit_label = draft.unit_label
        intervention_label = (
            entry.selected_intervention.codigo if entry.selected_intervention else "-"
        )
        lugar_label = entry.lugar.descripcion if entry.lugar else "-"

        # Get unit type for title
        unit_type = draft.unit_type or ""
        if unit_type == "locomotora":
            unit_type_title = "Locomotora"
        elif unit_type == "coche_remolcado":
            unit_type_title = "Coche Remolcado"
        elif unit_type == "coche_motor":
            unit_type_title = "Coche Motor"
        else:
            unit_type_title = "Unidad"

        subject = f"Ingreso a mantenimiento - {unit_label} - {intervention_label}"

        def fmt_km(val):
            if val is None:
                return "-"
            return f"{val:,}".replace(",", ".")

        def fmt_date(val):
            if val is None:
                return "-"
            return val.strftime("%d/%m/%Y")

        history = draft.history
        created_by = getattr(entry, "created_by", None)
        sender_name = ""
        if created_by:
            sender_name = getattr(created_by, "get_full_name", lambda: "")() or getattr(
                created_by,
                "username",
                "",
            )
        display_rules = resolve_maintenance_display_rules(
            draft.unit_type,
            draft.brand_code,
        )

        if display_rules.use_rp_history:
            secondary_code = history.last_rp_code if history else None
            secondary_date = history.last_rp_date if history else None
            secondary_km = history.last_rp_km_since if history else None
        else:
            secondary_code = history.last_numeral_code if history else None
            secondary_date = history.last_numeral_date if history else None
            secondary_km = history.last_numeral_km_since if history else None

        model_detail_label = "Clase" if draft.unit_type == "coche_remolcado" else "Modelo"

        body_lines = [
            "=" * 50,
            f"MATERIAL RODANTE - INGRESO DE {unit_type_title.upper()}",
            "=" * 50,
            "",
            f"Unidad: {unit_label}",
            f"Marca: {draft.brand_label}",
            f"{model_detail_label}: {draft.model_label}",
            f"Lugar: {lugar_label}",
            f"Intervención: {intervention_label}",
            f"Fecha ingreso: {entry.entry_datetime:%d/%m/%Y %H:%M}",
        ]

        if entry.trigger_type == "km" and entry.trigger_value is not None:
            body_lines.append(f"KM: {fmt_km(entry.trigger_value)}")
        if entry.trigger_type == "time" and entry.trigger_value is not None:
            body_lines.append(f"Período: {entry.trigger_value} meses")

        body_lines.append("")
        body_lines.append("-" * 50)
        body_lines.append("HISTORIAL DE MANTENIMIENTO")
        body_lines.append("-" * 50)

        # RG
        if history and history.last_rg_date:
            body_lines.append(
                f"Última RG: {fmt_date(history.last_rg_date)} "
                f"({fmt_km(history.last_rg_km_since)} km)"
            )
        else:
            body_lines.append("Última RG: Sin registro")

        # Dynamic maintenance label
        if secondary_code:
            body_lines.append(
                f"{display_rules.history_label}: {secondary_code} "
                f"({fmt_date(secondary_date)}) "
                f"({fmt_km(secondary_km)} km)"
            )
        else:
            body_lines.append(f"{display_rules.history_label}: Sin registro")

        # ABC
        if display_rules.show_abc:
            if history and history.last_abc_date:
                body_lines.append(
                    f"Última ABC: {fmt_date(history.last_abc_date)} "
                    f"({fmt_km(history.last_abc_km_since)} km)"
                )
            else:
                body_lines.append("Última ABC: Sin registro")

        if entry.observations:
            body_lines.append("")
            body_lines.append("-" * 50)
            body_lines.append("OBSERVACIONES")
            body_lines.append("-" * 50)
            body_lines.append(entry.observations)

        if sender_name:
            body_lines.append("")
            body_lines.append(f"Saludos, {sender_name}")

        return subject, "\n".join(body_lines)

    @staticmethod
    def _months_between(start_date: date, end_date: date) -> int:
        if end_date < start_date:
            return 0
        return (end_date.year - start_date.year) * 12 + (
            end_date.month - start_date.month
        )

    @staticmethod
    def _split_tasks(tasks_raw: str | None) -> list[str]:
        if not tasks_raw:
            return []
        return [line.strip() for line in tasks_raw.splitlines() if line.strip()]

    @staticmethod
    def _unit_brand_model(maintenance_unit: MaintenanceUnitModel | None):
        if not maintenance_unit:
            return "-", "-", None, None

        if hasattr(maintenance_unit, "locomotive"):
            brand = maintenance_unit.locomotive.brand
            model = maintenance_unit.locomotive.model
            return (
                brand.name,
                model.name,
                brand.code,
                model.code,
                maintenance_unit.unit_type,
            )

        if hasattr(maintenance_unit, "railcar"):
            brand = maintenance_unit.railcar.brand
            railcar_class = maintenance_unit.railcar.railcar_class
            return (
                brand.name,
                railcar_class.code,
                brand.code,
                None,
                maintenance_unit.unit_type,
            )

        if hasattr(maintenance_unit, "motorcoach"):
            brand = maintenance_unit.motorcoach.brand
            return (
                brand.name,
                maintenance_unit.motorcoach.configuration,
                brand.code,
                None,
                maintenance_unit.unit_type,
            )

        return "-", "-", None, None, None
