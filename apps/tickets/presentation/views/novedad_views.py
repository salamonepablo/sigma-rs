"""Views for the novedad CRUD workflows."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from apps.tickets.application.formatters.km_format import format_km_eu
from apps.tickets.application.use_cases.legacy_sync_use_case import LegacySyncUseCase
from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryRequestCache,
    MaintenanceEntryUseCase,
)
from apps.tickets.infrastructure.services.kilometrage_repository import (
    KilometrageRepository,
)
from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)
from apps.tickets.presentation.forms import (
    MaintenanceEntryForm,
    NovedadFilterForm,
    NovedadForm,
)


class NovedadListView(LoginRequiredMixin, ListView):
    """List novedad records with filtering capabilities."""

    model = NovedadModel
    template_name = "tickets/novedad_list.html"
    context_object_name = "novedades"
    paginate_by = 50
    DEFAULT_RANGE_DAYS = 60
    RANGE_STEP_DAYS = 30
    MAX_RANGE_DAYS = 365

    def get_queryset(self):
        queryset = (
            NovedadModel.objects.select_related(
                "maintenance_unit",
                "intervencion",
                "lugar",
            )
            .order_by("-fecha_desde", "-created_at")
            .all()
        )

        category = self.kwargs.get("category")
        if category:
            queryset = self._filter_by_category(queryset, category)

        self.range_days = self._determine_range_days()
        today = timezone.now().date()
        self.default_date_from = today - timedelta(days=self.range_days)
        self.default_date_to = today
        url_unit_type = self.kwargs.get("unit_type")
        self.filter_form = NovedadFilterForm(
            self.request.GET or None,
            initial={
                "unit_type": url_unit_type,
                "date_from": self.default_date_from,
                "date_to": self.default_date_to,
            },
        )

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            queryset = self._filter_by_unit_type(
                queryset, data.get("unit_type") or url_unit_type
            )

            if data.get("intervencion"):
                queryset = queryset.filter(intervencion=data["intervencion"])

            if data.get("lugar"):
                queryset = queryset.filter(lugar=data["lugar"])

            date_from = data.get("date_from")
            date_to = data.get("date_to")

            if date_from:
                queryset = queryset.filter(fecha_desde__gte=date_from)
                self.using_default_range = False
            else:
                queryset = queryset.filter(fecha_desde__gte=self.default_date_from)
                self.using_default_range = True

            if date_to:
                queryset = queryset.filter(fecha_desde__lte=date_to)
            else:
                queryset = queryset.filter(fecha_desde__lte=self.default_date_to)

            include_al = data.get("include_alistamientos")

            if search := data.get("search"):
                queryset = queryset.filter(
                    Q(maintenance_unit__number__icontains=search)
                    | Q(legacy_unit_code__icontains=search)
                    | Q(observaciones__icontains=search)
                    | Q(intervencion__codigo__icontains=search)
                )

            if not include_al:
                queryset = queryset.exclude(
                    Q(intervencion__codigo__iexact="AL")
                    | Q(legacy_intervencion_codigo__iexact="AL")
                )
        else:
            queryset = self._filter_by_unit_type(queryset, url_unit_type)
            queryset = queryset.filter(
                fecha_desde__gte=self.default_date_from,
                fecha_desde__lte=self.default_date_to,
            )
            self.using_default_range = True
            queryset = queryset.exclude(
                Q(intervencion__codigo__iexact="AL")
                | Q(legacy_intervencion_codigo__iexact="AL")
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["unit_type"] = self.kwargs.get("unit_type")
        context["category"] = self.kwargs.get("category")
        context["unit_type_display"] = self._unit_type_display()
        context["range_days"] = self.range_days
        context["default_date_from"] = self.default_date_from
        context["show_processing_message"] = self.range_days > self.DEFAULT_RANGE_DAYS
        context["using_default_range"] = getattr(self, "using_default_range", False)
        context["more_history_query"] = self._build_more_history_query()
        return context

    def _filter_by_unit_type(self, queryset, unit_type):
        if not unit_type:
            return queryset
        if unit_type == MaintenanceUnitModel.UnitType.LOCOMOTIVE:
            return queryset.filter(
                maintenance_unit__unit_type__in=[
                    MaintenanceUnitModel.UnitType.LOCOMOTIVE,
                    MaintenanceUnitModel.UnitType.MOTORCOACH,
                ]
            )
        if unit_type == MaintenanceUnitModel.UnitType.WAGON:
            return queryset.filter(maintenance_unit__unit_type=unit_type)
        return queryset.filter(maintenance_unit__unit_type=unit_type)

    def _filter_by_category(self, queryset, category: str):
        unit_type_map = {
            "traccion": [
                MaintenanceUnitModel.UnitType.LOCOMOTIVE,
                MaintenanceUnitModel.UnitType.MOTORCOACH,
            ],
            "ccrr": [MaintenanceUnitModel.UnitType.RAILCAR],
            "carga": [MaintenanceUnitModel.UnitType.WAGON],
        }
        unit_types = unit_type_map.get(category)
        if not unit_types:
            return queryset.filter(maintenance_unit__rolling_stock_category=category)

        legacy_units = MaintenanceUnitModel.objects.filter(
            unit_type__in=unit_types
        ).values_list("number", flat=True)

        return queryset.filter(
            Q(maintenance_unit__rolling_stock_category=category)
            | Q(maintenance_unit__unit_type__in=unit_types)
            | Q(
                maintenance_unit__isnull=True,
                legacy_unit_code__in=legacy_units,
            )
        )

    def _unit_type_display(self) -> str:
        unit_type = self.kwargs.get("unit_type")
        category = self.kwargs.get("category")
        if category == "traccion":
            return "Locomotoras y CM"
        if category == "ccrr":
            return "Coches Remolcados"
        if category == "carga":
            return "Vagones"
        if unit_type == MaintenanceUnitModel.UnitType.LOCOMOTIVE:
            return "Locomotoras / Coches Motor"
        if unit_type == MaintenanceUnitModel.UnitType.RAILCAR:
            return "Coches Remolcados"
        if unit_type == MaintenanceUnitModel.UnitType.MOTORCOACH:
            return "Coches Motor"
        if unit_type == MaintenanceUnitModel.UnitType.WAGON:
            return "Vagones"
        return "Todas las Unidades"

    def _determine_range_days(self) -> int:
        try:
            requested = int(self.request.GET.get("range_days", self.DEFAULT_RANGE_DAYS))
        except (TypeError, ValueError):
            requested = self.DEFAULT_RANGE_DAYS
        requested = max(self.DEFAULT_RANGE_DAYS, requested)
        return min(requested, self.MAX_RANGE_DAYS)

    def _build_more_history_query(self) -> str | None:
        next_range = min(self.range_days + self.RANGE_STEP_DAYS, self.MAX_RANGE_DAYS)
        if next_range == self.range_days:
            return None
        params = self.request.GET.copy()
        mutable = params.dict()
        mutable.pop("page", None)
        mutable["range_days"] = str(next_range)
        return f"?{urlencode(mutable)}"


class NovedadSyncView(LoginRequiredMixin, View):
    """Trigger synchronous sync for novedades and kilometrage."""

    def post(self, request, *args, **kwargs):
        next_url = (
            request.POST.get("next")
            or request.META.get("HTTP_REFERER")
            or reverse("tickets:novedad_list")
        )
        use_case = LegacySyncUseCase()

        try:
            result = use_case.run()
            message = (
                "Sincronizacion completada. "
                f"Novedades: {result.novedades.inserted} · "
                f"Kilometraje: {result.kilometrage.inserted}"
            )
            messages.success(request, message)
        except Exception as exc:
            messages.error(
                request,
                f"No se pudo sincronizar novedades y kilometraje. Detalle: {exc}",
            )

        return redirect(next_url)


class NovedadDetailView(LoginRequiredMixin, DetailView):
    """Show a single novedad record."""

    model = NovedadModel
    template_name = "tickets/novedad_detail.html"
    context_object_name = "novedad"

    def get_queryset(self):
        return NovedadModel.objects.select_related(
            "maintenance_unit",
            "intervencion",
            "lugar",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = None
        if self.object and self.object.maintenance_unit:
            category = self.object.maintenance_unit.rolling_stock_category
        context["category"] = category
        return context


class MaintenanceEntryCreateView(LoginRequiredMixin, FormView):
    """Create maintenance entry from a novedad."""

    template_name = "tickets/maintenance_entry_form.html"
    form_class = MaintenanceEntryForm

    def dispatch(self, request, *args, **kwargs):
        self.novedad = (
            NovedadModel.objects.select_related(
                "maintenance_unit",
                "lugar",
                "maintenance_unit__locomotive__brand",
                "maintenance_unit__locomotive__model",
                "maintenance_unit__railcar__brand",
                "maintenance_unit__railcar__railcar_class",
                "maintenance_unit__motorcoach__brand",
            )
            .filter(pk=kwargs.get("pk"))
            .first()
        )
        if not self.novedad:
            messages.error(request, "No se encontró la novedad seleccionada.")
            return super().dispatch(request, *args, **kwargs)
        self._request_cache = None
        if getattr(settings, "INGRESO_REQUEST_CACHE_ENABLED", False):
            self._request_cache = MaintenanceEntryRequestCache()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        draft = self._get_draft()
        if draft and draft.suggestion.suggested_code:
            kwargs["suggested_code"] = draft.suggestion.suggested_code
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if not self.novedad:
            return initial
        initial["lugar"] = self.novedad.lugar
        initial["observations"] = self.novedad.observaciones
        if self.novedad.intervencion_id:
            initial["selected_intervention"] = self.novedad.intervencion_id
        km_since_rg, days_since, intervention_type, intervention_date, km_since_last = (
            self._prefill_trigger_value()
        )
        if km_since_rg is not None:
            initial["trigger_km"] = self._format_km(km_since_rg)
        if intervention_type:
            initial["last_intervention_type"] = intervention_type
        if intervention_date:
            initial["last_intervention_date"] = intervention_date
        if km_since_last is not None:
            initial["last_intervention_km"] = self._format_km(km_since_last)
        if days_since is not None:
            initial["last_intervention_days"] = days_since
        draft = self._get_draft()
        if draft and draft.pending_ticket_tasks and not initial.get("checklist_tasks"):
            initial["checklist_tasks"] = "\n".join(draft.pending_ticket_tasks)
        return initial

    def form_valid(self, form):
        if not self.novedad:
            messages.error(self.request, "No se pudo crear el ingreso.")
            return self.form_invalid(form)

        # Check if ingreso already generated
        if self.novedad.ingreso_generado:
            messages.error(
                self.request,
                "Ya se generó un ingreso para esta novedad. "
                "Si necesitas regenerarlo, contacta al administrador.",
            )
            return self.form_invalid(form)

        # Get terminal_id from header (if provided by frontend/tray bridge)
        terminal_id = self.request.headers.get("X-TERMINAL-ID")

        use_case = MaintenanceEntryUseCase()
        result = use_case.create_entry(
            novedad_id=str(self.novedad.pk),
            entry_datetime=form.cleaned_data["entry_datetime"],
            trigger_type=form.resolved_trigger_type,
            trigger_value=form.resolved_trigger_value,
            trigger_unit=form.resolved_trigger_unit,
            lugar_id=str(form.cleaned_data["lugar"].pk)
            if form.cleaned_data.get("lugar")
            else None,
            selected_intervention_code=(
                form.cleaned_data["selected_intervention"].codigo
                if form.cleaned_data.get("selected_intervention")
                else None
            ),
            checklist_tasks=form.cleaned_data.get("checklist_tasks"),
            observations=form.cleaned_data.get("observations"),
            user=self.request.user,
            terminal_id=terminal_id,
            request_cache=getattr(self, "_request_cache", None),
        )

        messages.success(
            self.request, "Ingreso a mantenimiento generado correctamente."
        )

        if result.recipients_status != "ok":
            messages.warning(
                self.request,
                "No se encontraron destinatarios configurados para el lugar. "
                "Revise la configuración de destinatarios.",
            )
        elif result.outlook_status == "error":
            reason = result.outlook_reason or "error desconocido"
            messages.warning(
                self.request,
                f"No se pudo encolar el envio de correo: {reason}. "
                "El PDF fue generado correctamente.",
            )
        elif result.outlook_status == "pending":
            messages.info(
                self.request,
                "El correo quedo pendiente para envio desde Outlook local.",
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["novedad"] = self.novedad
        draft = self._get_draft()
        context["draft"] = draft
        return context

    def get_success_url(self):
        return reverse_lazy("tickets:novedad_detail", kwargs={"pk": self.novedad.pk})

    def _get_draft(self):
        if hasattr(self, "_draft_cache") and self._draft_cache is not None:
            return self._draft_cache
        if not self.novedad:
            return None
        km_value, _, _, _, _ = self._prefill_trigger_value()
        trigger_value = km_value
        trigger_type = "km" if trigger_value is not None else None
        trigger_unit = "km" if trigger_value is not None else None
        use_case = MaintenanceEntryUseCase()
        self._draft_cache = use_case.prepare_draft(
            novedad_id=str(self.novedad.pk),
            trigger_value=trigger_value,
            trigger_type=trigger_type,
            trigger_unit=trigger_unit,
            request_cache=getattr(self, "_request_cache", None),
        )
        return self._draft_cache

    def _prefill_trigger_value(self):
        if not self.novedad or not self.novedad.maintenance_unit:
            return None, None, None, None, None
        use_case = MaintenanceEntryUseCase()
        repo = KilometrageRepository()
        latest_km = repo.get_latest_km(self.novedad.maintenance_unit.number)
        if latest_km is None:
            return None, None, None, None, None
        draft = use_case.prepare_draft(
            novedad_id=str(self.novedad.pk),
            trigger_value=latest_km,
            trigger_type="km",
            trigger_unit="km",
            request_cache=getattr(self, "_request_cache", None),
        )

        km_since_rg = draft.history.last_rg_km_since
        entry_date = timezone.now().date()

        last_intervention_date = None
        last_intervention_code = None
        last_intervention_km = None
        unit_type = self.novedad.maintenance_unit.unit_type
        if unit_type == "locomotora":
            brand = getattr(
                getattr(self.novedad.maintenance_unit, "locomotive", None),
                "brand",
                None,
            )
            brand_code = brand.code if brand else None
            model = getattr(
                getattr(self.novedad.maintenance_unit, "locomotive", None),
                "model",
                None,
            )
            model_code = model.code if model else None

            priority_codes = []
            if model_code and model_code.startswith("CKD"):
                priority_codes = [
                    "RG",
                    "720K",
                    "360K",
                    "R6",
                    "R5",
                    "R4",
                    "R3",
                    "R2",
                    "R1",
                    "EX",
                ]
            else:
                priority_codes = [
                    "RG",
                    "N11",
                    "N10",
                    "N9",
                    "N8",
                    "N7",
                    "N6",
                    "N5",
                    "N4",
                    "N3",
                    "N2",
                    "N1",
                    "ABC",
                    "AB",
                    "A",
                ]
        elif unit_type == "coche_remolcado":
            brand = getattr(
                getattr(self.novedad.maintenance_unit, "railcar", None),
                "brand",
                None,
            )
            brand_code = brand.code if brand else None
            if brand_code == "CNR":
                priority_codes = ["A4", "A3", "A2", "A1", "SEM", "MEN"]
            else:
                priority_codes = ["RG", "RP", "ABC", "AB", "A"]
        elif unit_type == "coche_motor":
            priority_codes = ["RG", "RP", "SEM", "MEN"]
        else:
            priority_codes = []

        if priority_codes:
            last_intervention = (
                NovedadModel.objects.filter(
                    maintenance_unit=self.novedad.maintenance_unit,
                    intervencion__codigo__in=priority_codes,
                    fecha_hasta__isnull=False,
                )
                .select_related("intervencion")
                .order_by("-fecha_hasta")
                .first()
            )
            if last_intervention and last_intervention.intervencion:
                last_intervention_code = last_intervention.intervencion.codigo
                last_intervention_date = last_intervention.fecha_hasta
                if last_intervention_date:
                    last_intervention_km = repo.get_km_since(
                        self.novedad.maintenance_unit.number,
                        last_intervention_date,
                    )

        days_since = None
        if last_intervention_date:
            days_since = (entry_date - last_intervention_date).days

        return (
            km_since_rg,
            days_since,
            last_intervention_code,
            last_intervention_date,
            last_intervention_km,
        )

    @staticmethod
    def _format_km(value: Decimal | int | str | None) -> str:
        return format_km_eu(value)


class NovedadReferenceMixin:
    """Provide reference data for novedad forms."""

    def _reference_options(self):
        category = self.kwargs.get("category")
        unit_queryset = MaintenanceUnitModel.objects.order_by("number")
        if category:
            unit_queryset = unit_queryset.filter(rolling_stock_category=category)
        unit_options = [
            {
                "number": unit.number,
                "display": f"{unit.number} ({unit.get_unit_type_display()})",
            }
            for unit in unit_queryset
        ]
        intervencion_options = list(
            IntervencionTipoModel.objects.filter(is_active=True)
            .order_by("codigo")
            .values("codigo", "descripcion")
        )
        lugar_options = [
            {
                "code": option.short_desc or option.codigo,
                "label": f"{option.codigo} - {option.descripcion}",
            }
            for option in LugarModel.objects.filter(is_active=True).order_by(
                "descripcion"
            )
        ]

        return {
            "unit_options": unit_options,
            "intervencion_options": intervencion_options,
            "lugar_options": lugar_options,
        }


class NovedadCreateView(NovedadReferenceMixin, LoginRequiredMixin, CreateView):
    """Create a new novedad entry."""

    model = NovedadModel
    form_class = NovedadForm
    template_name = "tickets/novedad_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        unit_type = self.kwargs.get("unit_type")
        category = self.kwargs.get("category")
        if unit_type:
            kwargs["unit_type"] = unit_type
        elif category == "traccion":
            kwargs["unit_type"] = "locomotora"
        elif category == "ccrr":
            kwargs["unit_type"] = "coche_remolcado"
        elif category == "carga":
            kwargs["unit_type"] = "vagon"
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Novedad registrada correctamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._reference_options())
        context["action"] = "Crear"
        context["unit_type"] = self.kwargs.get("unit_type")
        context["category"] = self.kwargs.get("category")
        return context

    def get_success_url(self):
        unit_type = self.kwargs.get("unit_type")
        category = self.kwargs.get("category")
        if category == "traccion":
            return reverse_lazy("tickets:novedad_list_locomotoras")
        elif category == "ccrr":
            return reverse_lazy("tickets:novedad_list_ccrr")
        elif category == "carga":
            return reverse_lazy("tickets:novedad_list_vagones")
        if unit_type:
            return reverse_lazy(
                "tickets:novedad_list_by_type", kwargs={"unit_type": unit_type}
            )
        return reverse_lazy("tickets:novedad_list")


class NovedadUpdateView(NovedadReferenceMixin, LoginRequiredMixin, UpdateView):
    """Edit an existing novedad record."""

    model = NovedadModel
    form_class = NovedadForm
    template_name = "tickets/novedad_form.html"
    context_object_name = "novedad"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object and self.object.maintenance_unit:
            kwargs["unit_type"] = self.object.maintenance_unit.unit_type
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Novedad actualizada correctamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._reference_options())
        context["action"] = "Editar"
        if self.object and self.object.maintenance_unit:
            context["unit_type"] = self.object.maintenance_unit.unit_type
            context["category"] = self.object.maintenance_unit.rolling_stock_category
        return context

    def get_success_url(self):
        return reverse_lazy("tickets:novedad_detail", kwargs={"pk": self.object.pk})


class NovedadDeleteView(LoginRequiredMixin, DeleteView):
    """Remove a novedad record."""

    model = NovedadModel
    template_name = "tickets/novedad_confirm_delete.html"
    context_object_name = "novedad"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Novedad eliminada correctamente.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        category = None
        if self.object and self.object.maintenance_unit:
            category = self.object.maintenance_unit.rolling_stock_category
        if category == "traccion":
            return reverse_lazy("tickets:novedad_list_locomotoras")
        if category == "ccrr":
            return reverse_lazy("tickets:novedad_list_ccrr")
        if category == "carga":
            return reverse_lazy("tickets:novedad_list_vagones")
        return reverse_lazy("tickets:novedad_list")
