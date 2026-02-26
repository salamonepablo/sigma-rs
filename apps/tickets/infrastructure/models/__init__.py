"""Django models for the tickets infrastructure layer."""

# Base model
from apps.tickets.infrastructure.models.base import BaseModel

# Maintenance unit models
from apps.tickets.infrastructure.models.maintenance_unit import (
    LocomotiveModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    RailcarModel,
)

# Reference data models
from apps.tickets.infrastructure.models.reference import (
    AffectedSystemModel,
    BrandModel,
    FailureTypeModel,
    GOPModel,
    LocomotiveModelModel,
    PersonalModel,
    RailcarClassModel,
    SupervisorModel,
    TrainNumberModel,
)

# Ticket model
from apps.tickets.infrastructure.models.ticket import TicketModel

__all__ = [
    # Base
    "BaseModel",
    # Reference data
    "AffectedSystemModel",
    "BrandModel",
    "FailureTypeModel",
    "GOPModel",
    "LocomotiveModelModel",
    "PersonalModel",
    "RailcarClassModel",
    "SupervisorModel",
    "TrainNumberModel",
    # Maintenance units
    "LocomotiveModel",
    "MaintenanceUnitModel",
    "MotorcoachModel",
    "RailcarModel",
    # Ticket
    "TicketModel",
]
