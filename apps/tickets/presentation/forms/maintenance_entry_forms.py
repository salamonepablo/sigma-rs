"""Forms for maintenance entry workflow."""

from __future__ import annotations

from django import forms
from django.utils import timezone

from apps.tickets.models import IntervencionTipoModel, LugarModel, MaintenanceEntryModel


class MaintenanceEntryForm(forms.Form):
    """Form to capture maintenance entry information."""

    entry_datetime = forms.DateTimeField(
        label="Fecha y hora de ingreso",
        widget=forms.DateTimeInput(
            attrs={"class": "form-control form-control-sm", "type": "datetime-local"}
        ),
    )
    trigger_km = forms.IntegerField(
        label="Kilometraje",
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "placeholder": "KM"}
        ),
    )
    trigger_months = forms.IntegerField(
        label="Período (meses)",
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "placeholder": "Meses"}
        ),
    )
    lugar = forms.ModelChoiceField(
        label="Lugar",
        queryset=LugarModel.objects.filter(is_active=True).order_by("descripcion"),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    selected_intervention = forms.ModelChoiceField(
        label="Intervención",
        required=False,
        queryset=IntervencionTipoModel.objects.filter(is_active=True).order_by(
            "codigo"
        ),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    checklist_tasks = forms.CharField(
        label="Checklist de tareas",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control form-control-sm", "rows": 4}
        ),
        help_text="Una tarea por línea",
    )
    observations = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control form-control-sm", "rows": 3}
        ),
    )

    def __init__(self, *args, **kwargs):
        suggested_code = kwargs.pop("suggested_code", None)
        super().__init__(*args, **kwargs)
        self._resolved_trigger_type = None
        self._resolved_trigger_value = None
        self._resolved_trigger_unit = None

        if not self.initial.get("entry_datetime"):
            self.initial["entry_datetime"] = timezone.now().strftime("%Y-%m-%dT%H:%M")

        if suggested_code:
            self.fields["selected_intervention"].initial = (
                IntervencionTipoModel.objects.filter(codigo__iexact=suggested_code)
                .values_list("pk", flat=True)
                .first()
            )

    def clean(self):
        cleaned_data = super().clean()
        km_value = cleaned_data.get("trigger_km")
        months_value = cleaned_data.get("trigger_months")

        if km_value and months_value:
            self.add_error(
                "trigger_months",
                "Debe informar solo kilometraje o período, no ambos.",
            )
            return cleaned_data

        if not km_value and not months_value:
            self.add_error(
                "trigger_km",
                "Debe informar kilometraje o período.",
            )
            return cleaned_data

        if km_value:
            self._resolved_trigger_type = MaintenanceEntryModel.TriggerType.KM
            self._resolved_trigger_value = km_value
            self._resolved_trigger_unit = MaintenanceEntryModel.TriggerUnit.KM
        else:
            self._resolved_trigger_type = MaintenanceEntryModel.TriggerType.TIME
            self._resolved_trigger_value = months_value
            self._resolved_trigger_unit = MaintenanceEntryModel.TriggerUnit.MONTH

        return cleaned_data

    @property
    def resolved_trigger_type(self) -> str | None:
        return self._resolved_trigger_type

    @property
    def resolved_trigger_value(self) -> int | None:
        return self._resolved_trigger_value

    @property
    def resolved_trigger_unit(self) -> str | None:
        return self._resolved_trigger_unit
