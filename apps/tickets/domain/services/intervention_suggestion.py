"""Domain service for maintenance intervention suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class MaintenanceCycle:
    """Maintenance cycle data needed for suggestion logic."""

    intervention_code: str
    intervention_name: str
    trigger_type: str
    trigger_value: int
    trigger_unit: str


@dataclass(frozen=True)
class InterventionHistoryItem:
    """Historical intervention record."""

    intervention_code: str
    date_from: date
    date_until: date | None


@dataclass(frozen=True)
class UnitMaintenanceHistory:
    """Summary of unit's maintenance history for display."""

    last_rg_date: date | None
    last_rg_km_since: Decimal | None
    last_numeral_code: str | None
    last_numeral_date: date | None
    last_numeral_km_since: Decimal | None
    last_rp_code: str | None
    last_rp_date: date | None
    last_rp_km_since: Decimal | None
    last_abc_code: str | None
    last_abc_date: date | None
    last_abc_km_since: Decimal | None


def _normalize_code(value: str | None) -> str:
    return (value or "").strip().upper()


def _is_ckd(
    brand_code: str | None,
    model_code: str | None,
    brand_name: str | None = None,
    model_name: str | None = None,
    unit_number: str | None = None,
) -> bool:
    normalized_brand = _normalize_code(brand_code)
    normalized_model = _normalize_code(model_code)
    if normalized_brand == "CNR" and normalized_model.startswith("CKD"):
        return True
    brand_label = _normalize_code(brand_name)
    model_label = _normalize_code(model_name)
    unit_label = _normalize_code(unit_number)
    return ("CNR" in brand_label or "DALIAN" in brand_label) and (
        "CKD" in model_label or "CKD" in unit_label
    )


@dataclass(frozen=True)
class InterventionSuggestion:
    """Result of the intervention suggestion process."""

    status: str
    reason: str | None
    suggested_code: str | None
    suggested_name: str | None
    last_intervention_code: str | None
    last_intervention_date: date | None
    km_since_last: Decimal | None
    period_since_last: int | None


class InterventionPriorityResolver:
    """Resolve intervention priority list for a unit."""

    GM_LOCO = [
        "RG",
        "N11",
        "N10",
        "N9",
        "N8",
        "N7",
        "N6",
        "N5",
        "N4",
        "N3",
        "N2",
        "N1",
        "ABC",
        "AB",
        "A",
    ]
    CKD_LOCO = [
        "720K",
        "360K",
        "R6",
        "R5",
        "R4",
        "R3",
        "R2",
        "R1",
        "EX",
    ]
    CNR_COACH = [
        "A4",
        "A3",
        "A2",
        "A1",
        "SEM",
        "MEN",
    ]
    MATERFER_COACH = [
        "RG",
        "RP",
        "ABC",
        "AB",
        "A",
    ]
    NOHAB_MOTORCOACH = [
        "RG",
        "RP",
        "SEM",
        "MEN",
    ]
    WAGON = [
        "AL",
        "REV",
        "A",
        "B",
    ]

    def resolve(
        self,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        brand_name: str | None = None,
        model_name: str | None = None,
        unit_number: str | None = None,
    ) -> list[str]:
        """Return priority list for the unit.

        Args:
            unit_type: Unit type identifier.
            brand_code: Brand code from master data.
            model_code: Model code when applicable.

        Returns:
            Ordered list of intervention codes from higher to lower priority.
        """

        if not unit_type:
            return []

        normalized_brand = _normalize_code(brand_code)

        if unit_type == "locomotora":
            if _is_ckd(brand_code, model_code, brand_name, model_name, unit_number):
                return self.CKD_LOCO
            return self.GM_LOCO

        if unit_type == "coche_remolcado":
            if normalized_brand in {"CNR"}:
                return self.CNR_COACH
            if normalized_brand in {"MATERFER", "MTF"}:
                return self.MATERFER_COACH
            return self.MATERFER_COACH

        if unit_type == "coche_motor":
            if normalized_brand in {"NOHAB"}:
                return self.NOHAB_MOTORCOACH
            return self.NOHAB_MOTORCOACH

        if unit_type == "vagon":
            return self.WAGON

        return []


