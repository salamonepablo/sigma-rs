"""Domain entities for the tickets application."""

# Maintenance units (rolling stock)
from apps.tickets.domain.entities.locomotive import Locomotive
from apps.tickets.domain.entities.maintenance_unit import MaintenanceUnit
from apps.tickets.domain.entities.motorcoach import Motorcoach
from apps.tickets.domain.entities.railcar import Railcar

# Reference data entities
from apps.tickets.domain.entities.affected_system import AffectedSystem
from apps.tickets.domain.entities.brand import Brand
from apps.tickets.domain.entities.failure_type import FailureType
from apps.tickets.domain.entities.gop import GOP
from apps.tickets.domain.entities.locomotive_model import LocomotiveModel
from apps.tickets.domain.entities.railcar_class import RailcarClass
from apps.tickets.domain.entities.supervisor import Supervisor
from apps.tickets.domain.entities.train_number import TrainNumber

# Main entity
from apps.tickets.domain.entities.ticket import Ticket

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
    "RailcarClass",
    "Supervisor",
    "TrainNumber",
    # Main entity
    "Ticket",
]
