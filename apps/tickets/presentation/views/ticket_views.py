"""Views for Ticket CRUD operations."""

import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.tickets.models import (
    FailureTypeModel,
    MaintenanceUnitModel,
    SupervisorModel,
    TicketModel,
    TrainNumberModel,
)
from apps.tickets.presentation.forms import TicketFilterForm, TicketForm


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page with unit type selection."""

    template_name = "tickets/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count tickets by status
        context["pending_count"] = TicketModel.objects.filter(
            status=TicketModel.Status.PENDING
        ).count()
        context["completed_count"] = TicketModel.objects.filter(
            status=TicketModel.Status.COMPLETED
        ).count()
        context["total_count"] = TicketModel.objects.count()
        return context


class TicketListView(LoginRequiredMixin, ListView):
    """List all tickets with filtering."""

    model = TicketModel
    template_name = "tickets/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 20

    def get_queryset(self):
        """Filter tickets based on query parameters."""
        queryset = TicketModel.objects.select_related(
            "maintenance_unit", "gop", "supervisor", "failure_type"
        ).order_by("-date", "-created_at")

        # Get unit type filter from URL
        unit_type = self.kwargs.get("unit_type")
        if unit_type:
            queryset = queryset.filter(maintenance_unit__unit_type=unit_type)

        # Apply form filters
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        entry_type = self.request.GET.get("entry_type")
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)

        gop = self.request.GET.get("gop")
        if gop:
            queryset = queryset.filter(gop_id=gop)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(ticket_number__icontains=search)
                | Q(reported_failure__icontains=search)
                | Q(maintenance_unit__number__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = TicketFilterForm(self.request.GET)
        context["unit_type"] = self.kwargs.get("unit_type")
        context["unit_type_display"] = self._get_unit_type_display()
        return context

    def _get_unit_type_display(self):
        """Get display name for unit type."""
        unit_type = self.kwargs.get("unit_type")
        if unit_type == "locomotora":
            return "Locomotoras"
        elif unit_type == "coche_remolcado":
            return "Coches Remolcados"
        elif unit_type == "coche_motor":
            return "Coches Motor"
        return "Todas las Unidades"


class TicketDetailView(LoginRequiredMixin, DetailView):
    """View ticket details."""

    model = TicketModel
    template_name = "tickets/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        return TicketModel.objects.select_related(
            "maintenance_unit",
            "gop",
            "supervisor",
            "train_number",
            "failure_type",
            "affected_system",
        )


class TicketCreateView(LoginRequiredMixin, CreateView):
    """Create a new ticket."""

    model = TicketModel
    form_class = TicketForm
    template_name = "tickets/ticket_form.html"
    success_url = reverse_lazy("tickets:ticket_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass unit_type to form if specified in URL
        unit_type = self.kwargs.get("unit_type")
        if unit_type:
            kwargs["unit_type"] = unit_type
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Generate a new UUID for the ticket
        initial["id"] = uuid.uuid4()
        return initial

    def form_valid(self, form):
        # Set the UUID before saving
        form.instance.id = uuid.uuid4()
        messages.success(
            self.request,
            f"Ticket {form.instance.ticket_number} creado exitosamente.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Crear"
        context["unit_type"] = self.kwargs.get("unit_type")
        # Add supervisors and trains for datalist autocomplete
        context["supervisors"] = SupervisorModel.objects.filter(is_active=True)
        context["trains"] = TrainNumberModel.objects.filter(is_active=True)
        # Add failure types for JS auto-select
        context["failure_types"] = FailureTypeModel.objects.filter(is_active=True)
        return context

    def get_success_url(self):
        unit_type = self.kwargs.get("unit_type")
        if unit_type:
            return reverse_lazy(
                "tickets:ticket_list_by_type", kwargs={"unit_type": unit_type}
            )
        return reverse_lazy("tickets:ticket_list")


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing ticket."""

    model = TicketModel
    form_class = TicketForm
    template_name = "tickets/ticket_form.html"
    context_object_name = "ticket"

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Ticket {form.instance.ticket_number} actualizado exitosamente.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Editar"
        # Add supervisors and trains for datalist autocomplete
        context["supervisors"] = SupervisorModel.objects.filter(is_active=True)
        context["trains"] = TrainNumberModel.objects.filter(is_active=True)
        # Add failure types for JS auto-select
        context["failure_types"] = FailureTypeModel.objects.filter(is_active=True)
        return context

    def get_success_url(self):
        return reverse_lazy("tickets:ticket_detail", kwargs={"pk": self.object.pk})


class TicketDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a ticket."""

    model = TicketModel
    template_name = "tickets/ticket_confirm_delete.html"
    context_object_name = "ticket"
    success_url = reverse_lazy("tickets:ticket_list")

    def form_valid(self, form):
        ticket_number = self.object.ticket_number
        response = super().form_valid(form)
        messages.success(self.request, f"Ticket {ticket_number} eliminado.")
        return response
