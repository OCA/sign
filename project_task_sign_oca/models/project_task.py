# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectTask(models.Model):

    _inherit = "project.task"

    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="task_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        compute_sudo=True,
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        for task in self:
            task.sign_request_count = len(task.sign_request_ids)

    def action_view_sign_requests(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        return result

    def _generate_sign_oca_request(self):
        sign_request_obj = self.env["sign.oca.request"].sudo()
        for task in self:
            sign_template = task.company_id.project_task_sign_oca_template_id
            if sign_template:
                sign_template = sign_template.sudo()
                request = sign_request_obj.create(
                    sign_template._prepare_sign_oca_request_vals_from_record(task)
                )
                request.action_send()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for task in res:
            if task.partner_id:
                task._generate_sign_oca_request()
        return res

    def write(self, vals):
        old_partner_id = self.partner_id
        new_partner_id = vals.get("partner_id")
        res = super().write(vals)
        if new_partner_id and new_partner_id != old_partner_id:
            self._generate_sign_oca_request()
        return res
