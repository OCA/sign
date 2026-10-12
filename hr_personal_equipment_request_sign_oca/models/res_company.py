from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    personal_equipment_request_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        domain="[('model_id.model', '=', 'hr.personal.equipment.request')]",
        string="Personal Equipment Request Sign Oca Template",
    )
