# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    survey_user_input_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        domain="[('model_id.model', '=', 'survey.user_input')]",
        string="Sign Oca Template",
    )
