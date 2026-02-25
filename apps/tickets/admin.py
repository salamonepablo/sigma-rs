"""Django admin configuration for the tickets app."""

from django.contrib import admin

from apps.tickets.models import (
    AffectedSystemModel,
    BrandModel,
    FailureTypeModel,
    GOPModel,
    LocomotiveModel,
    LocomotiveModelModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    RailcarClassModel,
    RailcarModel,
    SupervisorModel,
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

    list_display = ["name", "code", "brand", "is_active"]
    list_filter = ["brand", "is_active"]
    search_fields = ["name", "code"]
    ordering = ["brand", "name"]


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


@admin.register(SupervisorModel)
class SupervisorAdmin(admin.ModelAdmin):
    """Admin for Supervisor model."""

    list_display = ["name", "employee_number", "email", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "employee_number", "email"]
    ordering = ["name"]


@admin.register(TrainNumberModel)
class TrainNumberAdmin(admin.ModelAdmin):
    """Admin for TrainNumber model."""

    list_display = ["number", "route", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["number", "route", "description"]
    ordering = ["number"]


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
                    "supervisor",
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
