"""Shared display rules for maintenance labels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaintenanceDisplayRules:
    """Display labels and field selection for maintenance history."""

    history_label: str
    km_label: str
    use_rp_history: bool
    show_abc: bool
    abc_label: str
    abc_km_label: str


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
                history_label="Última Numeral (360K/720K)",
                km_label="KM Numeral:",
                use_rp_history=False,
                show_abc=True,
                abc_label="Última Revisión (R1-R6)",
                abc_km_label="KM Revisión:",
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
            return MaintenanceDisplayRules(
                history_label="Última Revisión (A1-A4/SEM/MEN)",
                km_label="KM Revisión:",
                use_rp_history=False,
                show_abc=False,
                abc_label="Última ABC",
                abc_km_label="KM ABC:",
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
                show_abc=False,
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

    if unit_type == "vagon":
        return MaintenanceDisplayRules(
            history_label="Última Revisión (AL/REV/A/B)",
            km_label="KM Revisión:",
            use_rp_history=False,
            show_abc=False,
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
