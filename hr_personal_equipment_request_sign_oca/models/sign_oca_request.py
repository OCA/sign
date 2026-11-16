from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    personal_equipment_request_id = fields.Many2one(
        comodel_name="hr.personal.equipment.request",
        string="Personal Equipment Request",
        compute="_compute_personal_equipment_request_id",
        store=True,
    )

    ppe_employee_id = fields.Many2one(
        comodel_name="hr.employee",
        related="personal_equipment_request_id.employee_id",
        readonly=True,
        store=True,
    )

    @api.depends("record_ref")
    def _compute_personal_equipment_request_id(self):
        for item in self:
            if (
                item.record_ref
                and item.record_ref._name == "hr.personal.equipment.request"
            ):
                item.personal_equipment_request_id = item.record_ref.id
            else:
                item.personal_equipment_request_id = False
