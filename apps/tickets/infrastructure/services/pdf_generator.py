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
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from apps.tickets.domain.services.maintenance_labels import (
    MaintenanceDisplayRules,
    resolve_maintenance_display_rules,
)


@dataclass(frozen=True)
class MaintenanceEntryPdfData:
    """Payload for PDF generation."""

    entry_number: str
    unit_label: str
    unit_type: str
    brand_label: str
    brand_code: str | None
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
    last_rp_code: str | None
    last_rp_date: str | None
    last_rp_km: str | None
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

        images_dir = os.path.join(settings.BASE_DIR, "static", "images")
        left_logo = os.path.join(images_dir, "Logo_TAO.jpg")
        right_logo = os.path.join(images_dir, "ARS_MP_Logo.png")

        max_width = 3 * cm
        max_height = 1.5 * cm
        logo_y = height - 2.5 * cm

        def draw_logo(path: str, x: float) -> None:
            if not os.path.exists(path):
                return
            with contextlib.suppress(Exception):
                image = ImageReader(path)
                original_width, original_height = image.getSize()
                ratio = min(
                    max_width / original_width,
                    max_height / original_height,
                )
                draw_width = original_width * ratio
                draw_height = original_height * ratio
                pdf.drawImage(
                    image,
                    x,
                    logo_y + (max_height - draw_height) / 2,
                    width=draw_width,
                    height=draw_height,
                    mask="auto",
                )

        draw_logo(left_logo, 2 * cm)
        draw_logo(right_logo, width - 2 * cm - max_width)

        # Título
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(6 * cm, height - 1.5 * cm, "Material Rodante")

        unit_type_title = self._get_unit_type_title(data.unit_type)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(6 * cm, height - 2 * cm, unit_type_title)

        # Unit number in blue next to title
        if data.unit_label:
            pdf.setFont("Helvetica-Bold", 14)
            pdf.setFillColor(colors.blue)
            pdf.drawString(12.2 * cm, height - 2 * cm, data.unit_label)
            pdf.setFillColor(colors.black)

        pdf.setFont("Helvetica", 10)
        y = height - 3 * cm
        display_rules = resolve_maintenance_display_rules(
            data.unit_type,
            data.brand_code,
        )

        def draw_line(label: str, value: str):
            nonlocal y
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(2 * cm, y, label)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(6 * cm, y, value)
            y -= 0.6 * cm

        draw_line("Nro. Ingreso:", data.entry_number)
        draw_line("Unidad:", data.unit_label)
        draw_line("Marca:", data.brand_label or "-")
        draw_line(
            self._get_model_detail_title(data.unit_type),
            data.model_label or "-",
        )
        draw_line("Intervención:", data.intervention_label)
        draw_line("Lugar:", data.lugar_label)
        draw_line("Fecha ingreso:", data.entry_datetime.strftime("%d/%m/%Y %H:%M"))
        draw_line("Fecha egreso:", data.exit_datetime)
        for km_label, km_value in self._km_lines(data, display_rules):
            draw_line(km_label, self._format_km_value(km_value))
        draw_line("Usuario:", data.user_label)

        y -= 0.4 * cm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Checklist de tareas")
        y -= 0.6 * cm

        font_name = "Helvetica"
        font_size = 9
        pdf.setFont(font_name, font_size)
        tasks = data.checklist_tasks or []
        if not tasks:
            tasks = ["(Sin tareas definidas)"]
        _, descent = pdfmetrics.getAscentDescent(font_name, font_size)
        checkbox_size = 0.35 * cm
        checkbox_gap = 0.6 * cm
        label_gap = 0.15 * cm
        task_gap = 0.4 * cm
        line_height = 0.6 * cm
        for idx, task in enumerate(tasks, start=1):
            start_x = 2 * cm
            index_text = f"{idx}."
            pdf.drawString(start_x, y, index_text)
            index_width = pdf.stringWidth(index_text, font_name, font_size)
            cursor_x = start_x + index_width + 0.2 * cm
            box_y = y + descent
            pdf.rect(cursor_x, box_y, checkbox_size, checkbox_size)
            cursor_x += checkbox_size + label_gap
            pdf.drawString(cursor_x, y, "R")
            cursor_x += pdf.stringWidth("R", font_name, font_size) + checkbox_gap
            pdf.rect(cursor_x, box_y, checkbox_size, checkbox_size)
            cursor_x += checkbox_size + label_gap
            pdf.drawString(cursor_x, y, "P")
            cursor_x += pdf.stringWidth("P", font_name, font_size) + task_gap
            pdf.drawString(cursor_x, y, task)
            y -= line_height
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

        if y < 3.6 * cm:
            pdf.showPage()
            y = height - 2 * cm
        signature_y = 3 * cm
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(
            2 * cm,
            signature_y + 0.4 * cm,
            "Firma / Aclaración / Leg.",
        )
        pdf.line(2 * cm, signature_y, width - 2 * cm, signature_y)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(2 * cm, 2 * cm, "Referencias: R = Realizado | P = Pendiente")

        pdf.save()
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _get_unit_type_title(unit_type: str | None) -> str:
        """Return the title for the unit type."""
        if unit_type == "locomotora":
            return "Ingreso de Locomotora: "
        if unit_type == "coche_remolcado":
            return "Ingreso de Coche Remolcado: "
        if unit_type == "coche_motor":
            return "Ingreso de Coche Motor: "
        return "Ingreso a Mantenimiento: "

    @staticmethod
    def _get_model_detail_title(unit_type: str | None) -> str:
        """Return label for model/class detail based on unit type."""
        if unit_type == "coche_remolcado":
            return "Clase:"
        return "Modelo:"

    @staticmethod
    def _format_km_value(value: str | None) -> str:
        """Return kilometrage value with unit or fallback marker."""
        if not value:
            return "-"
        return f"{value}"

    @staticmethod
    def _km_lines(
        data: MaintenanceEntryPdfData,
        display_rules: MaintenanceDisplayRules,
    ) -> list[tuple[str, str | None]]:
        """Return kilometrage lines based on rolling stock type and brand."""
        lines: list[tuple[str, str | None]] = [("KM RG:", data.last_rg_km)]

        _, _, second_km = MaintenanceEntryPdfGenerator._get_secondary_history(
            data,
            display_rules,
        )
        lines.append((display_rules.km_label, second_km))
        if display_rules.show_abc:
            lines.append(("KM ABC:", data.last_abc_km))
        return lines

    @staticmethod
    def _get_secondary_history(
        data: MaintenanceEntryPdfData,
        display_rules: MaintenanceDisplayRules,
    ) -> tuple[str | None, str | None, str | None]:
        """Return secondary maintenance record based on shared display rules."""
        if display_rules.use_rp_history:
            return data.last_rp_code, data.last_rp_date, data.last_rp_km
        return data.last_numeral_code, data.last_numeral_date, data.last_numeral_km
