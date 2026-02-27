"""Domain entities for the tickets application."""

# Maintenance units (rolling stock)
# Reference data entities
from apps.tickets.domain.entities.affected_system import AffectedSystem
from apps.tickets.domain.entities.brand import Brand
from apps.tickets.domain.entities.failure_type import FailureType
from apps.tickets.domain.entities.gop import GOP
from apps.tickets.domain.entities.locomotive import Locomotive
from apps.tickets.domain.entities.locomotive_model import LocomotiveModel
from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit
from apps.tickets.domain.entities.motorcoach import Motorcoach
from apps.tickets.domain.entities.personal import Personal
from apps.tickets.domain.entities.railcar import Railcar
from apps.tickets.domain.entities.railcar_class import RailcarClass

# Main entity
from apps.tickets.domain.entities.ticket import Ticket
from apps.tickets.domain.entities.train_number import TrainNumber

__all__ = [
    # Maintenance units
    "MaintenanceUnit",
    "Locomotive",
    "Motorcoach",
    "Railcar",
    # Reference data
    "AffectedSystem",
    "Brand",
    "FailureType",
    "GOP",
    "LocomotiveModel",
    "Personal",
    "RailcarClass",
    "TrainNumber",
    # Main entity
    "Ticket",
]
