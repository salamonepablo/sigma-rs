"""Django models for the tickets infrastructure layer."""

# Base model
from apps.tickets.infrastructure.models.base import BaseModel

# Reference data models
from apps.tickets.infrastructure.models.reference import (
    AffectedSystemModel,
    BrandModel,
    FailureTypeModel,
    GOPModel,
    LocomotiveModelModel,
    RailcarClassModel,
    SupervisorModel,
    TrainNumberModel,
)

# Maintenance unit models
from apps.tickets.infrastructure.models.maintenance_unit import (
    LocomotiveModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    RailcarModel,
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
