# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    crm_lead_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        domain="[('model_id.model', '=', 'crm.lead')]",
        string="Sign Oca Template",
    )
