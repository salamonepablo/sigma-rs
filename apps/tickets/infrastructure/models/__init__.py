"""Django models for the tickets infrastructure layer."""

from apps.tickets.infrastructure.models.base import BaseModel
from apps.tickets.infrastructure.models.kilometrage import KilometrageRecordModel
from apps.tickets.infrastructure.models.mail_recipient import LugarEmailRecipientModel
from apps.tickets.infrastructure.models.maintenance_cycle import MaintenanceCycleModel
from apps.tickets.infrastructure.models.maintenance_entry import MaintenanceEntryModel
from apps.tickets.infrastructure.models.maintenance_unit import (
    LocomotiveModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    RailcarModel,
)
from apps.tickets.infrastructure.models.novedad import NovedadModel
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
from apps.tickets.infrastructure.models.ticket import TicketModel

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
    # Maintenance cycles and entries
    "MaintenanceCycleModel",
    "MaintenanceEntryModel",
    # Kilometrage
    "KilometrageRecordModel",
    # Mail recipients
    "LugarEmailRecipientModel",
    # Ticket
    "TicketModel",
    # Novedad
    "NovedadModel",
]
