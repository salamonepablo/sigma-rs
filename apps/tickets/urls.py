"""URL configuration for the tickets app."""

from django.urls import path

from apps.tickets.presentation.views import (
    HomeView,
    LoginView,
    LogoutView,
    MaintenanceEntryCreateView,
    NovedadCreateView,
    NovedadDeleteView,
    NovedadDetailView,
    NovedadListView,
    NovedadUpdateView,
    TicketCreateView,
    TicketDeleteView,
    TicketDetailView,
    TicketListView,
    TicketStatusUpdateView,
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
    path(
        "ticket/<uuid:pk>/status/",
        TicketStatusUpdateView.as_view(),
        name="ticket_status_update",
    ),
    # Novedad CRUD - General
    path("novedades/", NovedadListView.as_view(), name="novedad_list"),
    path("novedades/create/", NovedadCreateView.as_view(), name="novedad_create"),
    path(
        "novedades/<str:unit_type>/create/",
        NovedadCreateView.as_view(),
        name="novedad_create_by_type",
    ),
    path(
        "novedades/<str:unit_type>/",
        NovedadListView.as_view(),
        name="novedad_list_by_type",
    ),
    path("novedad/<uuid:pk>/", NovedadDetailView.as_view(), name="novedad_detail"),
    path(
        "novedad/<uuid:pk>/ingreso/",
        MaintenanceEntryCreateView.as_view(),
        name="maintenance_entry_create",
    ),
    path("novedad/<uuid:pk>/edit/", NovedadUpdateView.as_view(), name="novedad_update"),
    path(
        "novedad/<uuid:pk>/delete/",
        NovedadDeleteView.as_view(),
        name="novedad_delete",
    ),
    # Novedad CRUD - Separated by category
    path(
        "locomotoras/novedades/",
        NovedadListView.as_view(),
        name="novedad_list_locomotoras",
        kwargs={"category": "traccion"},
    ),
    path(
        "locomotoras/novedades/create/",
        NovedadCreateView.as_view(),
        name="novedad_create_locomotoras",
        kwargs={"category": "traccion"},
    ),
    path(
        "ccrr/novedades/",
        NovedadListView.as_view(),
        name="novedad_list_ccrr",
        kwargs={"category": "ccrr"},
    ),
    path(
        "ccrr/novedades/create/",
        NovedadCreateView.as_view(),
        name="novedad_create_ccrr",
        kwargs={"category": "ccrr"},
    ),
    # Tickets - Separated by category
    path(
        "locomotoras/tickets/",
        TicketListView.as_view(),
        name="ticket_list_locomotoras",
        kwargs={"category": "traccion"},
    ),
    path(
        "locomotoras/tickets/create/",
        TicketCreateView.as_view(),
        name="ticket_create_locomotoras",
        kwargs={"category": "traccion"},
    ),
    path(
        "ccrr/tickets/",
        TicketListView.as_view(),
        name="ticket_list_ccrr",
        kwargs={"category": "ccrr"},
    ),
    path(
        "ccrr/tickets/create/",
        TicketCreateView.as_view(),
        name="ticket_create_ccrr",
        kwargs={"category": "ccrr"},
    ),
]
