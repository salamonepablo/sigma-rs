from __future__ import annotations

from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["numero", "titulo", "estado", "prioridad", "creado_por", "fecha"]
    list_filter = ["estado", "prioridad"]
    search_fields = ["titulo", "descripcion"]
