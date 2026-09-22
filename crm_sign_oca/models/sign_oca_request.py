# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    # This field is required for the inverse of crm.lead.
    crm_lead_id = fields.Many2one(
        comodel_name="crm.lead",
        compute="_compute_crm_lead_id",
        string="CRM Lead",
        readonly=True,
        store=True,
    )

    @api.depends("record_ref")
    def _compute_crm_lead_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "crm.lead"
        ):
            item.crm_lead_id = item.record_ref.id
