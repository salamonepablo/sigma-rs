from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.ticket_list, name="ticket_list"),
    path("ticket/nuevo/", views.ticket_create, name="ticket_create"),
    path("ticket/<int:pk>/editar/", views.ticket_edit, name="ticket_edit"),
    path("ticket/<int:pk>/eliminar/", views.ticket_delete, name="ticket_delete"),
]
