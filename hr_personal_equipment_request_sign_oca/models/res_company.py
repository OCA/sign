from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    personal_equipment_request_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        domain="[('model_id.model', '=', 'hr.personal.equipment.request')]",
        string="Template for Personal Equipment Request Signature Request",
        help="If this template is set, "
        "Personal Equipment Requests automatically generate a Signature Request",
    )
