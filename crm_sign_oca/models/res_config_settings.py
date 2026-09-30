# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crm_lead_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.crm_lead_sign_oca_template_id",
        string="Sign Oca Template",
        readonly=False,
    )
