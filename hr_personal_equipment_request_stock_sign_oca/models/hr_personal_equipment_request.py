from odoo import models


class HrPersonalEquipmentRequest(models.Model):
    _inherit = "hr.personal.equipment.request"

    def _needs_sign_request(self):
        needs_sign_request = super()._needs_sign_request()
        return needs_sign_request and any(
            equipment.is_ppe and equipment.state == "valid"
            for equipment in self.line_ids
        )
