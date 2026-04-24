# Copyright 2023-2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, modules


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def sign_oca_request_user_count(self):
        requests = {}
        domain = [
            ("request_id.state", "=", "0_sent"),
            (
                "partner_id",
                "child_of",
                [self.env.user.partner_id.commercial_partner_id.id],
            ),
            ("signed_on", "=", False),
        ]
        signer_model = self.env["sign.oca.request.signer"]
        groups = signer_model._read_group(
            domain, groupby=["model"], aggregates=["__count"]
        )
        for model_value, _count in groups:
            group_domain = domain + [("model", "=", model_value)]
            if model_value:
                model = model_value
                Model = self.env[model].with_user(self.env.user)
                signers = signer_model.search(group_domain)
                if signers:
                    total_records = Model.with_context(active_test=False).search_count(
                        [("id", "in", signers.mapped("res_id"))]
                    )
                    if total_records > 0:
                        record = self.env[model]
                        model_id = (
                            self.env["ir.model"].sudo().search([("model", "=", model)])
                        )
                        requests[model] = {
                            "id": model_id.id,
                            "name": record._description,
                            "model": model,
                            "icon": modules.module.get_module_icon(
                                record._original_module
                            ),
                            "total_records": total_records,
                        }
            else:
                signers = signer_model.search(group_domain)
                requests["undefined"] = {
                    "id": False,
                    "name": self.env._("Undefined"),
                    "model": "sign.oca.request",
                    "icon": modules.module.get_module_icon("sign_oca"),
                    "total_records": len(signers),
                }
        return list(requests.values())
