"""Views for the tickets presentation layer."""

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
    "TicketCreateView",
    "TicketDeleteView",
    "TicketDetailView",
    "TicketListView",
    "TicketUpdateView",
]
