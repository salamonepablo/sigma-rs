"""PDF generator for maintenance entry documents."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class MaintenanceEntryPdfData:
    """Payload for PDF generation."""

    entry_number: str
    unit_label: str
    unit_type: str
    brand_label: str
    model_label: str
    user_label: str
    intervention_label: str
    entry_datetime: datetime
    exit_datetime: str
    lugar_label: str
    trigger_label: str
    observations: str
    checklist_tasks: list[str]
    # Historial
    last_rg_date: str | None
    last_rg_km: str | None
    last_numeral_code: str | None
    last_numeral_date: str | None
    last_numeral_km: str | None
    last_abc_date: str | None
    last_abc_km: str | None


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

        # Logo TA (izquierda)
        logo_path = os.path.join(
            settings.BASE_DIR, "static", "images", "Logo_TAO.png"
        )
        if os.path.exists(logo_path):
            with contextlib.suppress(Exception):
                pdf.drawImage(
                    logo_path,
                    2 * cm,
                    height - 2.5 * cm,
                    width=3 * cm,
                    height=1.5 * cm,
                    mask="auto",
                )

        # Título
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(6 * cm, height - 1.5 * cm, "Material Rodante")

        unit_type_title = self._get_unit_type_title(data.unit_type)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(6 * cm, height - 2 * cm, unit_type_title)

        # Unit number in blue next to title
        if data.unit_label:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColor(colors.blue)
            pdf.drawString(14 * cm, height - 2 * cm, data.unit_label)
            pdf.setFillColor(colors.black)

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
        draw_line("", data.trigger_label)

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

        # Segunda página: Historial
        pdf.showPage()
        y = height - 2 * cm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(2 * cm, y, "Historial de Mantenimiento")
        y -= 0.8 * cm

        # RG
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Última RG:")
        pdf.setFont("Helvetica", 10)
        if data.last_rg_date:
            pdf.drawString(6 * cm, y, f"{data.last_rg_date}")
            if data.last_rg_km:
                pdf.drawString(10 * cm, y, f"({data.last_rg_km} km)")
        else:
            pdf.drawString(6 * cm, y, "Sin registro")
        y -= 0.6 * cm

        # Numeral
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Última Intervención:")
        pdf.setFont("Helvetica", 10)
        if data.last_numeral_code:
            pdf.drawString(
                6 * cm, y, f"{data.last_numeral_code} ({data.last_numeral_date})"
            )
            if data.last_numeral_km:
                pdf.drawString(11 * cm, y, f"({data.last_numeral_km} km)")
        else:
            pdf.drawString(6 * cm, y, "Sin registro")
        y -= 0.6 * cm

        # ABC
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Última ABC:")
        pdf.setFont("Helvetica", 10)
        if data.last_abc_date:
            pdf.drawString(6 * cm, y, f"{data.last_abc_date}")
            if data.last_abc_km:
                pdf.drawString(10 * cm, y, f"({data.last_abc_km} km)")
        else:
            pdf.drawString(6 * cm, y, "Sin registro")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _get_unit_type_title(unit_type: str | None) -> str:
        """Return the title for the unit type."""
        if unit_type == "locomotora":
            return "Ingreso de Locomotora"
        if unit_type == "coche_remolcado":
            return "Ingreso de Coche Remolcado"
        if unit_type == "coche_motor":
            return "Ingreso de Coche Motor"
        return "Ingreso a Mantenimiento"
