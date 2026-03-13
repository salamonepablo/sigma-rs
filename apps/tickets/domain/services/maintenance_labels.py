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


def resolve_maintenance_display_rules(
    unit_type: str | None,
    brand_code: str | None,
) -> MaintenanceDisplayRules:
    """Return display rules based on rolling stock type and brand."""
    if not unit_type or not brand_code:
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
        )

    brand = (brand_code or "").strip().upper()

    if unit_type == "locomotora":
        if brand.startswith("CKD") or brand == "CNR":
            return MaintenanceDisplayRules(
                history_label="Última Revisión (R1-R6)",
                km_label="KM Revisión:",
                use_rp_history=False,
                show_abc=True,
            )
        return MaintenanceDisplayRules(
            history_label="Última Numeral (N1-N11)",
            km_label="KM Numeral:",
            use_rp_history=False,
            show_abc=True,
        )

    if unit_type == "coche_remolcado":
        if brand in {"CNR"}:
            return MaintenanceDisplayRules(
                history_label="Última Revisión (A1-A4)",
                km_label="KM Revisión:",
                use_rp_history=False,
                show_abc=True,
            )
        if brand in {"MATERFER", "MTF"}:
            return MaintenanceDisplayRules(
                history_label="Última RP",
                km_label="KM RP:",
                use_rp_history=True,
                show_abc=True,
            )
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
        )

    if unit_type == "coche_motor":
        if brand in {"NOHAB"}:
            return MaintenanceDisplayRules(
                history_label="Última RP",
                km_label="KM RP:",
                use_rp_history=True,
                show_abc=False,
            )
        return MaintenanceDisplayRules(
            history_label="Última Intervención",
            km_label="KM Intervención:",
            use_rp_history=False,
            show_abc=True,
        )

    return MaintenanceDisplayRules(
        history_label="Última Intervención",
        km_label="KM Intervención:",
        use_rp_history=False,
        show_abc=True,
    )
