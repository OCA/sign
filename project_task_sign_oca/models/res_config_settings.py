# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    project_task_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.project_task_sign_oca_template_id",
        string="Project Task Sign Oca Template",
        readonly=False,
    )
