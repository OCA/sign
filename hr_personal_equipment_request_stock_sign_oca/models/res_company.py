# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ppe_report_show_sn = fields.Boolean(
        string="Show S/N in Sign Request for PPE Request",
    )
