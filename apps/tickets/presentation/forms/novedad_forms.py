"""Forms for the novedad CRUD screens."""

from __future__ import annotations

from typing import Optional

from django import forms

from apps.tickets.models import (
    IntervencionTipoModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
)


class NovedadForm(forms.ModelForm):
    """ModelForm used to create and edit novedad records."""

    unit_input = forms.CharField(
        label="Unidad",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Nro de unidad (ej: A904, U3001)",
                "autocomplete": "off",
                "list": "unit-list",
                "data-uppercase": "true",
                "style": "text-transform: uppercase;",
            }
        ),
    )
    intervencion_input = forms.CharField(
        label="Intervención",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Código intervención (ej: AL, RA)",
                "autocomplete": "off",
                "list": "intervencion-list",
                "data-uppercase": "true",
                "style": "text-transform: uppercase;",
            }
        ),
    )
    lugar_input = forms.CharField(
        label="Lugar",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Código de lugar (ej: PMRE, 120)",
                "autocomplete": "off",
                "list": "lugar-list",
                "data-uppercase": "true",
                "style": "text-transform: uppercase;",
            }
        ),
    )

    class Meta:
        model = NovedadModel
        fields = [
            "maintenance_unit",
            "fecha_desde",
            "fecha_hasta",
            "intervencion",
            "lugar",
            "observaciones",
            "observaciones_egreso",
        ]
        widgets = {
            "maintenance_unit": forms.HiddenInput(),
            "intervencion": forms.HiddenInput(),
            "lugar": forms.HiddenInput(),
            "fecha_desde": forms.DateInput(
                attrs={"class": "form-control form-control-sm", "type": "date"},
                format="%Y-%m-%d",
            ),
            "fecha_hasta": forms.DateInput(
                attrs={"class": "form-control form-control-sm", "type": "date"},
                format="%Y-%m-%d",
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 3,
                    "placeholder": "Motivo de ingreso, falla observada, etc.",
                }
            ),
            "observaciones_egreso": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 3,
                    "placeholder": "Trabajos realizados, nota de entrega, etc.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        unit_type = kwargs.pop("unit_type", None)
        super().__init__(*args, **kwargs)
        self.fields["observaciones"].required = False
        self.fields["observaciones_egreso"].required = False
        self.fields["maintenance_unit"].required = False
        self.fields["intervencion"].required = False
        self.fields["lugar"].required = False

        self.fields["maintenance_unit"].queryset = self._unit_queryset(unit_type)
        self.fields["intervencion"].queryset = IntervencionTipoModel.objects.filter(
            is_active=True
        ).order_by("codigo")
        self.fields["lugar"].queryset = LugarModel.objects.filter(
            is_active=True
        ).order_by("descripcion")

        # Pre-fill manual inputs when editing
        if self.instance and self.instance.pk:
            if self.instance.maintenance_unit:
                self.fields[
                    "unit_input"
                ].initial = self.instance.maintenance_unit.number
            elif self.instance.legacy_unit_code:
                self.fields["unit_input"].initial = self.instance.legacy_unit_code

            if self.instance.intervencion:
                self.fields[
                    "intervencion_input"
                ].initial = self.instance.intervencion.codigo
            elif self.instance.legacy_intervencion_codigo:
                self.fields[
                    "intervencion_input"
                ].initial = self.instance.legacy_intervencion_codigo

            if self.instance.lugar:
                self.fields["lugar_input"].initial = (
                    self.instance.lugar.short_desc or str(self.instance.lugar.codigo)
                )
            elif self.instance.legacy_lugar_codigo:
                self.fields["lugar_input"].initial = str(
                    self.instance.legacy_lugar_codigo
                )

        self._legacy_unit_code: str | None = None
        self._legacy_intervencion_codigo: str | None = None

    def _unit_queryset(self, unit_type: Optional[str]):
        queryset = MaintenanceUnitModel.objects.order_by("number")
        if not unit_type:
            return queryset
        if unit_type == MaintenanceUnitModel.UnitType.LOCOMOTIVE:
            return queryset.filter(
                unit_type__in=[
                    MaintenanceUnitModel.UnitType.LOCOMOTIVE,
                    MaintenanceUnitModel.UnitType.MOTORCOACH,
                ]
            )
        if unit_type == MaintenanceUnitModel.UnitType.WAGON:
            return queryset.filter(unit_type=unit_type)
        return queryset.filter(unit_type=unit_type)

    def clean(self):
        cleaned_data = super().clean()
        self._resolve_unit(cleaned_data)
        self._resolve_intervencion(cleaned_data)
        self._resolve_lugar(cleaned_data)

        fecha_desde = cleaned_data.get("fecha_desde")
        fecha_hasta = cleaned_data.get("fecha_hasta")
        if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
            self.add_error(
                "fecha_hasta",
                "La fecha hasta no puede ser anterior a la fecha desde.",
            )

        return cleaned_data

    def _resolve_unit(self, cleaned_data):
        unit_value = (self.cleaned_data.get("unit_input") or "").strip().upper()
        if not unit_value:
            self.add_error("unit_input", "Debe indicar una unidad o código.")
            return

        unit = MaintenanceUnitModel.objects.filter(number__iexact=unit_value).first()
        cleaned_data["maintenance_unit"] = unit
        self._legacy_unit_code = None if unit else unit_value

    def _resolve_intervencion(self, cleaned_data):
        interv_value = (
            (self.cleaned_data.get("intervencion_input") or "").strip().upper()
        )
        if not interv_value:
            self.add_error(
                "intervencion_input",
                "Debe indicar un código de intervención.",
            )
            return

        intervencion = IntervencionTipoModel.objects.filter(
            codigo__iexact=interv_value
        ).first()
        cleaned_data["intervencion"] = intervencion
        self._legacy_intervencion_codigo = None if intervencion else interv_value

    def _resolve_lugar(self, cleaned_data):
        lugar_value = (self.cleaned_data.get("lugar_input") or "").strip().upper()
        if not lugar_value:
            self.add_error("lugar_input", "Debe indicar un lugar.")
            return

        lugar = None
        if lugar_value.isdigit():
            lugar = LugarModel.objects.filter(codigo=int(lugar_value)).first()
        if not lugar:
            lugar = LugarModel.objects.filter(short_desc__iexact=lugar_value).first()
        if not lugar:
            lugar = LugarModel.objects.filter(descripcion__iexact=lugar_value).first()

        if not lugar:
            self.add_error(
                "lugar_input",
                "No se encontró un lugar con ese código. Actualice el maestro antes de continuar.",
            )
            return

        cleaned_data["lugar"] = lugar

    def save(self, commit: bool = True):
        instance = super().save(commit=False)

        if not instance.pk:
            instance.is_legacy = False

        if instance.maintenance_unit:
            instance.legacy_unit_code = instance.maintenance_unit.number
        else:
            instance.legacy_unit_code = self._legacy_unit_code

        if instance.intervencion:
            instance.legacy_intervencion_codigo = instance.intervencion.codigo
        else:
            instance.legacy_intervencion_codigo = self._legacy_intervencion_codigo

        if instance.lugar:
            instance.legacy_lugar_codigo = instance.lugar.codigo

        if commit:
            instance.save()

        return instance


class NovedadFilterForm(forms.Form):
    """Form used to filter novelty listings."""

    UNIT_CHOICES = [
        ("", "Todas las unidades"),
        (
            MaintenanceUnitModel.UnitType.LOCOMOTIVE,
            "Locomotoras",
        ),
        (MaintenanceUnitModel.UnitType.RAILCAR, "Coches Remolcados"),
        (MaintenanceUnitModel.UnitType.MOTORCOACH, "Coches Motor"),
        (MaintenanceUnitModel.UnitType.WAGON, "Vagones"),
    ]

    unit_type = forms.ChoiceField(
        choices=UNIT_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Tipo de unidad",
    )
    intervencion = forms.ModelChoiceField(
        queryset=IntervencionTipoModel.objects.filter(is_active=True).order_by(
            "codigo"
        ),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Intervención",
    )
    lugar = forms.ModelChoiceField(
        queryset=LugarModel.objects.filter(is_active=True).order_by("descripcion"),
        required=False,
        empty_label="Todos los lugares",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Lugar",
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
        label="Desde",
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
        label="Hasta",
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Unidad, código o texto",
            }
        ),
        label="Búsqueda",
    )
    include_alistamientos = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Incluir AL",
    )
