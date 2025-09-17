# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from io import BytesIO

from PyPDF2 import PdfFileReader
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from odoo import models
from odoo.tools import file_path

from .. import utils as fonts_utils


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request.signer"

    def _detect_arabic(self, text):
        """Return True if the text contains Arabic characters."""
        return any("\u0600" <= ch <= "\u06FF" for ch in text or "")

    def _get_font_for_text(self, text):
        """Return (font_name, processed_text, alignment)."""
        if not text:
            return None, None, TA_LEFT
        if self._detect_arabic(text):
            font_name = "Amiri"
            fonts_directory = file_path(
                os.path.join("sign_oca_font_support", "static", "fonts")
            )
            font_path = os.path.join(fonts_directory, "Amiri-Regular.ttf")
            fonts_utils.ensure_font_registered(font_name, font_path)
            return font_name, fonts_utils.prepare_text(text, is_arabic=True), TA_RIGHT
        # Default fallback
        return "Helvetica", text, TA_LEFT

    def _render_text_to_pdf(self, text, font_name, alignment, item, box):
        """Draw text into a PDF page and return the page object."""
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(box.getWidth(), box.getHeight()))
        style = ParagraphStyle(
            name="Custom",
            fontName=font_name,
            fontSize=12,
            leading=14,
            alignment=alignment,
        )
        par = Paragraph(text, style=style)
        par.wrap(
            item["width"] / 100 * float(box.getWidth()),
            item["height"] / 100 * float(box.getHeight()),
        )
        par.drawOn(
            can,
            item["position_x"] / 100 * float(box.getWidth()),
            (100 - item["position_y"] - item["height"]) / 100 * float(box.getHeight()),
        )
        can.save()
        packet.seek(0)
        return PdfFileReader(packet).getPage(0)

    def _get_pdf_page_text(self, item, box):
        """Override text rendering to support custom fonts."""
        if not item.get("value"):
            return super()._get_pdf_page_text(item, box)
        font_name, text, alignment = self._get_font_for_text(item["value"])
        if font_name and text:
            return self._render_text_to_pdf(text, font_name, alignment, item, box)
        return super()._get_pdf_page_text(item, box)
