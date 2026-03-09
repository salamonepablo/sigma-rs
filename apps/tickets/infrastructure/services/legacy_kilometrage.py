"""Legacy kilometrage reader for compatibility with TXT exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class KilometrageRecord:
    """Kilometrage record for a unit at a given date."""

    unit_number: str
    record_date: date
    km_value: int


class LegacyKilometrageRepository:
    """Load kilometrage values from legacy TXT exports."""

    def __init__(self, base_path: Path | None = None):
        self._base_path = base_path or Path("context/db-legacy")
        self._cache: dict[str, list[KilometrageRecord]] = {}

    def get_km_at_or_before(self, unit_number: str, target_date: date) -> int | None:
        """Return kilometer value at or before a given date.

        Args:
            unit_number: Unit identifier.
            target_date: Cutoff date.

        Returns:
            Kilometer value if found, otherwise None.
        """

        records = self._get_records(unit_number)
        filtered = [r for r in records if r.record_date <= target_date]
        if not filtered:
            return None
        filtered.sort(key=lambda r: r.record_date)
        return filtered[-1].km_value

    def get_km_since(self, unit_number: str, from_date: date) -> int | None:
        """Return total kilometers since a given date.

        Sums all km values from the first record on or after from_date
        to the latest record.

        Args:
            unit_number: Unit identifier.
            from_date: Starting date (inclusive).

        Returns:
            Total kilometers accumulated since from_date, or None if no records.
        """

        records = self._get_records(unit_number)
        filtered = [r for r in records if r.record_date >= from_date]
        if not filtered:
            return None
        filtered.sort(key=lambda r: r.record_date)
        total_km = sum(r.km_value for r in filtered)
        return total_km

    def get_latest_km(self, unit_number: str) -> int | None:
        """Return latest kilometer value for a unit."""

        records = self._get_records(unit_number)
        if not records:
            return None
        records.sort(key=lambda r: r.record_date)
        return records[-1].km_value

    def _get_records(self, unit_number: str) -> list[KilometrageRecord]:
        unit_key = unit_number.strip().upper()
        if unit_key in self._cache:
            return self._cache[unit_key]

        records = []
        for file_name, unit_field in [
            ("KilometrajeLocs.txt", "Locs"),
            ("Kilometraje_CCRR.txt", "Coche"),
        ]:
            file_path = self._base_path / file_name
            if not file_path.exists():
                continue
            records.extend(self._read_file(file_path, unit_field, unit_key))

        self._cache[unit_key] = records
        return records

    def _read_file(
        self, file_path: Path, unit_field: str, unit_key: str
    ) -> list[KilometrageRecord]:
        records: list[KilometrageRecord] = []
        with open(file_path, encoding="latin-1") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw_unit = (row.get(unit_field) or "").strip().upper()
                if raw_unit != unit_key:
                    continue
                raw_date = (row.get("Fecha") or "").strip()
                raw_km = (row.get("Kms_diario") or "").strip()
                parsed_date = self._parse_date(raw_date)
                if not parsed_date:
                    continue
                try:
                    km_value = int(float(raw_km))
                except ValueError:
                    continue
                records.append(
                    KilometrageRecord(
                        unit_number=unit_key,
                        record_date=parsed_date,
                        km_value=km_value,
                    )
                )
        return records

    @staticmethod
    def _parse_date(value: str) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None
