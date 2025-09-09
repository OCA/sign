# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import models


class SignOcaTemplate(models.Model):
    _inherit = "sign.oca.template"

    def _prepare_sign_oca_request_vals_from_record(self, record):
        request_values = super()._prepare_sign_oca_request_vals_from_record(record)
        if record._name == "hr.personal.equipment.request":
            report = self.env["ir.actions.report"]._get_report_from_name(
                "hr_personal_equipment_request_sign_oca.ppe_sign_report_template"
            )
            pdf = report._render_qweb_pdf(report.report_name, res_ids=record.ids)[0]
            request_values.update({"data": base64.b64encode(pdf)})
        return request_values
