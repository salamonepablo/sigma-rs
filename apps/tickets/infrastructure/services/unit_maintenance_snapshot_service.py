"""Service that computes and persists the km snapshot for a maintenance unit."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.tickets.domain.services.intervention_suggestion import (
    InterventionHistoryItem,
    InterventionSuggestionService,
    MaintenanceCycle,
)
from apps.tickets.infrastructure.models import (
    KilometrageRecordModel,
    MaintenanceCycleModel,
    MaintenanceUnitModel,
    NovedadModel,
    UnitMaintenanceSnapshotModel,
)

logger = logging.getLogger(__name__)


class UnitMaintenanceSnapshotService:
    """Compute and persist UnitMaintenanceSnapshotModel for a given unit.

    The snapshot replaces expensive SUM queries on the maintenance entry
    critical path with a single row lookup per unit.
    """

    def __init__(
        self,
        suggestion_service: InterventionSuggestionService | None = None,
    ) -> None:
        self._suggestion_service = suggestion_service or InterventionSuggestionService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_unit(
        self, maintenance_unit: MaintenanceUnitModel
    ) -> UnitMaintenanceSnapshotModel:
        """Compute and upsert the snapshot for a single unit.

        Args:
            maintenance_unit: The unit to refresh.

        Returns:
            The saved snapshot instance.
        """
        history_items = self._load_history(maintenance_unit)
        cycles = self._load_cycles(maintenance_unit)
        brand_code, model_code, brand_name, model_name = self._unit_labels(
            maintenance_unit
        )

        history = self._suggestion_service.get_maintenance_history(
            unit_type=maintenance_unit.unit_type,
            brand_code=brand_code,
            model_code=model_code,
            cycles=cycles,
            history=history_items,
            brand_name=brand_name,
            model_name=model_name,
            unit_number=maintenance_unit.number,
        )

        # If no RG exists in intervention history, fall back to the puesta en
        # servicio date derived from the first km record (units that started at 0 km,
        # e.g. CKD locos, CNR coaches).
        rg_date = history.last_rg_date or self._ps_date_from_km(maintenance_unit.number)

        km_rg = self._km_since(maintenance_unit.number, rg_date)
        km_numeral = self._km_since(maintenance_unit.number, history.last_numeral_date)
        km_rp = self._km_since(maintenance_unit.number, history.last_rp_date)
        km_abc = self._km_since(maintenance_unit.number, history.last_abc_date)

        snapshot, _ = UnitMaintenanceSnapshotModel.objects.update_or_create(
            maintenance_unit=maintenance_unit,
            defaults={
                "unit_number": maintenance_unit.number,
                "last_rg_date": rg_date,
                "km_since_rg": km_rg,
                "last_numeral_code": history.last_numeral_code,
                "last_numeral_date": history.last_numeral_date,
                "km_since_numeral": km_numeral,
                "last_rp_code": history.last_rp_code,
                "last_rp_date": history.last_rp_date,
                "km_since_rp": km_rp,
                "last_abc_code": history.last_abc_code,
                "last_abc_date": history.last_abc_date,
                "km_since_abc": km_abc,
            },
        )
        return snapshot

    def refresh_by_unit_number(
        self, unit_number: str
    ) -> UnitMaintenanceSnapshotModel | None:
        """Refresh snapshot for a unit identified by its number string.

        Returns None if the unit is not found.
        """
        mu = MaintenanceUnitModel.objects.filter(
            number__iexact=unit_number.strip()
        ).first()
        if not mu:
            logger.warning(
                "UnitMaintenanceSnapshotService: unit %s not found", unit_number
            )
            return None
        return self.refresh_unit(mu)

    def refresh_bulk(
        self,
        unit_numbers: list[str] | None = None,
        progress_callback=None,
    ) -> int:
        """Compute and persist snapshots for all units (or a subset).

        Args:
            unit_numbers: Optional list of unit numbers to restrict the refresh.
                          If None, all units with km records are processed.
            progress_callback: Optional callable(unit_number: str) called after
                               each unit is processed.

        Returns:
            Number of units processed.
        """
        qs = MaintenanceUnitModel.objects.all()
        if unit_numbers:
            qs = qs.filter(number__in=[u.strip().upper() for u in unit_numbers])

        count = 0
        for mu in qs.iterator():
            try:
                self.refresh_unit(mu)
                count += 1
                if progress_callback:
                    progress_callback(mu.number)
            except Exception:
                logger.exception("Failed to refresh snapshot for unit %s", mu.number)
        return count

    def get_snapshot(self, unit_number: str) -> UnitMaintenanceSnapshotModel | None:
        """Return the stored snapshot for a unit, or None if not computed yet."""
        return (
            UnitMaintenanceSnapshotModel.objects.filter(
                unit_number__iexact=unit_number.strip()
            )
            .select_related("maintenance_unit")
            .first()
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _km_since(unit_number: str, from_date: date | None) -> Decimal | None:
        """Sum km records from from_date (inclusive) to present."""
        if from_date is None:
            return None
        result = KilometrageRecordModel.objects.filter(
            unit_number__iexact=unit_number.strip(),
            record_date__gte=from_date,
        ).aggregate(total=Sum("km_value"))
        return result["total"]

    @staticmethod
    def _ps_date_from_km(unit_number: str) -> date | None:
        """Return the date of the earliest km record as a PS proxy."""
        record = (
            KilometrageRecordModel.objects.filter(
                unit_number__iexact=unit_number.strip()
            )
            .order_by("record_date")
            .first()
        )
        return record.record_date if record else None

    @staticmethod
    def _load_history(mu: MaintenanceUnitModel) -> list[InterventionHistoryItem]:
        items = (
            NovedadModel.objects.filter(
                maintenance_unit=mu,
                fecha_hasta__isnull=False,
            )
            .select_related("intervencion")
            .order_by("-fecha_desde")
        )
        result = []
        for item in items:
            code = item.intervencion.codigo if item.intervencion else None
            if code:
                result.append(
                    InterventionHistoryItem(
                        intervention_code=code,
                        date_from=item.fecha_desde,
                        date_until=item.fecha_hasta,
                    )
                )
        return result

    @staticmethod
    def _load_cycles(mu: MaintenanceUnitModel) -> list[MaintenanceCycle]:
        brand_code = None
        model_code = None
        if mu.unit_type == "locomotora" and hasattr(mu, "locomotive") and mu.locomotive:
            brand_code = mu.locomotive.brand.code if mu.locomotive.brand else None
            model_code = mu.locomotive.model.code if mu.locomotive.model else None
        elif (
            mu.unit_type == "coche_remolcado" and hasattr(mu, "railcar") and mu.railcar
        ):
            brand_code = mu.railcar.brand.code if mu.railcar.brand else None
        elif (
            mu.unit_type == "coche_motor"
            and hasattr(mu, "motorcoach")
            and mu.motorcoach
        ):
            brand_code = mu.motorcoach.brand.code if mu.motorcoach.brand else None
        elif mu.unit_type == "vagon" and hasattr(mu, "wagon") and mu.wagon:
            brand_code = mu.wagon.brand.code if mu.wagon.brand else None

        if not brand_code:
            return []

        qs = MaintenanceCycleModel.objects.filter(
            rolling_stock_type=mu.unit_type,
            brand__code__iexact=brand_code,
            is_active=True,
        )
        if model_code:
            model_qs = qs.filter(model__code__iexact=model_code)
            qs = model_qs if model_qs.exists() else qs.filter(model__isnull=True)
        else:
            qs = qs.filter(model__isnull=True)

        return [
            MaintenanceCycle(
                intervention_code=c.intervention_code,
                intervention_name=c.intervention_name,
                trigger_type=c.trigger_type,
                trigger_value=c.trigger_value,
                trigger_unit=c.trigger_unit,
            )
            for c in qs
        ]

    @staticmethod
    def _unit_labels(
        mu: MaintenanceUnitModel,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """Return (brand_code, model_code, brand_name, model_name)."""
        brand_code = brand_name = model_code = model_name = None
        if mu.unit_type == "locomotora" and hasattr(mu, "locomotive") and mu.locomotive:
            loco = mu.locomotive
            if loco.brand:
                brand_code = loco.brand.code
                brand_name = loco.brand.name
            if loco.model:
                model_code = loco.model.code
                model_name = loco.model.name
        elif (
            mu.unit_type == "coche_remolcado" and hasattr(mu, "railcar") and mu.railcar
        ):
            rc = mu.railcar
            if rc.brand:
                brand_code = rc.brand.code
                brand_name = rc.brand.name
        elif (
            mu.unit_type == "coche_motor"
            and hasattr(mu, "motorcoach")
            and mu.motorcoach
        ):
            mc = mu.motorcoach
            if mc.brand:
                brand_code = mc.brand.code
                brand_name = mc.brand.name
        elif mu.unit_type == "vagon" and hasattr(mu, "wagon") and mu.wagon:
            wg = mu.wagon
            if wg.brand:
                brand_code = wg.brand.code
                brand_name = wg.brand.name
        return brand_code, model_code, brand_name, model_name
