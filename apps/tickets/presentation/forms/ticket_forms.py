"""Forms for Ticket CRUD operations."""

import uuid

from django import forms

from apps.tickets.models import (
    AffectedSystemModel,
    FailureTypeModel,
    GOPModel,
    MaintenanceUnitModel,
    PersonalModel,
    TicketModel,
    TrainNumberModel,
)


class TicketForm(forms.ModelForm):
    """Form for creating and editing tickets."""

    # Train number as text field for free input
    train_number_input = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Ej: 1234",
                "list": "train-list",
            }
        ),
        label="Número de Tren",
    )

    class Meta:
        model = TicketModel
        fields = [
            "date",
            "maintenance_unit",
            "gop",
            "entry_type",
            "status",
            "reported_failure",
            "affected_service",
            "failure_type",
            "affected_system",
            "interviniente",
            "work_order_number",
            "notification_time",
            "intervention_time",
            "delivery_time",
            "observations",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={"class": "form-control form-control-sm", "type": "date"}
            ),
            "maintenance_unit": forms.Select(
                attrs={"class": "form-select form-select-sm"}
            ),
            "gop": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "entry_type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "reported_failure": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 2,
                    "placeholder": "Descripción de la falla",
                }
            ),
            "affected_service": forms.Select(
                attrs={"class": "form-select form-select-sm"}
            ),
            "failure_type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "affected_system": forms.Select(
                attrs={"class": "form-select form-select-sm"}
            ),
            "interviniente": forms.Select(
                attrs={"class": "form-select form-select-sm"}
            ),
            "work_order_number": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": "123456",
                    "type": "number",
                }
            ),
            "notification_time": forms.TimeInput(
                attrs={"class": "form-control form-control-sm", "type": "time"}
            ),
            "intervention_time": forms.TimeInput(
                attrs={"class": "form-control form-control-sm", "type": "time"}
            ),
            "delivery_time": forms.TimeInput(
                attrs={"class": "form-control form-control-sm", "type": "time"}
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 2,
                    "placeholder": "Trabajo realizado / observaciones",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with filtered querysets."""
        # Get unit_type filter if provided
        unit_type = kwargs.pop("unit_type", None)
        super().__init__(*args, **kwargs)

        # Store unit_type for later use
        self._unit_type = unit_type

        # Filter maintenance units by type if specified
        if unit_type:
            self.fields[
                "maintenance_unit"
            ].queryset = MaintenanceUnitModel.objects.filter(
                unit_type=unit_type, is_active=True
            )
            # Filter intervinientes by sector matching unit_type
            self.fields["interviniente"].queryset = PersonalModel.objects.filter(
                sector=unit_type, is_active=True
            ).order_by("full_name")
        else:
            self.fields[
                "maintenance_unit"
            ].queryset = MaintenanceUnitModel.objects.filter(is_active=True)
            # Show all active intervinientes if no unit_type filter
            self.fields["interviniente"].queryset = PersonalModel.objects.filter(
                is_active=True
            ).order_by("full_name")

        # Filter active items only for all FK fields
        self.fields["gop"].queryset = GOPModel.objects.filter(is_active=True)
        self.fields["failure_type"].queryset = FailureTypeModel.objects.filter(
            is_active=True
        )
        self.fields["affected_system"].queryset = AffectedSystemModel.objects.filter(
            is_active=True
        )

        # Make optional fields not required
        self.fields["failure_type"].required = False
        self.fields["affected_system"].required = False
        self.fields["affected_service"].required = False
        self.fields["interviniente"].required = False
        self.fields["work_order_number"].required = False
        self.fields["notification_time"].required = False
        self.fields["intervention_time"].required = False
        self.fields["delivery_time"].required = False
        self.fields["observations"].required = False

        # Pre-populate text fields if editing existing ticket
        if self.instance and self.instance.pk:
            if self.instance.train_number:
                self.fields[
                    "train_number_input"
                ].initial = self.instance.train_number.number

    def save(self, commit=True):
        """Save the form, creating train_number if needed."""
        instance = super().save(commit=False)

        # Handle train number - create if doesn't exist
        train_number_input = self.cleaned_data.get("train_number_input", "").strip()
        if train_number_input:
            train, _ = TrainNumberModel.objects.get_or_create(
                number=train_number_input,
                defaults={"id": uuid.uuid4()},
            )
            instance.train_number = train
        else:
            instance.train_number = None

        if commit:
            instance.save()

        return instance


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
