# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tools import misc

from odoo.addons.base.tests.common import BaseCommon


class TestCcRecipients(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = base64.b64encode(
            open(
                misc.file_path("sign_oca/tests/empty.pdf"),
                "rb",
            ).read()
        )
        cls.signer_partner = cls.env["res.partner"].create(
            {"name": "Test Signer", "email": "signer@example.com"}
        )
        cls.cc_partner_1 = cls.env["res.partner"].create(
            {"name": "CC Recipient 1", "email": "cc1@example.com"}
        )
        cls.cc_partner_2 = cls.env["res.partner"].create(
            {"name": "CC Recipient 2", "email": "cc2@example.com"}
        )
        cls.role_customer = cls.env.ref("sign_oca.sign_role_customer")

    def _create_request_with_cc(self, **kwargs):
        vals = {
            "data": self.data,
            "name": "Test Sign Request",
            "signer_ids": [
                (
                    0,
                    0,
                    {
                        "partner_id": self.signer_partner.id,
                        "role_id": self.role_customer.id,
                    },
                ),
            ],
            "cc_partner_ids": [(6, 0, [self.cc_partner_1.id])],
        }
        vals.update(kwargs)
        return self.env["sign.oca.request"].create(vals)

    def test_cc_notification_after_all_signed(self):
        """CC recipients notified with signed PDF after all signers complete."""
        request = self._create_request_with_cc()
        request.action_send()
        # Mark signer as signed
        request.signer_ids[0].signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.state, "2_signed")
        # Assert cc_notify log was created
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "cc_notify"),
            ]
        )
        self.assertEqual(len(log), 1)
        # Assert ir.attachment was created for the signed PDF
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "sign.oca.request"),
                ("res_id", "=", request.id),
            ],
            order="id desc",
            limit=1,
        )
        self.assertTrue(
            attachment, "Signed PDF attachment should be created for CC notification"
        )

    def test_cc_not_sent_before_complete(self):
        """CC notification should NOT be sent when not all signers have signed."""
        signer_partner_2 = self.env["res.partner"].create(
            {"name": "Signer Two", "email": "signer2@example.com"}
        )
        request = self._create_request_with_cc(
            signer_ids=[
                (
                    0,
                    0,
                    {
                        "partner_id": self.signer_partner.id,
                        "role_id": self.role_customer.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": signer_partner_2.id,
                        "role_id": self.role_customer.id,
                    },
                ),
            ],
        )
        request.action_send()
        # Mark only first signer as signed
        request.signer_ids[0].signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.state, "0_sent")
        # Assert NO cc_notify log exists
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "cc_notify"),
            ]
        )
        self.assertEqual(len(log), 0)

    def test_cc_with_no_recipients(self):
        """Request without CC recipients should complete without errors."""
        request = self._create_request_with_cc(
            cc_partner_ids=[(6, 0, [])],
        )
        request.action_send()
        # Mark signer as signed
        request.signer_ids[0].signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.state, "2_signed")
        # Assert NO cc_notify log (no error should occur)
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "cc_notify"),
            ]
        )
        self.assertEqual(len(log), 0)

    def test_cc_with_sequential_mode(self):
        """CC notification should be sent after all sequential signers complete."""
        signer_partner_2 = self.env["res.partner"].create(
            {"name": "Signer Two", "email": "signer2@example.com"}
        )
        request = self._create_request_with_cc(
            signing_mode="sequential",
            signer_ids=[
                (
                    0,
                    0,
                    {
                        "partner_id": self.signer_partner.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 10,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": signer_partner_2.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 20,
                    },
                ),
            ],
        )
        request.action_send()
        # Sign first signer (order 10)
        first_signer = request.signer_ids.filtered(lambda s: s.signing_order == 10)
        first_signer.signed_on = fields.Datetime.now()
        request._check_signed()
        # Should advance to step 2, not yet complete
        self.assertEqual(request.state, "0_sent")
        # Sign second signer (order 20)
        second_signer = request.signer_ids.filtered(lambda s: s.signing_order == 20)
        second_signer.signed_on = fields.Datetime.now()
        request._check_signed()
        # Now fully signed
        self.assertEqual(request.state, "2_signed")
        # Assert cc_notify log exists
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "cc_notify"),
            ]
        )
        self.assertEqual(len(log), 1)
