"""URL configuration for the tickets app."""

from django.urls import path

from apps.tickets.presentation.views import (
    HomeView,
    LoginView,
    LogoutView,
    TicketCreateView,
    TicketDeleteView,
    TicketDetailView,
    TicketListView,
    TicketUpdateView,
)

app_name = "tickets"

urlpatterns = [
    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Home
    path("", HomeView.as_view(), name="home"),
    # Ticket CRUD
    path("tickets/", TicketListView.as_view(), name="ticket_list"),
    path(
        "tickets/<str:unit_type>/",
        TicketListView.as_view(),
        name="ticket_list_by_type",
    ),
    path("tickets/create/", TicketCreateView.as_view(), name="ticket_create"),
    path(
        "tickets/<str:unit_type>/create/",
        TicketCreateView.as_view(),
        name="ticket_create_by_type",
    ),
    path("ticket/<uuid:pk>/", TicketDetailView.as_view(), name="ticket_detail"),
    path("ticket/<uuid:pk>/edit/", TicketUpdateView.as_view(), name="ticket_update"),
    path("ticket/<uuid:pk>/delete/", TicketDeleteView.as_view(), name="ticket_delete"),
]
