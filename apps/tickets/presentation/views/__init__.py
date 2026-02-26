"""Views for the tickets presentation layer."""

from apps.tickets.presentation.views.auth_views import LoginView, LogoutView
from apps.tickets.presentation.views.ticket_views import (
    HomeView,
    TicketCreateView,
    TicketDeleteView,
    TicketDetailView,
    TicketListView,
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
    "TicketUpdateView",
]
