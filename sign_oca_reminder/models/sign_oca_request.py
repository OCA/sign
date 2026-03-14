# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    sent_date = fields.Datetime(
        copy=False,
        readonly=True,
        help="Date and time when the request was sent to signers.",
    )
    reminder_enabled = fields.Boolean(
        string="Automatic Reminders",
        help="Send periodic email reminders to unsigned signers.",
    )
    reminder_interval_days = fields.Integer(
        string="Reminder Interval (Days)",
        help="Number of days between automatic reminders.",
    )
    last_reminder_date = fields.Datetime(
        string="Last Reminder Sent",
        copy=False,
        readonly=True,
    )
    reminder_count = fields.Integer(
        string="Reminders Sent",
        default=0,
        copy=False,
        readonly=True,
    )
    validity_date = fields.Date(
        string="Expiration Date",
        copy=False,
        help="Date after which the request will be automatically cancelled.",
    )
    is_expired = fields.Boolean(
        compute="_compute_is_expired",
        string="Expired",
    )
    next_reminder_date = fields.Datetime(
        compute="_compute_next_reminder_date",
        store=True,
        string="Next Reminder",
    )

    @api.depends("validity_date")
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_expired = record.validity_date and record.validity_date < today

    @api.depends(
        "reminder_enabled",
        "reminder_interval_days",
        "sent_date",
        "last_reminder_date",
        "state",
    )
    def _compute_next_reminder_date(self):
        for record in self:
            if (
                not record.reminder_enabled
                or record.state != "0_sent"
                or not record.reminder_interval_days
            ):
                record.next_reminder_date = False
                continue
            base_date = record.last_reminder_date or record.sent_date
            if not base_date:
                record.next_reminder_date = False
                continue
            record.next_reminder_date = base_date + timedelta(
                days=record.reminder_interval_days
            )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        company = self.env.company
        if "reminder_enabled" in fields_list:
            defaults["reminder_enabled"] = company.sign_oca_reminder_enabled
        if "reminder_interval_days" in fields_list:
            defaults["reminder_interval_days"] = (
                company.sign_oca_reminder_interval_days or 3
            )
        if "validity_date" in fields_list and company.sign_oca_validity_days:
            defaults["validity_date"] = fields.Date.context_today(self) + timedelta(
                days=company.sign_oca_validity_days
            )
        return defaults

    def action_send(self, sign_now=False, message=""):
        result = super().action_send(sign_now=sign_now, message=message)
        for record in self:
            if record.state == "0_sent" and not record.sent_date:
                record.sent_date = fields.Datetime.now()
        return result

    def action_resend(self):
        self.ensure_one()
        if self.state != "0_sent":
            return
        unsigned_signers = self.signer_ids.filtered(lambda s: not s.signed_on)
        if not unsigned_signers:
            return
        self._send_reminder_to_signers(unsigned_signers, is_manual=True)
        self._set_action_log("resend")

    def _send_reminder_to_signers(self, signers, is_manual=False):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for signer in signers:
            signer._portal_ensure_token()
            access_url = signer.access_url
            if not access_url.startswith("http"):
                access_url = base_url + access_url
            render_result = self.env["ir.qweb"]._render(
                "sign_oca_reminder.sign_oca_reminder_mail",
                {
                    "record": self,
                    "signer": signer,
                    "link": access_url,
                    "is_manual": is_manual,
                },
                engine="ir.qweb",
                minimal_qcontext=True,
            )
            subject = f"Reminder: {self.name} awaiting your signature"
            self.env["mail.thread"].message_notify(
                body=render_result,
                partner_ids=signer.partner_id.ids,
                subject=subject,
                subtype_id=self.env.ref("mail.mt_comment").id,
                mail_auto_delete=False,
                email_layout_xmlid="mail.mail_notification_light",
            )
        now = fields.Datetime.now()
        self.write(
            {
                "last_reminder_date": now,
                "reminder_count": self.reminder_count + 1,
            }
        )
        if not is_manual:
            self._set_action_log("reminder")

    @api.model
    def _cron_send_reminders(self):
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()

        # Phase 1: Expire overdue requests
        expired_requests = self.search(
            [
                ("state", "=", "0_sent"),
                ("validity_date", "!=", False),
                ("validity_date", "<", today),
            ]
        )
        for request in expired_requests:
            try:
                request._expire_request()
            except Exception:
                _logger.exception(
                    "Failed to expire sign request %s (id=%s)",
                    request.name,
                    request.id,
                )

        # Phase 2: Send reminders
        due_requests = self.search(
            [
                ("state", "=", "0_sent"),
                ("reminder_enabled", "=", True),
                ("next_reminder_date", "<=", now),
            ]
        )
        for request in due_requests:
            try:
                unsigned_signers = request.signer_ids.filtered(
                    lambda s: not s.signed_on
                )
                if unsigned_signers:
                    request._send_reminder_to_signers(unsigned_signers)
            except Exception:
                _logger.exception(
                    "Failed to send reminder for sign request %s (id=%s)",
                    request.name,
                    request.id,
                )

    def _expire_request(self):
        self.ensure_one()
        self.write({"state": "3_cancel"})
        self._set_action_log("expire")
        # Notify the request owner
        body = (
            f"The sign request <b>{self.name}</b> has expired because it was not "
            f"completed before the expiration date ({self.validity_date})."
        )
        self.env["mail.thread"].message_notify(
            body=body,
            partner_ids=self.create_uid.partner_id.ids,
            subject=f"Sign request expired: {self.name}",
            subtype_id=self.env.ref("mail.mt_comment").id,
            mail_auto_delete=False,
        )

    def _check_signed(self):
        result = super()._check_signed()
        for record in self:
            if record.state == "2_signed" and record.reminder_enabled:
                record.reminder_enabled = False
        return result


class SignRequestLog(models.Model):
    _inherit = "sign.oca.request.log"

    action = fields.Selection(
        selection_add=[
            ("resend", "Resend"),
            ("expire", "Expire"),
            ("reminder", "Reminder"),
        ],
        ondelete={
            "resend": "cascade",
            "expire": "cascade",
            "reminder": "cascade",
        },
    )
