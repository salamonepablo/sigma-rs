from __future__ import annotations

from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    """Formulario de carga/edición de tickets."""

    class Meta:
        model = Ticket
        fields = ["titulo", "descripcion", "estado", "prioridad"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "prioridad": forms.Select(attrs={"class": "form-select"}),
        }
