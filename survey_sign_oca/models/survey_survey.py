# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class Survey(models.Model):
    _inherit = "survey.survey"

    start_button_name = fields.Char("Survey Start Button Name", default="Start")
