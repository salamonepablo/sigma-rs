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
    LocomotiveModel,
    LocomotiveModelModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    PersonalModel,
    RailcarClassModel,
    RailcarModel,
    SupervisorModel,
    TicketModel,
    TrainNumberModel,
)

__all__ = [
    "BaseModel",
    "AffectedSystemModel",
    "BrandModel",
    "FailureTypeModel",
    "GOPModel",
    "LocomotiveModel",
    "LocomotiveModelModel",
    "MaintenanceUnitModel",
    "MotorcoachModel",
    "PersonalModel",
    "RailcarClassModel",
    "RailcarModel",
    "SupervisorModel",
    "TicketModel",
    "TrainNumberModel",
]
