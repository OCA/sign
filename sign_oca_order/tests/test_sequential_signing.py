# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools import misc

from odoo.addons.base.tests.common import BaseCommon


class TestSequentialSigning(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = base64.b64encode(
            open(
                misc.file_path("sign_oca/tests/empty.pdf"),
                "rb",
            ).read()
        )
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Signer One", "email": "signer1@example.com"}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Signer Two", "email": "signer2@example.com"}
        )
        cls.partner_3 = cls.env["res.partner"].create(
            {"name": "Signer Three", "email": "signer3@example.com"}
        )
        cls.role_customer = cls.env.ref("sign_oca.sign_role_customer")

    def _create_sequential_request(self, **kwargs):
        """Create a sequential sign request with 3 signers at orders 10, 20, 30."""
        vals = {
            "data": self.data,
            "name": "Test Sequential",
            "signing_mode": "sequential",
            "signer_ids": [
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_1.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 10,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_2.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 20,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_3.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 30,
                    },
                ),
            ],
        }
        vals.update(kwargs)
        return self.env["sign.oca.request"].create(vals)

    def _get_signer_by_partner(self, request, partner):
        """Return the signer record matching the given partner."""
        return request.signer_ids.filtered(lambda s: s.partner_id == partner)

    def _get_signers_by_order(self, request, order):
        """Return signer records matching the given signing_order."""
        return request.signer_ids.filtered(lambda s: s.signing_order == order)

    # ----------------------------------------------------------------
    # 1. Send only activates the first step
    # ----------------------------------------------------------------

    def test_sequential_send_first_step_only(self):
        """Sending a sequential request should only activate the first step."""
        request = self._create_sequential_request()
        request.action_send()

        self.assertEqual(request.state, "0_sent")
        self.assertEqual(request.current_signing_order, 10)

        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_2 = self._get_signer_by_partner(request, self.partner_2)
        signer_3 = self._get_signer_by_partner(request, self.partner_3)

        self.assertEqual(signer_1.signer_state, "sent")
        self.assertEqual(signer_2.signer_state, "waiting")
        self.assertEqual(signer_3.signer_state, "waiting")
        self.assertTrue(request.sent_date)

    # ----------------------------------------------------------------
    # 2. Advance after first signer signs
    # ----------------------------------------------------------------

    def test_sequential_advance_after_signing(self):
        """After the first signer signs, the second step should activate."""
        request = self._create_sequential_request()
        request.action_send()

        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_1.signed_on = fields.Datetime.now()
        request._check_signed()

        self.assertEqual(request.current_signing_order, 20)

        signer_2 = self._get_signer_by_partner(request, self.partner_2)
        signer_3 = self._get_signer_by_partner(request, self.partner_3)

        self.assertEqual(signer_2.signer_state, "sent")
        self.assertEqual(signer_3.signer_state, "waiting")
        self.assertEqual(request.state, "0_sent")

    # ----------------------------------------------------------------
    # 3. Same order => parallel within the step
    # ----------------------------------------------------------------

    def test_sequential_same_order_parallel(self):
        """Signers with the same order should sign in parallel within a step."""
        request = self._create_sequential_request(
            signer_ids=[
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_1.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 10,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_2.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 10,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "partner_id": self.partner_3.id,
                        "role_id": self.role_customer.id,
                        "signing_order": 20,
                    },
                ),
            ],
        )
        request.action_send()

        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_2 = self._get_signer_by_partner(request, self.partner_2)
        signer_3 = self._get_signer_by_partner(request, self.partner_3)

        # Both order-10 signers should be sent
        self.assertEqual(signer_1.signer_state, "sent")
        self.assertEqual(signer_2.signer_state, "sent")
        self.assertEqual(signer_3.signer_state, "waiting")

        # Sign only partner_1
        signer_1.signed_on = fields.Datetime.now()
        request._check_signed()

        # partner_2 is still pending in the same step -- no advancement
        self.assertEqual(signer_2.signer_state, "sent")
        self.assertEqual(signer_3.signer_state, "waiting")
        self.assertEqual(request.current_signing_order, 10)

        # Now sign partner_2 as well
        signer_2.signed_on = fields.Datetime.now()
        request._check_signed()

        # Step should now advance to order 20
        self.assertEqual(signer_3.signer_state, "sent")
        self.assertEqual(request.current_signing_order, 20)

    # ----------------------------------------------------------------
    # 4. All signers complete => request fully signed
    # ----------------------------------------------------------------

    def test_sequential_all_signed_completes(self):
        """Signing all signers in order should mark the request as signed."""
        request = self._create_sequential_request()
        request.action_send()

        # Sign signer 1 (order 10)
        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_1.signed_on = fields.Datetime.now()
        request._check_signed()

        # Sign signer 2 (order 20)
        signer_2 = self._get_signer_by_partner(request, self.partner_2)
        signer_2.signed_on = fields.Datetime.now()
        request._check_signed()

        # Sign signer 3 (order 30)
        signer_3 = self._get_signer_by_partner(request, self.partner_3)
        signer_3.signed_on = fields.Datetime.now()
        request._check_signed()

        self.assertEqual(request.state, "2_signed")

    # ----------------------------------------------------------------
    # 5. Resend only targets current step
    # ----------------------------------------------------------------

    def test_sequential_resend_only_current(self):
        """Resend should only notify unsigned signers in the current step."""
        request = self._create_sequential_request()
        request.action_send()

        # Resend at step 1
        request.action_resend()
        self.assertEqual(request.reminder_count, 1)

        # Sign signer 1, advance to step 2
        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_1.signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.current_signing_order, 20)

        # Resend at step 2
        request.action_resend()
        self.assertEqual(request.reminder_count, 2)

    # ----------------------------------------------------------------
    # 6. Cron reminder respects sequential order
    # ----------------------------------------------------------------

    def test_sequential_cron_reminder_only_current(self):
        """Cron reminders should only target the current step's signers."""
        request = self._create_sequential_request(
            reminder_enabled=True,
            reminder_interval_days=1,
        )
        request.action_send()

        # Backdate sent_date so the reminder becomes due
        request.sent_date = fields.Datetime.now() - timedelta(days=2)
        request.invalidate_recordset()

        self.env["sign.oca.request"]._cron_send_reminders()

        self.assertEqual(request.reminder_count, 1)

    # ----------------------------------------------------------------
    # 7. Waiting signer cannot sign
    # ----------------------------------------------------------------

    def test_action_sign_blocks_waiting_signer(self):
        """A signer in 'waiting' state should be blocked from signing."""
        request = self._create_sequential_request()
        request.action_send()

        signer_2 = self._get_signer_by_partner(request, self.partner_2)
        self.assertEqual(signer_2.signer_state, "waiting")

        with self.assertRaises(UserError):
            signer_2.action_sign(
                items={},
                access_token=signer_2.access_token,
            )

    # ----------------------------------------------------------------
    # 8. Advancing step creates a log entry
    # ----------------------------------------------------------------

    def test_advance_step_logs_action(self):
        """Advancing to the next step should create an 'advance_step' log."""
        request = self._create_sequential_request()
        request.action_send()

        signer_1 = self._get_signer_by_partner(request, self.partner_1)
        signer_1.signed_on = fields.Datetime.now()
        request._check_signed()

        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "advance_step"),
            ]
        )
        self.assertEqual(len(log), 1)

    # ----------------------------------------------------------------
    # 9. Expiration works in sequential mode
    # ----------------------------------------------------------------

    def test_expiration_works_in_sequential_mode(self):
        """A sequential request past its validity date should be expired."""
        request = self._create_sequential_request(
            validity_date=fields.Date.context_today(self.env["sign.oca.request"])
            - timedelta(days=1),
        )
        request.action_send()

        self.env["sign.oca.request"]._cron_send_reminders()

        self.assertEqual(request.state, "3_cancel")
