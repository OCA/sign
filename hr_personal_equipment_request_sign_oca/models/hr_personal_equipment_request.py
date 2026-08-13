from odoo import api, fields, models


class HrPersonalEquipmentRequest(models.Model):
    _inherit = "hr.personal.equipment.request"

    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="personal_equipment_request_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        store=True,
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        for item in self:
            item.sign_request_count = len(item.sign_request_ids)

    def action_view_sign_requests(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        return result

    def _needs_sign_request(self):
        """This Equipment Request has to generate a Signature Request."""
        self.ensure_one()
        return any(equipment.is_ppe for equipment in self.line_ids)

    def _generate_sign_oca_request(self):
        sign_request_obj = self.env["sign.oca.request"].sudo()
        for item in self:
            if item._needs_sign_request():
                company = item.employee_id.company_id
                sign_template = company.personal_equipment_request_sign_oca_template_id
                if sign_template:
                    sign_template = sign_template.sudo()
                    request = sign_request_obj.create(
                        sign_template._prepare_sign_oca_request_vals_from_record(item)
                    )
                    request.action_send()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._generate_sign_oca_request()
        return res

    def write(self, vals):
        if "employee_id" in vals:
            old_employees = {rec.id: rec.employee_id for rec in self}
        res = super().write(vals)
        if "employee_id" in vals:
            for rec in self:
                if rec.employee_id and rec.employee_id != old_employees.get(rec.id):
                    rec._generate_sign_oca_request()
        return res
