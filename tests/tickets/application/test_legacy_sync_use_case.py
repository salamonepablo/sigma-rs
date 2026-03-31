"""Pruebas del caso de uso de sincronizacion legacy."""

from pathlib import Path

import pytest
from django.test import override_settings

from apps.tickets.application.use_cases.legacy_sync_use_case import (
    LegacySyncUseCase,
    SyncStats,
)


class _DummyNovedadImporter:
    def import_detenciones(self, **kwargs):
        return SyncStats(
            processed=10, inserted=5, skipped_old=0, duplicates=1, invalid=0
        )

    def import_detenciones_ccrr(self, **kwargs):
        return SyncStats(
            processed=4, inserted=2, skipped_old=0, duplicates=0, invalid=1
        )


class _DummyKilometrageImporter:
    def import_all(self, **kwargs):
        return SyncStats(
            processed=8, inserted=6, skipped_old=2, duplicates=0, invalid=0
        )


class _FailingNovedadImporter:
    def import_detenciones(self, **kwargs):
        raise FileNotFoundError("missing")

    def import_detenciones_ccrr(self, **kwargs):
        raise AssertionError("should not be called")


class _CapturingNovedadImporter:
    def __init__(self):
        self.base_paths = []

    def import_detenciones(self, **kwargs):
        self.base_paths.append(kwargs.get("base_path"))
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )

    def import_detenciones_ccrr(self, **kwargs):
        self.base_paths.append(kwargs.get("base_path"))
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )


class _CapturingKilometrageImporter:
    def __init__(self):
        self.base_paths = []

    def import_all(self, **kwargs):
        self.base_paths.append(kwargs.get("base_path"))
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )


class _DefaultingNovedadImporter:
    DEFAULT_PATH = Path("context/db-legacy")

    def __init__(self):
        self.base_paths = []

    def import_detenciones(self, **kwargs):
        resolved_path = kwargs.get("base_path") or self.DEFAULT_PATH
        self.base_paths.append(resolved_path)
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )

    def import_detenciones_ccrr(self, **kwargs):
        resolved_path = kwargs.get("base_path") or self.DEFAULT_PATH
        self.base_paths.append(resolved_path)
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )


class _DefaultingKilometrageImporter:
    DEFAULT_PATH = Path("context/db-legacy")

    def __init__(self):
        self.base_paths = []

    def import_all(self, **kwargs):
        resolved_path = kwargs.get("base_path") or self.DEFAULT_PATH
        self.base_paths.append(resolved_path)
        return SyncStats(
            processed=0, inserted=0, skipped_old=0, duplicates=0, invalid=0
        )


@pytest.mark.django_db
def test_use_case_aggregates_stats(tmp_path):
    """Consolida estadisticas de novedades y kilometraje."""
    use_case = LegacySyncUseCase(
        novedad_importer=_DummyNovedadImporter(),
        kilometrage_importer=_DummyKilometrageImporter(),
    )

    result = use_case.run(base_path=Path(tmp_path))

    assert result.novedades.processed == 14
    assert result.novedades.inserted == 7
    assert result.novedades.duplicates == 1
    assert result.novedades.invalid == 1
    assert result.kilometrage.inserted == 6
    assert result.kilometrage.skipped_old == 2
    assert result.duration_seconds >= 0


@pytest.mark.django_db
def test_use_case_propagates_errors(tmp_path):
    """Propaga errores de importacion para informar el fallo."""
    use_case = LegacySyncUseCase(
        novedad_importer=_FailingNovedadImporter(),
        kilometrage_importer=_DummyKilometrageImporter(),
    )

    with pytest.raises(FileNotFoundError):
        use_case.run(base_path=Path(tmp_path))


@pytest.mark.django_db
def test_use_case_usa_legacy_data_path_por_default(tmp_path):
    """Usa LEGACY_DATA_PATH cuando no se provee base_path."""
    novedad_importer = _CapturingNovedadImporter()
    kilometrage_importer = _CapturingKilometrageImporter()
    use_case = LegacySyncUseCase(
        novedad_importer=novedad_importer,
        kilometrage_importer=kilometrage_importer,
    )

    with override_settings(LEGACY_DATA_PATH=str(tmp_path)):
        use_case.run(base_path=None)

    assert novedad_importer.base_paths == [Path(tmp_path), Path(tmp_path)]
    assert kilometrage_importer.base_paths == [Path(tmp_path)]


@pytest.mark.django_db
def test_use_case_fallback_legacy_data_path_cuando_vacio():
    """Usa el path local por defecto si LEGACY_DATA_PATH esta vacio."""
    novedad_importer = _DefaultingNovedadImporter()
    kilometrage_importer = _DefaultingKilometrageImporter()
    use_case = LegacySyncUseCase(
        novedad_importer=novedad_importer,
        kilometrage_importer=kilometrage_importer,
    )

    with override_settings(LEGACY_DATA_PATH=""):
        use_case.run(base_path=None)

    assert novedad_importer.base_paths == [
        Path("context/db-legacy"),
        Path("context/db-legacy"),
    ]
    assert kilometrage_importer.base_paths == [Path("context/db-legacy")]
