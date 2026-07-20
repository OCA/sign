# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ppe_report_show_sn = fields.Boolean(
        related="company_id.ppe_report_show_sn",
        readonly=False,
    )
