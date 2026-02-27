"""Django admin configuration for the tickets app."""

from django.contrib import admin

from apps.tickets.models import (
    AffectedSystemModel,
    BrandModel,
    FailureTypeModel,
    GOPModel,
    IntervencionTipoModel,
    LocomotiveModel,
    LocomotiveModelModel,
    LugarModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    NovedadModel,
    PersonalModel,
    RailcarClassModel,
    RailcarModel,
    TicketModel,
    TrainNumberModel,
)

# =============================================================================
# Reference Data Admin
# =============================================================================


@admin.register(BrandModel)
class BrandAdmin(admin.ModelAdmin):
    """Admin for Brand model."""

    list_display = ["name", "code", "full_name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code", "full_name"]
    ordering = ["name"]


@admin.register(LocomotiveModelModel)
class LocomotiveModelAdmin(admin.ModelAdmin):
    """Admin for LocomotiveModel model."""

    list_display = ["name", "code", "brand", "is_active"]
    list_filter = ["brand", "is_active"]
    search_fields = ["name", "code"]
    ordering = ["brand", "name"]


@admin.register(RailcarClassModel)
class RailcarClassAdmin(admin.ModelAdmin):
    """Admin for RailcarClass model."""

    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["code"]


@admin.register(FailureTypeModel)
class FailureTypeAdmin(admin.ModelAdmin):
    """Admin for FailureType model."""

    list_display = ["name", "code", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(AffectedSystemModel)
class AffectedSystemAdmin(admin.ModelAdmin):
    """Admin for AffectedSystem model."""

    list_display = ["name", "code", "failure_type", "is_active"]
    list_filter = ["failure_type", "is_active"]
    search_fields = ["name", "code"]
    ordering = ["failure_type", "name"]


@admin.register(GOPModel)
class GOPAdmin(admin.ModelAdmin):
    """Admin for GOP model."""

    list_display = ["name", "code", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(PersonalModel)
class PersonalAdmin(admin.ModelAdmin):
    """Admin for Personal model."""

    list_display = ["full_name", "legajo_sap", "sector", "sector_simaf", "is_active"]
    list_filter = ["sector", "is_active"]
    search_fields = ["full_name", "legajo_sap", "cuit", "sector_simaf"]
    ordering = ["full_name"]


@admin.register(TrainNumberModel)
class TrainNumberAdmin(admin.ModelAdmin):
    """Admin for TrainNumber model."""

    list_display = ["number", "route", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["number", "route", "description"]
    ordering = ["number"]


@admin.register(LugarModel)
class LugarAdmin(admin.ModelAdmin):
    """Admin for Lugar model."""

    list_display = ["codigo", "descripcion", "short_desc", "tipo", "revision"]
    list_filter = ["tipo", "revision"]
    search_fields = ["codigo", "descripcion", "short_desc"]
    ordering = ["codigo"]


@admin.register(IntervencionTipoModel)
class IntervencionTipoAdmin(admin.ModelAdmin):
    """Admin for IntervencionTipo model."""

    list_display = ["codigo", "descripcion", "clase"]
    list_filter = ["clase"]
    search_fields = ["codigo", "descripcion"]
    ordering = ["codigo"]


# =============================================================================
# Maintenance Unit Admin
# =============================================================================


@admin.register(MaintenanceUnitModel)
class MaintenanceUnitAdmin(admin.ModelAdmin):
    """Admin for MaintenanceUnit model."""

    list_display = ["number", "unit_type", "is_active"]
    list_filter = ["unit_type", "is_active"]
    search_fields = ["number"]
    ordering = ["number"]


@admin.register(LocomotiveModel)
class LocomotiveAdmin(admin.ModelAdmin):
    """Admin for Locomotive model."""

    list_display = ["number", "brand", "model", "is_active"]
    list_filter = ["brand", "model", "maintenance_unit__is_active"]
    search_fields = ["maintenance_unit__number"]
    ordering = ["maintenance_unit__number"]

    def number(self, obj):
        return obj.maintenance_unit.number

    def is_active(self, obj):
        return obj.maintenance_unit.is_active

    number.short_description = "Número"
    is_active.boolean = True


@admin.register(RailcarModel)
class RailcarAdmin(admin.ModelAdmin):
    """Admin for Railcar model."""

    list_display = ["number", "brand", "railcar_class", "is_active"]
    list_filter = ["brand", "railcar_class", "maintenance_unit__is_active"]
    search_fields = ["maintenance_unit__number"]
    ordering = ["maintenance_unit__number"]

    def number(self, obj):
        return obj.maintenance_unit.number

    def is_active(self, obj):
        return obj.maintenance_unit.is_active

    number.short_description = "Número"
    is_active.boolean = True


@admin.register(MotorcoachModel)
class MotorcoachAdmin(admin.ModelAdmin):
    """Admin for Motorcoach model."""

    list_display = ["number", "brand", "configuration", "car_count", "is_active"]
    list_filter = ["brand", "configuration", "maintenance_unit__is_active"]
    search_fields = ["maintenance_unit__number"]
    ordering = ["maintenance_unit__number"]

    def number(self, obj):
        return obj.maintenance_unit.number

    def is_active(self, obj):
        return obj.maintenance_unit.is_active

    number.short_description = "Número"
    is_active.boolean = True


# =============================================================================
# Ticket Admin
# =============================================================================


@admin.register(TicketModel)
class TicketAdmin(admin.ModelAdmin):
    """Admin for Ticket model."""

    list_display = [
        "ticket_number",
        "date",
        "maintenance_unit",
        "gop",
        "interviniente",
        "entry_type",
        "status",
    ]
    list_filter = ["status", "entry_type", "gop", "date"]
    search_fields = [
        "ticket_number",
        "maintenance_unit__number",
        "reported_failure",
    ]
    date_hierarchy = "date"
    ordering = ["-date", "-created_at"]

    fieldsets = (
        (
            "Información Principal",
            {
                "fields": (
                    "ticket_number",
                    "date",
                    "maintenance_unit",
                    "gop",
                    "entry_type",
                    "status",
                )
            },
        ),
        (
            "Falla",
            {
                "fields": (
                    "reported_failure",
                    "affected_service",
                    "resolution",
                    "failure_type",
                    "affected_system",
                )
            },
        ),
        (
            "Detalles",
            {
                "fields": (
                    "train_number",
                    "interviniente",
                    "work_order_number",
                )
            },
        ),
        (
            "Tiempos",
            {
                "fields": (
                    "notification_time",
                    "intervention_time",
                    "delivery_time",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            "Observaciones",
            {
                "fields": ("observations",),
                "classes": ["collapse"],
            },
        ),
    )


# =============================================================================
# Novedad Admin
# =============================================================================


@admin.register(NovedadModel)
class NovedadAdmin(admin.ModelAdmin):
    """Admin for Novedad model."""

    list_display = [
        "maintenance_unit",
        "fecha_desde",
        "fecha_hasta",
        "intervencion",
        "lugar",
        "is_legacy",
    ]
    list_filter = [
        "is_legacy",
        "intervencion",
        "lugar",
        "maintenance_unit__unit_type",
    ]
    search_fields = [
        "maintenance_unit__number",
        "legacy_unit_code",
        "observaciones",
    ]
    date_hierarchy = "fecha_desde"
    ordering = ["-fecha_desde"]
    raw_id_fields = ["maintenance_unit", "intervencion", "lugar"]
