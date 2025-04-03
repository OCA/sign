# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    # This field is stored as a help to filter by.
    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="survey_user_input_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        compute_sudo=True,
        store=True,
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        request_data = self.env["sign.oca.request"].read_group(
            [("survey_user_input_id", "in", self.ids)],
            ["survey_user_input_id"],
            ["survey_user_input_id"],
        )
        mapped_data = {
            x["survey_user_input_id"][0]: x["survey_user_input_id_count"]
            for x in request_data
        }
        for item in self:
            item.sign_request_count = mapped_data.get(item.id, 0)

    def action_view_sign_requests(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        ctx = dict(self.env.context)
        ctx.update(
            {
                "default_maintenance_equipment_id": self.id,
                "search_default_maintenance_equipment_id": self.id,
            }
        )
        result["context"] = ctx
        return result

    def _process_generate_sign_oca_request(self, data):
        """Generate request from template if owner has changed."""
        request_model = self.env["sign.oca.request"].sudo()
        for item in self.filtered("partner_id"):
            sign_template = (
                item.survey_id.user_id.company_id.survey_user_input_sign_oca_template_id
            )
            old_partner_id = data[item.id] if item.id in data else False
            if sign_template and item.partner_id != old_partner_id:
                # Apply sudo because the user who creates the record may not have
                # permissions on sign.oca.template
                sign_template = sign_template.sudo()
                request_model.create(
                    sign_template._prepare_sign_oca_request_vals_from_record(item)
                )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if any(item.partner_id for item in res):
            res._process_generate_sign_oca_request({})
        return res
