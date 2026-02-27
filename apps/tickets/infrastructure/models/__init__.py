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
    IntervencionTipoModel,
    LocomotiveModelModel,
    LugarModel,
    PersonalModel,
    RailcarClassModel,
    TrainNumberModel,
)

# Ticket model
from apps.tickets.infrastructure.models.ticket import TicketModel

# Novedad model
from apps.tickets.infrastructure.models.novedad import NovedadModel

__all__ = [
    # Base
    "BaseModel",
    # Reference data
    "AffectedSystemModel",
    "BrandModel",
    "FailureTypeModel",
    "GOPModel",
    "IntervencionTipoModel",
    "LocomotiveModelModel",
    "LugarModel",
    "PersonalModel",
    "RailcarClassModel",
    "TrainNumberModel",
    # Maintenance units
    "LocomotiveModel",
    "MaintenanceUnitModel",
    "MotorcoachModel",
    "RailcarModel",
    # Ticket
    "TicketModel",
    # Novedad
    "NovedadModel",
]
