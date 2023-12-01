# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from base64 import b64decode
from io import BytesIO

from PyPDF2 import PdfFileReader
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from odoo import models


class SignOcaRequestSigner(models.Model):

    _inherit = "sign.oca.request.signer"

    def _get_pdf_page_biometric(self, item, box):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(box.getWidth(), box.getHeight()))
        if not item.get("value") or not item["value"].get("svg"):
            return False
        drawing = svg2rlg(BytesIO(b64decode(item["value"]["svg"])))
        scaling_x = item["width"] / 100 * float(box.getWidth()) / drawing.width
        scaling_y = item["height"] / 100 * float(box.getHeight()) / drawing.height

        drawing.width = item["width"] / 100 * float(box.getWidth())
        drawing.height = item["height"] / 100 * float(box.getHeight())
        drawing.scale(scaling_x, scaling_y)

        drawing.drawOn(
            can,
            item["position_x"] / 100 * float(box.getWidth()),
            (100 - item["position_y"] - item["height"]) / 100 * float(box.getHeight()),
        )
        can.save()
        packet.seek(0)
        new_pdf = PdfFileReader(packet)
        return new_pdf.getPage(0)
