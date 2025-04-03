# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    survey_user_input_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.survey_user_input_sign_oca_template_id",
        string="Sign Oca Template",
        readonly=False,
    )
