# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
import base64
from datetime import timedelta

from odoo import fields
from odoo.tools import misc

from odoo.addons.base.tests.common import BaseCommon


class TestSignOcaReminder(BaseCommon):
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
        cls.role_customer = cls.env.ref("sign_oca.sign_role_customer")

    def _create_request(self, **kwargs):
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
        }
        vals.update(kwargs)
        return self.env["sign.oca.request"].create(vals)

    # --- Default values from company ---

    def test_default_get_from_company(self):
        """Default values should come from company settings."""
        company = self.env.company
        company.write(
            {
                "sign_oca_reminder_enabled": True,
                "sign_oca_reminder_interval_days": 5,
                "sign_oca_validity_days": 30,
            }
        )
        request = self._create_request()
        self.assertTrue(request.reminder_enabled)
        self.assertEqual(request.reminder_interval_days, 5)
        expected_date = fields.Date.context_today(request) + timedelta(days=30)
        self.assertEqual(request.validity_date, expected_date)

    def test_default_get_no_validity(self):
        """When validity_days is 0, no expiration date should be set."""
        company = self.env.company
        company.write(
            {
                "sign_oca_reminder_enabled": False,
                "sign_oca_reminder_interval_days": 3,
                "sign_oca_validity_days": 0,
            }
        )
        request = self._create_request()
        self.assertFalse(request.reminder_enabled)
        self.assertEqual(request.reminder_interval_days, 3)
        self.assertFalse(request.validity_date)

    # --- Sent date ---

    def test_sent_date_recorded_on_send(self):
        """sent_date should be recorded when request is sent."""
        request = self._create_request()
        self.assertFalse(request.sent_date)
        request.action_send()
        self.assertEqual(request.state, "0_sent")
        self.assertTrue(request.sent_date)

    def test_sent_date_not_overwritten(self):
        """sent_date should not change if action_send is called again."""
        request = self._create_request()
        request.action_send()
        original_sent_date = request.sent_date
        # Calling again should not change sent_date (state is no longer draft)
        request.action_send()
        self.assertEqual(request.sent_date, original_sent_date)

    # --- Manual resend ---

    def test_resend_increments_count(self):
        """Manual resend should increment reminder_count."""
        request = self._create_request()
        request.action_send()
        self.assertEqual(request.reminder_count, 0)
        request.action_resend()
        self.assertEqual(request.reminder_count, 1)
        self.assertTrue(request.last_reminder_date)

    def test_resend_logs_action(self):
        """Manual resend should create a 'resend' log entry."""
        request = self._create_request()
        request.action_send()
        request.action_resend()
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "resend"),
            ]
        )
        self.assertEqual(len(log), 1)

    def test_resend_does_nothing_on_draft(self):
        """Resend should do nothing if request is still in draft."""
        request = self._create_request()
        request.action_resend()
        self.assertEqual(request.reminder_count, 0)
        self.assertFalse(request.last_reminder_date)

    def test_resend_skips_signed_signers(self):
        """Resend should only notify unsigned signers."""
        request = self._create_request(
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
                        "partner_id": self.signer_partner_2.id,
                        "role_id": self.role_customer.id,
                    },
                ),
            ],
        )
        request.action_send()
        # Mark first signer as signed
        request.signer_ids[0].signed_on = fields.Datetime.now()
        request.action_resend()
        # Should still work (one unsigned signer remains)
        self.assertEqual(request.reminder_count, 1)

    # --- Expiration ---

    def test_is_expired_computed(self):
        """is_expired should be True when validity_date is in the past."""
        request = self._create_request()
        request.validity_date = fields.Date.context_today(request) - timedelta(days=1)
        self.assertTrue(request.is_expired)

    def test_is_expired_false_for_future(self):
        """is_expired should be False when validity_date is in the future."""
        request = self._create_request()
        request.validity_date = fields.Date.context_today(request) + timedelta(days=10)
        self.assertFalse(request.is_expired)

    def test_is_expired_false_when_no_validity(self):
        """is_expired should be False when no validity_date is set."""
        request = self._create_request()
        request.validity_date = False
        self.assertFalse(request.is_expired)

    def test_cron_expires_overdue_requests(self):
        """Cron should cancel requests past their validity date."""
        request = self._create_request()
        request.action_send()
        request.validity_date = fields.Date.context_today(request) - timedelta(days=1)
        self.env["sign.oca.request"]._cron_send_reminders()
        self.assertEqual(request.state, "3_cancel")
        log = self.env["sign.oca.request.log"].search(
            [
                ("request_id", "=", request.id),
                ("action", "=", "expire"),
            ]
        )
        self.assertEqual(len(log), 1)

    def test_cron_does_not_expire_signed(self):
        """Cron should not expire already signed requests."""
        request = self._create_request()
        request.action_send()
        # Simulate signing
        request.state = "2_signed"
        request.validity_date = fields.Date.context_today(request) - timedelta(days=1)
        self.env["sign.oca.request"]._cron_send_reminders()
        # Should remain signed
        self.assertEqual(request.state, "2_signed")

    # --- Cron reminders ---

    def test_cron_sends_reminders_when_due(self):
        """Cron should send reminders for due requests."""
        request = self._create_request(
            reminder_enabled=True,
            reminder_interval_days=1,
        )
        request.action_send()
        # Backdate sent_date to make reminder due
        request.sent_date = fields.Datetime.now() - timedelta(days=2)
        # Force recompute of next_reminder_date
        request.invalidate_recordset()
        self.env["sign.oca.request"]._cron_send_reminders()
        self.assertEqual(request.reminder_count, 1)
        self.assertTrue(request.last_reminder_date)

    def test_cron_skips_disabled_reminders(self):
        """Cron should not send reminders when reminder_enabled is False."""
        request = self._create_request(
            reminder_enabled=False,
            reminder_interval_days=1,
        )
        request.action_send()
        request.sent_date = fields.Datetime.now() - timedelta(days=2)
        request.invalidate_recordset()
        self.env["sign.oca.request"]._cron_send_reminders()
        self.assertEqual(request.reminder_count, 0)

    # --- next_reminder_date computation ---

    def test_next_reminder_date_computed(self):
        """next_reminder_date should be sent_date + interval when enabled."""
        request = self._create_request(
            reminder_enabled=True,
            reminder_interval_days=3,
        )
        request.action_send()
        expected = request.sent_date + timedelta(days=3)
        self.assertEqual(request.next_reminder_date, expected)

    def test_next_reminder_date_false_when_disabled(self):
        """next_reminder_date should be False when reminders are disabled."""
        request = self._create_request(
            reminder_enabled=False,
            reminder_interval_days=3,
        )
        request.action_send()
        self.assertFalse(request.next_reminder_date)

    def test_next_reminder_date_after_reminder_sent(self):
        """next_reminder_date uses last_reminder_date after first reminder."""
        request = self._create_request(
            reminder_enabled=True,
            reminder_interval_days=2,
        )
        request.action_send()
        # Simulate reminder was sent
        now = fields.Datetime.now()
        request.write(
            {
                "last_reminder_date": now,
                "reminder_count": 1,
            }
        )
        request.invalidate_recordset()
        expected = now + timedelta(days=2)
        self.assertEqual(request.next_reminder_date, expected)

    # --- _check_signed disables reminders ---

    def test_check_signed_disables_reminders(self):
        """When all signers sign, reminders should be disabled."""
        request = self._create_request(reminder_enabled=True)
        request.action_send()
        self.assertTrue(request.reminder_enabled)
        # Simulate all signers signing
        for signer in request.signer_ids:
            signer.signed_on = fields.Datetime.now()
        request._check_signed()
        self.assertEqual(request.state, "2_signed")
        self.assertFalse(request.reminder_enabled)

    # --- Log action selection ---

    def test_log_action_selection_extended(self):
        """Log action field should include resend, expire, and reminder."""
        log_model = self.env["sign.oca.request.log"]
        action_field = log_model._fields["action"]
        selection_keys = [s[0] for s in action_field.selection]
        self.assertIn("resend", selection_keys)
        self.assertIn("expire", selection_keys)
        self.assertIn("reminder", selection_keys)
