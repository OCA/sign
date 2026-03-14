# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    signing_mode = fields.Selection(
        selection=[
            ("parallel", "Parallel (All at once)"),
            ("sequential", "Sequential (Ordered)"),
        ],
        default="parallel",
        required=True,
        copy=True,
    )
    cc_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="sign_oca_request_cc_partner_rel",
        column1="request_id",
        column2="partner_id",
        string="CC Recipients",
    )
    current_signing_order = fields.Integer(
        default=0,
        copy=False,
        readonly=True,
    )

    def action_send(self, sign_now=False, message=""):
        """Send the sign request, handling parallel and sequential modes."""
        for record in self:
            if record.signing_mode == "parallel":
                super(SignOcaRequest, record).action_send(
                    sign_now=sign_now,
                    message=message,
                )
                for signer in record.signer_ids:
                    signer.signer_state = "sent"
            else:
                record._action_send_sequential(
                    sign_now=sign_now,
                    message=message,
                )
        return True

    def _action_send_sequential(self, sign_now=False, message=""):
        """Send in sequential mode: only first-order signers get notified."""
        self.ensure_one()
        if self.state != "1_draft":
            return
        self._set_action_log("validate")
        self.state = "0_sent"

        first_order = min(self.signer_ids.mapped("signing_order"))
        self.current_signing_order = first_order

        for signer in self.signer_ids:
            signer._portal_ensure_token()
            if signer.signing_order == first_order:
                signer.signer_state = "sent"
            else:
                signer.signer_state = "waiting"

        first_signers = self.signer_ids.filtered(
            lambda s: s.signing_order == first_order
        )
        self._send_signing_notification(
            first_signers,
            sign_now=sign_now,
            message=message,
        )

        if not self.sent_date:
            self.sent_date = fields.Datetime.now()

    def _send_signing_notification(self, signers, sign_now=False, message=""):
        """Send signing invitation emails to the specified signers."""
        self.ensure_one()
        for signer in signers:
            signer._portal_ensure_token()
            if sign_now and signer.partner_id == self.env.user.partner_id:
                continue
            base_url = signer.get_base_url()
            access_url = signer.access_url
            if not access_url.startswith("http"):
                access_url = base_url + access_url
            render_result = self.env["ir.qweb"]._render(
                "sign_oca_order.sign_oca_sequential_initial_mail",
                {
                    "record": self,
                    "signer": signer,
                    "body": message,
                    "link": access_url,
                },
                engine="ir.qweb",
                minimal_qcontext=True,
            )
            self.env["mail.thread"].message_notify(
                body=render_result,
                partner_ids=signer.partner_id.ids,
                subject="New document to sign",
                subtype_id=self.env.ref("mail.mt_comment").id,
                mail_auto_delete=False,
                email_layout_xmlid="mail.mail_notification_light",
            )

    def _send_next_step_notification(self, signers):
        """Send 'your turn to sign' emails for sequential advancement."""
        self.ensure_one()
        for signer in signers:
            signer._portal_ensure_token()
            base_url = signer.get_base_url()
            access_url = signer.access_url
            if not access_url.startswith("http"):
                access_url = base_url + access_url
            render_result = self.env["ir.qweb"]._render(
                "sign_oca_order.sign_oca_your_turn_mail",
                {
                    "record": self,
                    "signer": signer,
                    "link": access_url,
                },
                engine="ir.qweb",
                minimal_qcontext=True,
            )
            self.env["mail.thread"].message_notify(
                body=render_result,
                partner_ids=signer.partner_id.ids,
                subject=f"Your turn to sign: {self.name}",
                subtype_id=self.env.ref("mail.mt_comment").id,
                mail_auto_delete=False,
                email_layout_xmlid="mail.mail_notification_light",
            )

    def _advance_to_next_step(self):
        """Advance to the next signing step in sequential mode."""
        self.ensure_one()
        if self.signing_mode != "sequential":
            return
        current_step_signers = self.signer_ids.filtered(
            lambda s: s.signing_order == self.current_signing_order
        )
        if not all(s.signed_on for s in current_step_signers):
            return
        remaining_orders = self.signer_ids.filtered(
            lambda s: not s.signed_on and s.signing_order > self.current_signing_order
        ).mapped("signing_order")
        if remaining_orders:
            next_order = min(remaining_orders)
            self.current_signing_order = next_order
            next_signers = self.signer_ids.filtered(
                lambda s: s.signing_order == next_order
            )
            for signer in next_signers:
                signer.signer_state = "sent"
            self._send_next_step_notification(next_signers)
            self._set_action_log("advance_step")

    def _check_signed(self):
        """Update signer states, advance sequential steps, and send CC."""
        pre_signed = {r.id: r.state == "2_signed" for r in self}
        for record in self:
            for signer in record.signer_ids:
                if signer.signed_on and signer.signer_state != "signed":
                    signer.signer_state = "signed"
            record._advance_to_next_step()
        result = super()._check_signed()
        for record in self:
            if not pre_signed[record.id] and record.state == "2_signed":
                record._send_cc_notification()
        return result

    def _send_cc_notification(self):
        """Send CC notification with signed PDF attached."""
        self.ensure_one()
        if not self.cc_partner_ids:
            return
        attachment = self.env["ir.attachment"].create(
            {
                "name": self.filename or f"{self.name}.pdf",
                "res_model": "sign.oca.request",
                "res_id": self.id,
                "datas": self.data,
                "type": "binary",
            }
        )
        render_result = self.env["ir.qweb"]._render(
            "sign_oca_order.sign_oca_cc_notification_mail",
            {"record": self},
            engine="ir.qweb",
            minimal_qcontext=True,
        )
        self.env["mail.thread"].message_notify(
            body=render_result,
            partner_ids=self.cc_partner_ids.ids,
            subject=f"Document signed: {self.name}",
            subtype_id=self.env.ref("mail.mt_comment").id,
            mail_auto_delete=False,
            attachment_ids=[attachment.id],
            email_layout_xmlid="mail.mail_notification_light",
        )
        self._set_action_log("cc_notify")

    def action_send_signed_request(self):
        """Send a nicely formatted signed document copy to all signers."""
        self.ensure_one()
        if (
            self.state != "2_signed"
            or not self.env.company.sign_oca_send_sign_request_copy
        ):
            return
        attachment = self.env["ir.attachment"].create(
            {
                "name": self.filename or f"{self.name}.pdf",
                "res_model": "sign.oca.request",
                "res_id": self.id,
                "datas": self.data,
                "type": "binary",
            }
        )
        render_result = self.env["ir.qweb"]._render(
            "sign_oca_order.sign_oca_signed_copy_mail",
            {"record": self},
            engine="ir.qweb",
            minimal_qcontext=True,
        )
        self.env["mail.thread"].message_notify(
            body=render_result,
            partner_ids=self.signer_ids.mapped("partner_id").ids,
            subject=f"Document signed: {self.name}",
            subtype_id=self.env.ref("mail.mt_comment").id,
            mail_auto_delete=False,
            attachment_ids=[attachment.id],
            email_layout_xmlid="mail.mail_notification_light",
        )

    def action_resend(self):
        """Resend notifications, respecting sequential signing order."""
        self.ensure_one()
        if self.state != "0_sent":
            return
        if self.signing_mode == "parallel":
            return super().action_resend()
        # Sequential mode: only resend to current step's unsigned signers
        current_signers = self.signer_ids.filtered(
            lambda s: not s.signed_on and s.signing_order == self.current_signing_order
        )
        if not current_signers:
            return
        self._send_reminder_to_signers(current_signers, is_manual=True)
        self._set_action_log("resend")

    @api.model
    def _cron_send_reminders(self):
        """Expire overdue requests and send reminders with sequential awareness."""
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

        # Phase 2: Send reminders with sequential awareness
        due_requests = self.search(
            [
                ("state", "=", "0_sent"),
                ("reminder_enabled", "=", True),
                ("next_reminder_date", "<=", now),
            ]
        )
        for request in due_requests:
            try:
                if request.signing_mode == "sequential":
                    current_order = request.current_signing_order
                    unsigned_signers = request.signer_ids.filtered(
                        lambda s, co=current_order: not s.signed_on
                        and s.signing_order == co
                    )
                else:
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
