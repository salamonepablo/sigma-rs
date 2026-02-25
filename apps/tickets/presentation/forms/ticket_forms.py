"""Forms for Ticket CRUD operations."""

from django import forms

from apps.tickets.models import (
    AffectedSystemModel,
    FailureTypeModel,
    GOPModel,
    MaintenanceUnitModel,
    SupervisorModel,
    TicketModel,
    TrainNumberModel,
)


class TicketForm(forms.ModelForm):
    """Form for creating and editing tickets."""

    class Meta:
        model = TicketModel
        fields = [
            "ticket_number",
            "date",
            "maintenance_unit",
            "gop",
            "entry_type",
            "status",
            "reported_failure",
            "train_number",
            "failure_type",
            "affected_system",
            "supervisor",
            "work_order_number",
            "notification_time",
            "intervention_time",
            "delivery_time",
            "observations",
        ]
        widgets = {
            "ticket_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: 2024-001"}
            ),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "maintenance_unit": forms.Select(attrs={"class": "form-select"}),
            "gop": forms.Select(attrs={"class": "form-select"}),
            "entry_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "reported_failure": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descripción de la falla reportada por el conductor",
                }
            ),
            "train_number": forms.Select(attrs={"class": "form-select"}),
            "failure_type": forms.Select(attrs={"class": "form-select"}),
            "affected_system": forms.Select(attrs={"class": "form-select"}),
            "supervisor": forms.Select(attrs={"class": "form-select"}),
            "work_order_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: OT-2024-100"}
            ),
            "notification_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "intervention_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "delivery_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Trabajo realizado / observaciones de la GOP",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with filtered querysets."""
        # Get unit_type filter if provided
        unit_type = kwargs.pop("unit_type", None)
        super().__init__(*args, **kwargs)

        # Filter maintenance units by type if specified
        if unit_type:
            self.fields["maintenance_unit"].queryset = (
                MaintenanceUnitModel.objects.filter(
                    unit_type=unit_type, is_active=True
                )
            )
        else:
            self.fields["maintenance_unit"].queryset = (
                MaintenanceUnitModel.objects.filter(is_active=True)
            )

        # Filter active items only for all FK fields
        self.fields["gop"].queryset = GOPModel.objects.filter(is_active=True)
        self.fields["supervisor"].queryset = SupervisorModel.objects.filter(
            is_active=True
        )
        self.fields["train_number"].queryset = TrainNumberModel.objects.filter(
            is_active=True
        )
        self.fields["failure_type"].queryset = FailureTypeModel.objects.filter(
            is_active=True
        )
        self.fields["affected_system"].queryset = AffectedSystemModel.objects.filter(
            is_active=True
        )

        # Make optional fields not required
        self.fields["train_number"].required = False
        self.fields["failure_type"].required = False
        self.fields["affected_system"].required = False
        self.fields["supervisor"].required = False
        self.fields["work_order_number"].required = False
        self.fields["notification_time"].required = False
        self.fields["intervention_time"].required = False
        self.fields["delivery_time"].required = False
        self.fields["observations"].required = False


class TicketFilterForm(forms.Form):
    """Form for filtering tickets in list view."""

    status = forms.ChoiceField(
        choices=[("", "Todos")] + list(TicketModel.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    entry_type = forms.ChoiceField(
        choices=[("", "Todos")] + list(TicketModel.EntryType.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    gop = forms.ModelChoiceField(
        queryset=GOPModel.objects.filter(is_active=True),
        required=False,
        empty_label="Todas las GOPs",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    )
