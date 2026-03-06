"""PDF generator for maintenance entry documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class MaintenanceEntryPdfData:
    """Payload for PDF generation."""

    entry_number: str
    unit_label: str
    user_label: str
    intervention_label: str
    entry_datetime: datetime
    exit_datetime: str
    lugar_label: str
    trigger_label: str
    observations: str
    checklist_tasks: list[str]


class MaintenanceEntryPdfGenerator:
    """Generate maintenance entry PDFs."""

    def generate(self, data: MaintenanceEntryPdfData) -> bytes:
        """Generate PDF bytes for a maintenance entry.

        Args:
            data: PDF payload.

        Returns:
            Bytes of the PDF document.
        """

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdf.setTitle("Ingreso a Mantenimiento")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(2 * cm, height - 2 * cm, "Ingreso a Mantenimiento")

        pdf.setFont("Helvetica", 10)
        y = height - 3 * cm

        def draw_line(label: str, value: str):
            nonlocal y
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(2 * cm, y, label)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(6 * cm, y, value)
            y -= 0.6 * cm

        draw_line("Nro. Ingreso:", data.entry_number)
        draw_line("Unidad:", data.unit_label)
        draw_line("Usuario:", data.user_label)
        draw_line("Intervención:", data.intervention_label)
        draw_line("Lugar:", data.lugar_label)
        draw_line("Fecha ingreso:", data.entry_datetime.strftime("%d/%m/%Y %H:%M"))
        draw_line("Fecha egreso:", data.exit_datetime)
        draw_line("KM/Período:", data.trigger_label)

        y -= 0.4 * cm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Checklist de tareas")
        y -= 0.6 * cm

        pdf.setFont("Helvetica", 9)
        tasks = data.checklist_tasks or []
        if not tasks:
            tasks = ["(Sin tareas definidas)"]
        for idx, task in enumerate(tasks, start=1):
            line = f"{idx}. [ ] {task}"
            pdf.drawString(2 * cm, y, line)
            y -= 0.5 * cm
            if y < 3 * cm:
                pdf.showPage()
                y = height - 2 * cm
                pdf.setFont("Helvetica", 9)

        y -= 0.4 * cm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Observaciones")
        y -= 0.6 * cm

        pdf.setFont("Helvetica", 9)
        for line in (data.observations or "-").splitlines():
            pdf.drawString(2 * cm, y, line)
            y -= 0.5 * cm
            if y < 3 * cm:
                pdf.showPage()
                y = height - 2 * cm
                pdf.setFont("Helvetica", 9)

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()
