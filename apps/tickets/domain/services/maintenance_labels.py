"""Shared display rules for maintenance labels."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaintenanceDisplayRules:
    """Display labels and field selection for maintenance history."""

    history_label: str
    km_label: str
    use_rp_history: bool
    show_abc: bool
    abc_label: str
    abc_km_label: str
    # CNR coaches need 3 independent secondary rows (A3, A2, A1).
    # When True, the rp slot holds A2 and the abc slot holds A1.
    show_rp_as_secondary_2: bool = field(default=False)
    secondary_2_label: str = field(default="")
    secondary_2_km_label: str = field(default="")
    # When True, km_since fields are not available; display days elapsed instead.
    show_days_instead_of_km: bool = field(default=False)


def _is_ckd(
    brand_code: str | None,
    model_code: str | None,
    brand_name: str | None = None,
    model_name: str | None = None,
    unit_number: str | None = None,
) -> bool:
    normalized_brand = (brand_code or "").strip().upper()
    normalized_model = (model_code or "").strip().upper()
    if normalized_brand == "CNR" and normalized_model.startswith("CKD"):
        return True
    brand_label = (brand_name or "").strip().upper()
    model_label = (model_name or "").strip().upper()
    unit_label = (unit_number or "").strip().upper()
    return ("CNR" in brand_label or "DALIAN" in brand_label) and (
        "CKD" in model_label or "CKD" in unit_label
    )


def resolve_maintenance_display_rules(
    unit_type: str | None,
    brand_code: str | None,
    model_code: str | None = None,
    brand_name: str | None = None,
    model_name: str | None = None,
    unit_number: str | None = None,
) -> MaintenanceDisplayRules:
    """Return display rules based on rolling stock type and brand."""
    if not unit_type or not brand_code:
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
            abc_label="Última ABC",
            abc_km_label="KM ABC:",
        )

    brand = (brand_code or "").strip().upper()

    if unit_type == "locomotora":
        if _is_ckd(brand_code, model_code, brand_name, model_name, unit_number):
            return MaintenanceDisplayRules(
                history_label="Última Numeral (N1-N2)",
                km_label="KM Numeral:",
                use_rp_history=False,
                show_abc=True,
                abc_label="Última R6",
                abc_km_label="KM R6:",
            )
        return MaintenanceDisplayRules(
            history_label="Última Numeral (N1-N11)",
            km_label="KM Numeral:",
            use_rp_history=False,
            show_abc=True,
            abc_label="Última ABC",
            abc_km_label="KM ABC:",
        )

    if unit_type == "coche_remolcado":
        if brand in {"CNR"}:
            # CNR coaches show 3 independent rows: A3, A2, A1 (all after last RG/PS).
            # last_numeral → A3, last_rp → A2 (repurposed), last_abc → A1 (repurposed).
            return MaintenanceDisplayRules(
                history_label="Última A3",
                km_label="KM A3:",
                use_rp_history=False,
                show_abc=True,
                abc_label="Última A1",
                abc_km_label="KM A1:",
                show_rp_as_secondary_2=True,
                secondary_2_label="Última A2",
                secondary_2_km_label="KM A2:",
            )
        if brand in {"MATERFER", "MTF"}:
            return MaintenanceDisplayRules(
                history_label="Última RP",
                km_label="KM RP:",
                use_rp_history=True,
                show_abc=True,
                abc_label="Última ABC",
                abc_km_label="KM ABC:",
            )
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
            abc_label="Última ABC",
            abc_km_label="KM ABC:",
        )

    if unit_type == "coche_motor":
        if brand in {"NOHAB"}:
            return MaintenanceDisplayRules(
                history_label="Última RP",
                km_label="KM RP:",
                use_rp_history=True,
                show_abc=True,
                abc_label="Último MEN/SEM",
                abc_km_label="KM MEN/SEM:",
            )
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
            abc_label="Última ABC",
            abc_km_label="KM ABC:",
        )

    if unit_type == "vagon":
        return MaintenanceDisplayRules(
            history_label="Última B",
            km_label="Días desde B:",
            use_rp_history=False,
            show_abc=True,
            abc_label="Última A/REV/AL",
            abc_km_label="Días desde A/REV/AL:",
            show_days_instead_of_km=True,
        )

    return MaintenanceDisplayRules(
        history_label="Última Intervención",
        km_label="KM Intervención:",
        use_rp_history=False,
        show_abc=True,
        abc_label="Última ABC",
        abc_km_label="KM ABC:",
    )
