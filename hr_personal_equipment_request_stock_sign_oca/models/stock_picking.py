# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_personal_equipment_request_signature_request(self):
        """Create a Signature Request for `self`."""
        # Only ask for signature when equipment is requested, not returned
        return_pickings = self.filtered(
            lambda picking: any(
                move.origin_returned_move_id for move in picking.move_ids
            )
        )
        no_return_equipment_requests = (self - return_pickings).equipment_request_id
        if no_return_equipment_requests:
            no_return_equipment_requests._generate_sign_oca_request()

    def _action_done(self):
        res = super()._action_done()
        self._create_personal_equipment_request_signature_request()
        return res