class InterventionSuggestionService:
    """Suggest interventions based on cycles and history."""

    def __init__(self, priority_resolver: InterventionPriorityResolver | None = None):
        self._priority_resolver = priority_resolver or InterventionPriorityResolver()

    def suggest(
        self,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        cycles: Iterable[MaintenanceCycle],
        trigger_type: str | None,
        trigger_value: Decimal | int | None,
        history: Iterable[InterventionHistoryItem],
        last_km_value: Decimal | None = None,
        current_km_value: Decimal | None = None,
        last_period_value: int | None = None,
        current_period_value: int | None = None,
        brand_name: str | None = None,
        model_name: str | None = None,
        unit_number: str | None = None,
    ) -> InterventionSuggestion:
        """Calculate a suggested intervention for a maintenance entry.

        Args:
            unit_type: Unit type identifier.
            brand_code: Brand code.
            model_code: Model code when applicable.
            cycles: Maintenance cycles applicable to the unit.
            trigger_type: Trigger type (km or time).
            trigger_value: Trigger value provided by user.
            history: Historical interventions for the unit.
            last_km_value: Kilometer value at last intervention.
            current_km_value: Current kilometer value.
            last_period_value: Period value at last intervention (months).
            current_period_value: Current period value (months).

        Returns:
            InterventionSuggestion with details for UI.
        """

        if not unit_type:
            return InterventionSuggestion(
                status="no_unit",
                reason="No unit type available",
                suggested_code=None,
                suggested_name=None,
                last_intervention_code=None,
                last_intervention_date=None,
                km_since_last=None,
                period_since_last=None,
            )

        if not trigger_type or trigger_value is None:
            return InterventionSuggestion(
                status="missing_trigger",
                reason="Missing trigger input",
                suggested_code=None,
                suggested_name=None,
                last_intervention_code=None,
                last_intervention_date=None,
                km_since_last=None,
                period_since_last=None,
            )

        cycle_list = [cycle for cycle in cycles if cycle.trigger_type == trigger_type]
        if not cycle_list:
            return InterventionSuggestion(
                status="no_cycles",
                reason="No cycles for trigger type",
                suggested_code=None,
                suggested_name=None,
                last_intervention_code=None,
                last_intervention_date=None,
                km_since_last=None,
                period_since_last=None,
            )

        cycle_list.sort(key=lambda item: item.trigger_value)
        candidate = None
        for cycle in cycle_list:
            if cycle.trigger_value <= trigger_value:
                candidate = cycle
        if candidate is None:
            candidate = cycle_list[0]
            status = "below_threshold"
        else:
            status = "ok"

        priority_list = self._priority_resolver.resolve(
            unit_type, brand_code, model_code, brand_name, model_name, unit_number
        )
        priority_index = {code: idx for idx, code in enumerate(priority_list)}
        eligible_codes = None
        if candidate.intervention_code in priority_index:
            candidate_index = priority_index[candidate.intervention_code]
            eligible_codes = {
                code for code, idx in priority_index.items() if idx <= candidate_index
            }

        last_intervention = None
        for item in sorted(history, key=lambda item: item.date_from, reverse=True):
            if eligible_codes is None or item.intervention_code in eligible_codes:
                last_intervention = item
                break

        km_since: Decimal | None = None
        period_since = None
        if last_km_value is not None and current_km_value is not None:
            km_since = max(current_km_value - last_km_value, Decimal("0"))
        if last_period_value is not None and current_period_value is not None:
            period_since = max(current_period_value - last_period_value, 0)

        return InterventionSuggestion(
            status=status,
            reason=None,
            suggested_code=candidate.intervention_code,
            suggested_name=candidate.intervention_name,
            last_intervention_code=last_intervention.intervention_code
            if last_intervention
            else None,
            last_intervention_date=last_intervention.date_from
            if last_intervention
            else None,
            km_since_last=km_since,
            period_since_last=period_since,
        )

    def get_maintenance_history(
        self,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        cycles: Iterable[MaintenanceCycle] | None,
        history: Iterable[InterventionHistoryItem],
        current_km_value: Decimal | None = None,
        current_period_value: int | None = None,
        entry_date: date | None = None,
        brand_name: str | None = None,
        model_name: str | None = None,
        unit_number: str | None = None,
    ) -> UnitMaintenanceHistory:
        """Extract key maintenance history items for display.

        Args:
            unit_type: Unit type identifier.
            brand_code: Brand code.
            model_code: Model code when applicable.
            history: Historical interventions for the unit.
            current_km_value: Current kilometer value.
            current_period_value: Current period value (months).
            entry_date: Date of entry for period calculations.

        Returns:
            UnitMaintenanceHistory with RG, numeral, and ABC info.
        """

        sorted_history = sorted(
            history, key=lambda item: item.date_until or item.date_from, reverse=True
        )

        cycle_codes = {
            _normalize_code(cycle.intervention_code) for cycle in (cycles or [])
        }

        normalized_brand = _normalize_code(brand_code)

        def fallback_secondary_codes() -> set[str]:
            if unit_type == "locomotora":
                if _is_ckd(brand_code, model_code, brand_name, model_name, unit_number):
                    return {"360K", "720K"}
                return {f"N{idx}" for idx in range(1, 12)}
            if unit_type == "coche_remolcado":
                if normalized_brand == "CNR":
                    return {"A1", "A2", "A3", "A4", "SEM", "MEN"}
                return {"RP"}
            if unit_type == "coche_motor":
                return {"RP"}
            if unit_type == "vagon":
                return {"AL", "REV", "A", "B"}
            return set()

        def fallback_tertiary_codes() -> set[str]:
            if unit_type == "locomotora":
                if _is_ckd(brand_code, model_code, brand_name, model_name, unit_number):
                    return {"R6"}
                return {"ABC"}
            if unit_type == "coche_remolcado" and normalized_brand in {
                "MATERFER",
                "MTF",
            }:
                return {"ABC"}
            return set()

        if unit_type == "locomotora":
            if _is_ckd(brand_code, model_code, brand_name, model_name, unit_number):
                secondary_codes = {code for code in cycle_codes if code.endswith("K")}
                tertiary_codes = {"R6"} if "R6" in cycle_codes else set()
            else:
                secondary_codes = {
                    code
                    for code in cycle_codes
                    if code.startswith("N") and code[1:].isdigit()
                }
                tertiary_codes = {"ABC"} if "ABC" in cycle_codes else set()
        elif unit_type == "coche_remolcado":
            if normalized_brand == "CNR":
                # CNR: three independent secondary slots shown separately in UI.
                # secondary → A3/A4 (highest), rp slot → A2, abc slot → A1.
                secondary_codes = cycle_codes.intersection({"A3", "A4"}) or {"A3", "A4"}
                tertiary_codes = set()
            else:
                secondary_codes = {"RP"} if "RP" in cycle_codes else set()
                tertiary_codes = {"ABC"} if "ABC" in cycle_codes else set()
        elif unit_type == "coche_motor":
            secondary_codes = {"RP"} if "RP" in cycle_codes else set()
            tertiary_codes = set()
        elif unit_type == "vagon":
            secondary_codes = cycle_codes.intersection({"AL", "REV", "A", "B"})
            tertiary_codes = set()
        else:
            secondary_codes = set()
            tertiary_codes = set()

        if not secondary_codes:
            secondary_codes = fallback_secondary_codes()
        if not tertiary_codes:
            tertiary_codes = fallback_tertiary_codes()

        is_cnr_coach = unit_type == "coche_remolcado" and normalized_brand == "CNR"

        # Pass 1: find last RG with no cutoff.
        last_rg_date = None
        for item in sorted_history:
            code = item.intervention_code.upper()
            if code == "RG":
                last_rg_date = item.date_until or item.date_from
                break

        # Pass 2: find last secondary (numeral / RP) only AFTER the last RG.
        # Inheritance rule: a higher-rank intervention resets all lower-rank ones,
        # so interventions on or before the RG date are considered superseded.
        # For CNR coaches: find A3/A4 only (A2 and A1 are independent slots).
        last_numeral_code = None
        last_numeral_date = None
        last_rp_code = None
        last_rp_date = None
        for item in sorted_history:
            code = item.intervention_code.upper()
            item_date = item.date_until or item.date_from
            if last_rg_date is not None and item_date <= last_rg_date:
                continue
            if last_numeral_date is None and code in secondary_codes:
                last_numeral_code = code
                last_numeral_date = item_date
            if not is_cnr_coach and last_rp_code is None and code == "RP":
                last_rp_code = code
                last_rp_date = item_date

        # Pass 3: tertiary or CNR A2/A1 slots.
        last_abc_code = None
        last_abc_date = None

        if is_cnr_coach:
            # CNR: A2 and A1 are each independent — both filtered only by last RG date,
            # not by each other. The rp slot carries A2, abc slot carries A1.
            for item in sorted_history:
                code = item.intervention_code.upper()
                item_date = item.date_until or item.date_from
                if last_rg_date is not None and item_date <= last_rg_date:
                    continue
                if last_rp_code is None and code == "A2":
                    last_rp_code = code
                    last_rp_date = item_date
                if last_abc_code is None and code == "A1":
                    last_abc_code = code
                    last_abc_date = item_date
                if last_rp_code and last_abc_code:
                    break
        else:
            # Standard: tertiary (ABC / R6 / …) only AFTER the last secondary
            # or, if no secondary exists after RG, after the last RG itself.
            abc_cutoff = last_numeral_date or last_rp_date or last_rg_date
            for item in sorted_history:
                code = item.intervention_code.upper()
                item_date = item.date_until or item.date_from
                if abc_cutoff is not None and item_date <= abc_cutoff:
                    continue
                if code in tertiary_codes:
                    last_abc_code = code
                    last_abc_date = item_date
                    break

        last_rg_km_since = None
        last_numeral_km_since = None
        last_rp_km_since = None
        last_abc_km_since = None

        if current_km_value is not None and entry_date is not None:
            if last_rg_date:
                last_rg_km_since = current_km_value
            if last_numeral_date:
                last_numeral_km_since = current_km_value
            if last_rp_date:
                last_rp_km_since = current_km_value
            if last_abc_date:
                last_abc_km_since = current_km_value

        return UnitMaintenanceHistory(
            last_rg_date=last_rg_date,
            last_rg_km_since=last_rg_km_since,
            last_numeral_code=last_numeral_code,
            last_numeral_date=last_numeral_date,
            last_numeral_km_since=last_numeral_km_since,
            last_rp_code=last_rp_code,
            last_rp_date=last_rp_date,
            last_rp_km_since=last_rp_km_since,
            last_abc_code=last_abc_code,
            last_abc_date=last_abc_date,
            last_abc_km_since=last_abc_km_since,
        )
