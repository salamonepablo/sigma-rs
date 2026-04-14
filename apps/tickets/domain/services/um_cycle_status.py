"""Domain service for maintenance unit cycle status calculations."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class CycleDefinition:
    """Cycle metadata needed for status calculations."""

    cycle_id: str
    intervention_code: str
    intervention_name: str
    trigger_type: str
    trigger_value: int
    trigger_unit: str


@dataclass(frozen=True)
class CycleHistoryItem:
    """Minimal intervention history entry."""

    intervention_code: str
    date_from: date
    date_until: date | None


@dataclass(frozen=True)
class CycleStatusResult:
    """Calculated status for a maintenance cycle."""

    cycle_id: str
    name: str
    current_value: int | None
    target_value: int | None
    percentage: float | None
    status: str


@dataclass(frozen=True)
class NextInterventionEstimate:
    """Estimated next intervention for a unit."""

    cycle_id: str
    intervention_code: str
    intervention_name: str
    trigger_type: str
    trigger_value: int
    remaining_value: int | None
    remaining_unit: str | None
    estimated_date: date | None


@dataclass(frozen=True)
class FixedAverageConfig:
    """Fallback averages when no recent kilometrage is available."""

    gm_km: int
    ckd_km: int
    ccrr_materfer_km: int
    ccrr_cnr_apr_nov_km: int
    ccrr_cnr_dec_mar_km: int


class UmCycleStatusService:
    """Calculate cycle status and next intervention estimate."""

    def build_statuses(
        self,
        *,
        cycles: list[CycleDefinition],
        history: list[CycleHistoryItem],
        current_km: Decimal | None,
        current_date: date,
        avg_km_last_3_months: Decimal | None,
        avg_km_last_6_months: Decimal | None,
        fixed_average: FixedAverageConfig,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        km_at_dates: dict[date, Decimal | None],
    ) -> tuple[list[CycleStatusResult], NextInterventionEstimate | None]:
        """Build cycle statuses and the next intervention estimate."""

        average_km = self._resolve_average_km(
            avg_km_last_3_months,
            avg_km_last_6_months,
            fixed_average,
            unit_type,
            brand_code,
            model_code,
            current_date,
        )

        statuses: list[CycleStatusResult] = []
        next_candidates: list[NextInterventionEstimate] = []

        for cycle in cycles:
            last_date = self._last_intervention_date(history, cycle.intervention_code)
            current_value, target_value, percentage = self._calculate_progress(
                cycle,
                last_date,
                current_date,
                current_km,
                km_at_dates,
            )
            status = self._status_from_percentage(percentage, current_value)
            statuses.append(
                CycleStatusResult(
                    cycle_id=cycle.cycle_id,
                    name=cycle.intervention_name,
                    current_value=current_value,
                    target_value=target_value,
                    percentage=percentage,
                    status=status,
                )
            )

            estimate = self._estimate_next_intervention(
                cycle,
                last_date,
                current_date,
                current_value,
                average_km,
            )
            if estimate and estimate.estimated_date:
                next_candidates.append(estimate)

        next_intervention = None
        if next_candidates:
            next_intervention = min(
                next_candidates,
                key=lambda item: item.estimated_date or current_date,
            )

        return statuses, next_intervention

    @staticmethod
    def _last_intervention_date(
        history: list[CycleHistoryItem], code: str
    ) -> date | None:
        normalized = (code or "").strip().upper()
        for item in sorted(
            history,
            key=lambda entry: entry.date_until or entry.date_from,
            reverse=True,
        ):
            if item.intervention_code.strip().upper() == normalized:
                return item.date_until or item.date_from
        return None

    def _calculate_progress(
        self,
        cycle: CycleDefinition,
        last_date: date | None,
        current_date: date,
        current_km: Decimal | None,
        km_at_dates: dict[date, Decimal | None],
    ) -> tuple[int | None, int | None, float | None]:
        target_value = cycle.trigger_value
        if cycle.trigger_type == "time":
            if last_date is None:
                return None, target_value, None
            current_value = self._months_between(last_date, current_date)
            percentage = self._percentage(current_value, target_value)
            return current_value, target_value, percentage

        if cycle.trigger_type == "km":
            if last_date is None or current_km is None:
                return None, target_value, None
            last_km = km_at_dates.get(last_date)
            if last_km is None:
                return None, target_value, None
            current_value = max(int(current_km - last_km), 0)
            percentage = self._percentage(current_value, target_value)
            return current_value, target_value, percentage

        return None, target_value, None

    @staticmethod
    def _percentage(
        current_value: int | None, target_value: int | None
    ) -> float | None:
        if current_value is None or not target_value:
            return None
        return round((current_value / target_value) * 100, 2)

    @staticmethod
    def _status_from_percentage(
        percentage: float | None, current_value: int | None
    ) -> str:
        if current_value is None:
            return "sin_datos"
        if percentage is not None and percentage >= 100:
            return "vencido"
        return "en_curso"

    def _estimate_next_intervention(
        self,
        cycle: CycleDefinition,
        last_date: date | None,
        current_date: date,
        current_value: int | None,
        average_km: Decimal | None,
    ) -> NextInterventionEstimate | None:
        remaining_value = None
        estimated_date = None
        remaining_unit = None

        if cycle.trigger_type == "time":
            remaining_unit = "month"
            if last_date is not None:
                remaining_value = max(cycle.trigger_value - (current_value or 0), 0)
                estimated_date = self._add_months(last_date, cycle.trigger_value)

        if cycle.trigger_type == "km":
            remaining_unit = "km"
            if current_value is not None:
                remaining_value = max(cycle.trigger_value - current_value, 0)
                if remaining_value == 0:
                    estimated_date = current_date
                elif average_km and average_km > 0:
                    months_remaining = Decimal(remaining_value) / average_km
                    estimated_date = current_date + timedelta(
                        days=int(round(float(months_remaining) * 30))
                    )

        if remaining_value is None and estimated_date is None:
            return None

        return NextInterventionEstimate(
            cycle_id=cycle.cycle_id,
            intervention_code=cycle.intervention_code,
            intervention_name=cycle.intervention_name,
            trigger_type=cycle.trigger_type,
            trigger_value=cycle.trigger_value,
            remaining_value=remaining_value,
            remaining_unit=remaining_unit,
            estimated_date=estimated_date,
        )

    def _resolve_average_km(
        self,
        avg_km_last_3_months: Decimal | None,
        avg_km_last_6_months: Decimal | None,
        fixed_average: FixedAverageConfig,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        current_date: date,
    ) -> Decimal | None:
        if avg_km_last_3_months and avg_km_last_3_months > 0:
            return avg_km_last_3_months
        if avg_km_last_6_months and avg_km_last_6_months > 0:
            return avg_km_last_6_months
        return self._fixed_average(
            fixed_average,
            unit_type,
            brand_code,
            model_code,
            current_date,
        )

    @staticmethod
    def _fixed_average(
        fixed_average: FixedAverageConfig,
        unit_type: str | None,
        brand_code: str | None,
        model_code: str | None,
        current_date: date,
    ) -> Decimal | None:
        if not unit_type:
            return None

        normalized_brand = (brand_code or "").strip().upper()
        normalized_model = (model_code or "").strip().upper()

        if unit_type == "locomotora":
            if normalized_brand == "CNR" and normalized_model.startswith("CKD"):
                return Decimal(fixed_average.ckd_km)
            return Decimal(fixed_average.gm_km)

        if unit_type == "coche_remolcado":
            if normalized_brand in {"MATERFER", "MTF"}:
                return Decimal(fixed_average.ccrr_materfer_km)
            if normalized_brand == "CNR":
                if current_date.month in {12, 1, 2, 3}:
                    return Decimal(fixed_average.ccrr_cnr_dec_mar_km)
                return Decimal(fixed_average.ccrr_cnr_apr_nov_km)
            return Decimal(fixed_average.ccrr_materfer_km)

        return None

    @staticmethod
    def _months_between(start_date: date, end_date: date) -> int:
        if end_date < start_date:
            return 0
        return (end_date.year - start_date.year) * 12 + (
            end_date.month - start_date.month
        )

    @staticmethod
    def _add_months(source_date: date, months: int) -> date:
        month_index = source_date.month - 1 + months
        year = source_date.year + month_index // 12
        month = month_index % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
