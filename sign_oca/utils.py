# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def ensure_font_registered(font_name, font_path):
    """
    Ensure a TTF/OTF font is registered in ReportLab.
    If already registered, does nothing.
    """
    try:
        pdfmetrics.getFont(font_name)
    except KeyError as err:
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font file not found: {font_path}") from err
        pdfmetrics.registerFont(TTFont(font_name, font_path))


def prepare_text(text, is_arabic=False):
    """
    Prepares text for ReportLab rendering.
    - If Arabic, reshapes + applies bidi.
    - Otherwise, leaves text as is.
    """
    if not text:
        return ""
    if is_arabic:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text
