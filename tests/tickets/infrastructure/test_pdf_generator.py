"""Pruebas de infraestructura para generación de PDF."""

from datetime import datetime

from apps.tickets.infrastructure.services.pdf_generator import (
    MaintenanceEntryPdfData,
    MaintenanceEntryPdfGenerator,
)


class TestMaintenanceEntryPdfGenerator:
    """Pruebas de generación de PDF."""

    def test_generates_pdf_bytes(self):
        generator = MaintenanceEntryPdfGenerator()
        data = MaintenanceEntryPdfData(
            entry_number="1234",
            unit_label="A904",
            user_label="Usuario Test",
            intervention_label="A - Revision",
            entry_datetime=datetime(2026, 3, 6, 10, 0),
            exit_datetime="-",
            lugar_label="Remedios de Escalada",
            trigger_label="16000 km",
            observations="Observaciones",
            checklist_tasks=["Tarea 1", "Tarea 2"],
        )

        pdf_bytes = generator.generate(data)

        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 100
