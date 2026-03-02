"""Views for the tickets presentation layer."""

from apps.tickets.presentation.views.auth_views import LoginView, LogoutView
from apps.tickets.presentation.views.novedad_views import (
    NovedadCreateView,
    NovedadDeleteView,
    NovedadDetailView,
    NovedadListView,
    NovedadUpdateView,
)
from apps.tickets.presentation.views.ticket_views import (
    HomeView,
    TicketCreateView,
    TicketDeleteView,
    TicketDetailView,
    TicketListView,
    TicketStatusUpdateView,
    TicketUpdateView,
)

__all__ = [
    "HomeView",
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
    "NovedadUpdateView",
    "NovedadDeleteView",
]
