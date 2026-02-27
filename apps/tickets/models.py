"""Models module for Django app discovery.

This module re-exports all models from the infrastructure layer
so Django can find them for migrations and admin.
"""

from apps.tickets.infrastructure.models import (
    AffectedSystemModel,
    BaseModel,
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

__all__ = [
    "BaseModel",
    "AffectedSystemModel",
    "BrandModel",
    "FailureTypeModel",
    "GOPModel",
    "IntervencionTipoModel",
    "LocomotiveModel",
    "LocomotiveModelModel",
    "LugarModel",
    "MaintenanceUnitModel",
    "MotorcoachModel",
    "NovedadModel",
    "PersonalModel",
    "RailcarClassModel",
    "RailcarModel",
    "TicketModel",
    "TrainNumberModel",
]
