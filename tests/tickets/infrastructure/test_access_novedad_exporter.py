"""Pruebas para el exportador de novedades a Access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from apps.tickets.infrastructure.services.access_novedad_exporter import (
    AccessNovedadExporter,
    ExportConfig,
    ExportResult,
)


@dataclass
class _DummyNovelty:
    maintenance_unit: object
    intervencion: object
    lugar: object
    fecha_desde: date
    fecha_hasta: date | None = None
    fecha_estimada: date | None = None
    observaciones: str | None = None
    legacy_unit_code: str | None = None
    legacy_intervencion_codigo: str | None = None
    legacy_lugar_codigo: int | None = None
    is_legacy: bool = False
    is_exported: bool = False
    legacy_id: int | None = None
    saved_update_fields: list[str] | None = None

    def save(self, update_fields: list[str]) -> None:
        self.saved_update_fields = update_fields


def _build_exporter() -> AccessNovedadExporter:
    return AccessNovedadExporter(
        config=ExportConfig(
            script_path=Path("scripts/export_to_access.ps1"),
            baselocs_path=Path("baseLocs.mdb"),
            baseccrr_path=Path("baseCCRR.mdb"),
        )
    )


def _patch_pending(monkeypatch, pending: list[_DummyNovelty]) -> None:
    from apps.tickets.infrastructure.models import novedad as novedad_module

    def _fake_filter(**kwargs):  # noqa: ARG001
        return pending

    monkeypatch.setattr(
        novedad_module.NovedadModel.objects,
        "filter",
        _fake_filter,
    )


def test_export_all_pending_existing_check_marks_exported_and_skips_insert(monkeypatch):
    exporter = _build_exporter()
    novelty = _DummyNovelty(
        maintenance_unit=type(
            "MU", (), {"number": "A100", "unit_type": "locomotora"}
        )(),
        intervencion=type("IT", (), {"codigo": "RA"})(),
        lugar=type("LG", (), {"codigo": 1})(),
        fecha_desde=date(2024, 1, 1),
    )
    _patch_pending(monkeypatch, [novelty])

    def _existing_check(**kwargs):  # noqa: ARG001
        return 777

    monkeypatch.setattr(exporter, "check_exists_in_access", _existing_check)

    def _should_not_insert(**kwargs):  # noqa: ARG001
        raise AssertionError("export_novedad no debe llamarse si CHECK encuentra ID")

    monkeypatch.setattr(exporter, "export_novedad", _should_not_insert)

    stats = exporter.export_all_pending()

    assert stats["exported"] == 0
    assert stats["skipped"] == 1
    assert stats["errors"] == 0
    assert novelty.is_exported is True
    assert novelty.legacy_id == 777
    assert novelty.saved_update_fields == ["is_exported", "legacy_id"]


def test_export_all_pending_normalizes_strings_before_check(monkeypatch):
    exporter = _build_exporter()
    novelty = _DummyNovelty(
        maintenance_unit=type(
            "MU", (), {"number": "  a100  ", "unit_type": "locomotora"}
        )(),
        intervencion=type("IT", (), {"codigo": "  ra  "})(),
        lugar=type("LG", (), {"codigo": 1})(),
        fecha_desde=date(2024, 1, 1),
    )
    _patch_pending(monkeypatch, [novelty])

    captured: dict[str, str] = {}

    def _capture_check(**kwargs):
        captured["unidad"] = kwargs["unidad"]
        captured["intervencion"] = kwargs["intervencion"]
        return None

    monkeypatch.setattr(exporter, "check_exists_in_access", _capture_check)

    def _successful_export(**kwargs):  # noqa: ARG001
        return ExportResult(success=True, legacy_id=55)

    monkeypatch.setattr(
        exporter,
        "export_novedad",
        _successful_export,
    )

    stats = exporter.export_all_pending()

    assert stats["exported"] == 1
    assert stats["errors"] == 0
    assert captured == {"unidad": "a100", "intervencion": "ra"}
