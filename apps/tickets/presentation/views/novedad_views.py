"""Views for the novedad CRUD workflows."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)
from apps.tickets.presentation.forms import NovedadFilterForm, NovedadForm


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
        return queryset.filter(maintenance_unit__unit_type=unit_type)

    def _unit_type_display(self) -> str:
        unit_type = self.kwargs.get("unit_type")
        if unit_type == MaintenanceUnitModel.UnitType.LOCOMOTIVE:
            return "Locomotoras / Coches Motor"
        if unit_type == MaintenanceUnitModel.UnitType.RAILCAR:
            return "Coches Remolcados"
        if unit_type == MaintenanceUnitModel.UnitType.MOTORCOACH:
            return "Coches Motor"
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


class NovedadReferenceMixin:
    """Provide reference data for novedad forms."""

    def _reference_options(self):
        unit_options = [
            {
                "number": unit.number,
                "display": f"{unit.number} ({unit.get_unit_type_display()})",
            }
            for unit in MaintenanceUnitModel.objects.order_by("number")
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
        if unit_type:
            kwargs["unit_type"] = unit_type
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
        return context

    def get_success_url(self):
        unit_type = self.kwargs.get("unit_type")
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
        return context

    def get_success_url(self):
        return reverse_lazy("tickets:novedad_detail", kwargs={"pk": self.object.pk})


class NovedadDeleteView(LoginRequiredMixin, DeleteView):
    """Remove a novedad record."""

    model = NovedadModel
    template_name = "tickets/novedad_confirm_delete.html"
    context_object_name = "novedad"
    success_url = reverse_lazy("tickets:novedad_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Novedad eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
