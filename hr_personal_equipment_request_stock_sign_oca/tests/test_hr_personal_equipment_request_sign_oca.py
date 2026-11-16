# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from .common import Common


class TestHrPersonalEquipmentRequestStockSignOca(Common):
    def test_personal_equipment_request_picking_done(self):
        """The Sign request is generated when the picking is done."""
        self.ppe_request.accept_request()
        for allocation in self.ppe_request.line_ids:
            allocation.move_ids[0].quantity_done = allocation.quantity
        self.ppe_request.picking_ids[0]._action_done()

        self.assertEqual(
            self.ppe_request.employee_id.user_partner_id,
            self.ppe_request.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(self.ppe_request.sign_request_count, 1)

    def test_personal_equipment_request_picking_cancel(self):
        """The Sign request is not generated when the picking is canceled."""
        self.ppe_request.accept_request()
        self.ppe_request.picking_ids[0].action_cancel()

        self.assertFalse(
            self.ppe_request.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(self.ppe_request.sign_request_count, 0)
