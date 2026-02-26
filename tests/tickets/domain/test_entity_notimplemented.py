"""Pruebas de igualdad NotImplemented en entidades de dominio."""

from datetime import date
from uuid import uuid4

import pytest

from apps.tickets.domain.entities.affected_system import AffectedSystem
from apps.tickets.domain.entities.brand import Brand
from apps.tickets.domain.entities.failure_type import FailureType
from apps.tickets.domain.entities.gop import GOP
from apps.tickets.domain.entities.locomotive import Locomotive
from apps.tickets.domain.entities.locomotive_model import LocomotiveModel
from apps.tickets.domain.entities.motorcoach import Motorcoach
from apps.tickets.domain.entities.personal import Personal, Sector
from apps.tickets.domain.entities.railcar import Railcar
from apps.tickets.domain.entities.railcar_class import RailcarClass
from apps.tickets.domain.entities.supervisor import Supervisor
from apps.tickets.domain.entities.ticket import Ticket
from apps.tickets.domain.entities.train_number import TrainNumber
from apps.tickets.domain.value_objects.ticket_enums import EntryType


@pytest.mark.parametrize(
    "entity_cls, kwargs",
    [
        (
            AffectedSystem,
            {
                "id": uuid4(),
                "name": "Motor",
                "code": "MOT",
                "failure_type_id": uuid4(),
            },
        ),
        (
            Brand,
            {
                "id": uuid4(),
                "name": "GM",
                "code": "GM",
            },
        ),
        (
            FailureType,
            {
                "id": uuid4(),
                "name": "Mecánicas",
                "code": "MEC",
            },
        ),
        (
            GOP,
            {
                "id": uuid4(),
                "name": "GOP 1",
                "code": "G1",
            },
        ),
        (
            LocomotiveModel,
            {
                "id": uuid4(),
                "name": "GT22",
                "code": "GT22",
                "brand_id": uuid4(),
            },
        ),
        (
            RailcarClass,
            {
                "id": uuid4(),
                "name": "CPA",
                "code": "CPA",
                "brand_id": uuid4(),
            },
        ),
        (
            Supervisor,
            {
                "id": uuid4(),
                "name": "Juan Pérez",
                "employee_number": "12345",
            },
        ),
        (
            TrainNumber,
            {
                "id": uuid4(),
                "number": "301",
            },
        ),
        (
            Personal,
            {
                "id": uuid4(),
                "legajo_sap": "100",
                "full_name": "Maria Gomez",
                "sector": Sector.LOCOMOTORAS,
            },
        ),
        (
            Locomotive,
            {
                "id": uuid4(),
                "number": "A900",
                "brand": "GM",
                "model": "GT22",
            },
        ),
        (
            Railcar,
            {
                "id": uuid4(),
                "number": "U3001",
                "brand": "Materfer",
                "coach_type": "U",
            },
        ),
        (
            Motorcoach,
            {
                "id": uuid4(),
                "number": "CM001",
                "brand": "CNR",
                "model": "CKD",
                "configuration": "CM-CM",
            },
        ),
        (
            Ticket,
            {
                "id": uuid4(),
                "ticket_number": "2024-999",
                "date": date.today(),
                "maintenance_unit_id": uuid4(),
                "gop_id": uuid4(),
                "entry_type": EntryType.IMMEDIATE,
                "reported_failure": "Falla",
            },
        ),
    ],
)
def test_entity_eq_returns_notimplemented(entity_cls, kwargs):
    """La comparación con otro tipo debe devolver NotImplemented."""
    instance = entity_cls(**kwargs)

    assert instance.__eq__("invalid") is NotImplemented
