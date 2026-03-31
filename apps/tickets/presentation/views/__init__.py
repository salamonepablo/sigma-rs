"""Views for the tickets presentation layer."""

from apps.tickets.presentation.views.auth_views import LoginView, LogoutView
from apps.tickets.presentation.views.novedad_actions import ResetIngresoView
from apps.tickets.presentation.views.novedad_views import (
    MaintenanceEntryCreateView,
    NovedadCreateView,
    NovedadDeleteView,
    NovedadDetailView,
    NovedadListView,
    NovedadSyncView,
    NovedadUpdateView,
)
from apps.tickets.presentation.views.ticket_views import (
    HomeView,
    LegacySyncView,
    TicketCreateView,
    TicketDeleteView,
    TicketDetailView,
    TicketListView,
    TicketStatusUpdateView,
    TicketUpdateView,
)

__all__ = [
    "HomeView",
    "LegacySyncView",
    "LoginView",
    "LogoutView",
    "TicketCreateView",
    "TicketDeleteView",
    "TicketDetailView",
    "TicketListView",
    "TicketStatusUpdateView",
    "TicketUpdateView",
    "NovedadListView",
    "NovedadDetailView",
    "NovedadCreateView",
    "MaintenanceEntryCreateView",
    "NovedadUpdateView",
    "NovedadDeleteView",
    "NovedadSyncView",
    "ResetIngresoView",
]
