"""Repository for kilometrage records stored in the database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.tickets.infrastructure.models import KilometrageRecordModel


class KilometrageRepository:
    """Provide kilometrage lookups backed by the database."""

    def get_km_at_or_before(
        self, unit_number: str, target_date: date
    ) -> Decimal | None:
        """Return kilometer value at or before a given date.

        Args:
            unit_number: Unit identifier.
            target_date: Cutoff date.

        Returns:
            Kilometer value if found, otherwise None.
        """

        unit_key = unit_number.strip().upper()
        record = (
            KilometrageRecordModel.objects.filter(
                unit_number__iexact=unit_key,
                record_date__lte=target_date,
            )
            .order_by("-record_date")
            .first()
        )
        return record.km_value if record else None

    def get_km_since(self, unit_number: str, from_date: date) -> Decimal | None:
        """Return total kilometers since a given date.

        Sums all km values from the first record on or after from_date
        to the latest record.

        Args:
            unit_number: Unit identifier.
            from_date: Starting date (inclusive).

        Returns:
            Total kilometers accumulated since from_date, or None if no records.
        """

        unit_key = unit_number.strip().upper()
        result = KilometrageRecordModel.objects.filter(
            unit_number__iexact=unit_key,
            record_date__gte=from_date,
        ).aggregate(total=Sum("km_value"))
        return result["total"] if result["total"] is not None else None

    def get_latest_km(self, unit_number: str) -> Decimal | None:
        """Return latest kilometer value for a unit."""

        unit_key = unit_number.strip().upper()
        record = (
            KilometrageRecordModel.objects.filter(unit_number__iexact=unit_key)
            .order_by("-record_date")
            .first()
        )
        return record.km_value if record else None
