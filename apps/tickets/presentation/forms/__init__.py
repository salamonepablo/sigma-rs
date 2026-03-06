"""Forms for the tickets presentation layer."""

from apps.tickets.presentation.forms.maintenance_entry_forms import MaintenanceEntryForm
from apps.tickets.presentation.forms.novedad_forms import (
    NovedadFilterForm,
    NovedadForm,
)
from apps.tickets.presentation.forms.ticket_forms import TicketFilterForm, TicketForm

__all__ = [
    "TicketForm",
    "TicketFilterForm",
    "NovedadForm",
    "NovedadFilterForm",
    "MaintenanceEntryForm",
]
