# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import hashlib
from base64 import b64decode

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

REFRESHABLE_PROVIDER_STATES = ("waiting", "processing", "signed")


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    provider_id = fields.Many2one(
        comodel_name="sign.oca.provider",
        domain="[('company_id', '=', company_id)]",
        tracking=True,
        default=lambda self: self.env["sign.oca.provider"]._get_default_provider(),
    )

    provider_transaction_ids = fields.One2many(
        comodel_name="sign.oca.provider.transaction",
        inverse_name="request_id",
        string="Provider Transactions",
        copy=False,
    )
    provider_state = fields.Selection(
        selection=[
            ("not_configured", "Not configured"),
            ("draft", "Draft"),
            ("in_progress", "In progress"),
            ("signed", "Signed"),
            ("validated", "Validated"),
            ("failed", "Failed"),
        ],
        compute="_compute_provider_state",
        store=True,
    )

    @api.depends(
        "provider_id",
        "provider_transaction_ids.state",
        "provider_transaction_ids.create_date",
    )
    def _compute_provider_state(self):
        for request in self:
            if not request.provider_id:
                request.provider_state = "not_configured"
                continue

            transaction = request.provider_transaction_ids.sorted(
                key=lambda tx: (
                    tx.create_date or fields.Datetime.from_string("1970-01-01"),
                    tx.id,
                ),
                reverse=True,
            )[:1]

            if not transaction:
                request.provider_state = "draft"
                continue

            state = transaction.state

            if state == "validated":
                request.provider_state = "validated"

            elif state == "signed":
                request.provider_state = "signed"

            elif state in {"error", "rejected", "cancelled"}:
                request.provider_state = "failed"

            elif state in {"prepared", "waiting", "processing"}:
                request.provider_state = "in_progress"

            else:
                request.provider_state = "draft"

    def _provider_mark_request_signed(
        self,
        transaction,
    ):
        self.ensure_one()
        transaction.ensure_one()

        latest_transaction = self.provider_transaction_ids.sorted(
            key=lambda tx: (
                tx.create_date,
                tx.id,
            ),
            reverse=True,
        )[:1]

        if latest_transaction != transaction:
            return False

        if transaction.state not in (
            "signed",
            "validated",
        ):
            return False

        self.write(
            {
                "state": "2_signed",
            }
        )

        return True

    def action_provider_prepare(self):
        for request in self:
            if not request.provider_id:
                raise ValidationError(_("Configure a provider first."))
            if request.provider_transaction_ids.filtered(
                lambda tx: tx.state not in ("cancelled", "rejected", "error")
            ):
                raise ValidationError(
                    _("This request already has an active provider transaction.")
                )
            if request.data:
                original_hash = hashlib.sha256(b64decode(request.data)).hexdigest()
            else:
                original_hash = False
            transactions = request.provider_id.prepare_request(request)
            transactions.write({"original_document_hash": original_hash})
        return True

    def action_provider_start(self):
        for request in self:
            transactions = request.provider_transaction_ids.filtered(
                lambda tx: tx.state in ("draft", "prepared", "error")
            )
            if not transactions:
                raise ValidationError(_("There are no transactions ready to start."))
            transactions.action_start()
        return True

    def action_provider_refresh(self):
        self.mapped("provider_transaction_ids").filtered(
            lambda tx: tx.state in REFRESHABLE_PROVIDER_STATES
        ).action_refresh()
        return True

    def cancel(self):
        res = super().cancel()
        for request in self:
            request.provider_transaction_ids.action_cancel()
        return res


class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    provider_transaction_id = fields.Many2one(
        "sign.oca.provider.transaction",
        copy=False,
        ondelete="set null",
    )
    identity_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("failed", "Failed"),
        ],
        default="pending",
        copy=False,
    )
    identity_method = fields.Selection(
        [
            ("provider_default", "Provider default"),
            ("otp_sms", "SMS OTP"),
            ("otp_email", "Email OTP"),
            ("certificate", "Digital certificate"),
            ("eid", "Electronic identity"),
            ("video", "Video identification"),
            ("other", "Other"),
        ],
        compute="_compute_identity_method",
        store=True,
        copy=False,
    )
    identity_verified_on = fields.Datetime(copy=False, readonly=True)
    provider_signer_ref = fields.Char(copy=False, index=True)
    provider_sign_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("opened", "Opened"),
            ("signing", "Signing"),
            ("signed", "Signed"),
            ("declined", "Declined"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
            ("error", "Error"),
        ],
        string="Provider signature status",
        default="pending",
        copy=False,
        index=True,
    )
    provider_sign_state_updated_on = fields.Datetime(
        string="Provider status updated on",
        copy=False,
        readonly=True,
    )

    @api.depends(
        "request_id.provider_id",
        "request_id.provider_id.identity_method",
    )
    def _compute_identity_method(self):
        for signer in self:
            signer.identity_method = (
                signer.request_id.provider_id.identity_method or "provider_default"
            )
