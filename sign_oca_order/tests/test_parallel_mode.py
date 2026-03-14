# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tools import misc

from odoo.addons.base.tests.common import BaseCommon


class TestParallelMode(BaseCommon):
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
        cls.signer_partner_2 = cls.env["res.partner"].create(
            {"name": "Test Signer 2", "email": "signer2@example.com"}
        )
        cls.cc_partner = cls.env["res.partner"].create(
            {"name": "CC Recipient", "email": "cc@example.com"}
        )
        cls.role_customer = cls.env.ref("sign_oca.sign_role_customer")

    def _create_parallel_request(self, **kwargs):
        vals = {
            "data": self.data,
            "name": "Test Parallel Request",
            "signing_mode": "parallel",
            "signer_ids": [
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
                        "partner_id": self.signer_partner_2.id,
                        "role_id": self.role_customer.id,
                    },
                ),
            ],
        }
        vals.update(kwargs)
        return self.env["sign.oca.request"].create(vals)

    def test_parallel_mode_is_default(self):
        """Parallel should be the default signing mode."""
        request = self._create_parallel_request()
        self.assertEqual(request.signing_mode, "parallel")

    def test_parallel_all_signers_sent(self):
        """All signers should be 'sent' after sending in parallel mode."""
        request = self._create_parallel_request()
        request.action_send()
        for signer in request.signer_ids:
            self.assertEqual(
                signer.signer_state,
                "sent",
                "All signers should be in 'sent' state in parallel mode",
            )

    def test_parallel_resend_sends_all_unsigned(self):
        """Resend in parallel mode increments reminder_count."""
        request = self._create_parallel_request()
        request.action_send()
        # Mark first signer as signed
        request.signer_ids[0].signed_on = fields.Datetime.now()
        request.action_resend()
        self.assertEqual(request.reminder_count, 1)

    def test_parallel_with_cc(self):
        """CC notification should be sent after all parallel signers complete."""
        request = self._create_parallel_request(
            cc_partner_ids=[(6, 0, [self.cc_partner.id])],
        )
        request.action_send()
        # Sign both signers
        for signer in request.signer_ids:
            signer.signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.state, "2_signed")
        # Assert cc_notify log exists
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "cc_notify"),
            ]
        )
        self.assertEqual(len(log), 1)
