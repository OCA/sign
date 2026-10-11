from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    personal_equipment_request_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.personal_equipment_request_sign_oca_template_id",
        readonly=False,
    )
