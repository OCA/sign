# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="crm_lead_id",
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
            [("crm_lead_id", "in", self.ids)],
            ["crm_lead_id"],
            ["crm_lead_id"],
        )
        mapped_data = {
            x["crm_lead_id"][0]: x["crm_lead_id_count"] for x in request_data
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
                "default_crm_lead_id": self.id,
                "search_default_crm_lead_id": self.id,
            }
        )
        result["context"] = ctx
        return result
