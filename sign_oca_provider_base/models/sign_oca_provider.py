# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import secrets

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SignOcaProvider(models.Model):
    _name = "sign.oca.provider"
    _description = "Electronic Signature Provider"
    _order = "sequence, name, id"

    name = fields.Char(
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    code = fields.Char(
        required=True,
        index=True,
        copy=False,
        default=lambda self: secrets.token_urlsafe(16),
        help="Stable technical identifier used in webhook URLs.",
    )
    provider_type = fields.Selection(
        selection="_selection_provider_type",
        required=True,
        help="Concrete provider implementation supplied by another addon.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    api_base_url = fields.Char()
    credential_ref = fields.Char(
        help=("The name of ir.config_parameter that stores the provider credentials."),
    )
    signature_level = fields.Selection(
        selection=[
            ("advanced", "Advanced electronic signature"),
            ("qualified", "Qualified electronic signature"),
        ],
        default="advanced",
        required=True,
    )
    identity_method = fields.Selection(
        selection=[
            ("provider_default", "Provider default"),
            ("otp_sms", "SMS OTP"),
            ("otp_email", "Email OTP"),
            ("certificate", "Digital certificate"),
            ("eid", "Electronic identity"),
            ("video", "Video identification"),
            ("other", "Other"),
        ],
        default="provider_default",
        required=True,
    )
    webhook_url = fields.Char(
        compute="_compute_webhook_url",
    )
    note = fields.Text()

    _sql_constraints = [
        (
            "sign_oca_provider_code_uniq",
            "unique(code)",
            "Provider code must be unique.",
        ),
    ]

    @api.model
    def _selection_provider_type(self):
        """Extend this selection in provider addons.

        Example:
            return super()._selection_provider_type() + [
                ("acme", "ACME Sign")
            ]
        """
        return [("dummy", "Development / Dummy")]

    def _compute_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for provider in self:
            provider.webhook_url = (
                f"{base_url}/sign_oca/webhook/{provider.code}"
                if base_url and provider.code
                else False
            )

    def action_check_configuration(self):
        for provider in self:
            provider._provider_check_configuration()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Provider configuration"),
                "message": _("Configuration is valid."),
                "type": "success",
                "sticky": False,
            },
        }

    def _get_default_provider(self):
        """Return the default provider for the current company.

        This is used to pre-fill the provider_id field in sign.oca.request.
        """
        return self.search(
            [("company_id", "=", self.env.company.id)],
            order="sequence, name, id",
            limit=1,
        )

    # -------------------------------------------------------------------------
    # Public orchestration API
    # -------------------------------------------------------------------------

    def prepare_request(self, request):
        self.ensure_one()
        request.ensure_one()
        self._ensure_company(request)
        self._provider_check_configuration()
        return self._provider_prepare_request(request)

    def start_transaction(self, transaction):
        self.ensure_one()
        transaction.ensure_one()
        if transaction.provider_id != self:
            raise ValidationError(_("Transaction belongs to another provider."))
        self._provider_check_configuration()
        return self._provider_start_transaction(transaction)

    def refresh_transaction(self, transaction):
        self.ensure_one()
        transaction.ensure_one()
        return self._provider_refresh_transaction(transaction)

    def cancel_transaction(self, transaction):
        self.ensure_one()
        transaction.ensure_one()
        return self._provider_cancel_transaction(transaction)

    def process_webhook(self, payload, headers=None):
        self.ensure_one()
        return self._provider_process_webhook(payload, headers=headers or {})

    def download_signed_document(self, transaction):
        self.ensure_one()
        transaction.ensure_one()
        return self._provider_download_signed_document(transaction)

    def download_evidence(self, transaction):
        self.ensure_one()
        transaction.ensure_one()
        return self._provider_download_evidence(transaction)

    def _ensure_company(self, request):
        if request.company_id != self.company_id:
            raise ValidationError(
                _("Provider and signature request must belong to the same company.")
            )

    # -------------------------------------------------------------------------
    # Provider hooks
    # -------------------------------------------------------------------------

    def _provider_check_configuration(self):
        """Validate configuration. Provider addons should call super()."""
        self.ensure_one()
        if self.provider_type == "dummy":
            return True
        raise UserError(
            _("Provider type '%s' is declared but has no implementation.")
            % self.provider_type
        )

    def _provider_prepare_request(self, request):
        """Create one or more transaction records and return a recordset.

        Provider implementations may create a single envelope transaction per
        request or one transaction per signer.
        """
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.id,
                "request_id": request.id,
                "state": "prepared",
            }
        )
        return transaction

    def _provider_start_transaction(self, transaction):
        """Send/upload the transaction to the remote provider."""
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        transaction.write(
            {
                "state": "waiting",
                "external_id": f"dummy-{transaction.id}",
            }
        )
        return transaction

    def _provider_refresh_transaction(self, transaction):
        """Query remote status and synchronize the transaction."""
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        return transaction

    def _provider_cancel_transaction(self, transaction):
        """Cancel/revoke the transaction remotely."""
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        transaction.state = "cancelled"
        return transaction

    def _provider_process_webhook(self, payload, headers=None):
        """Validate and process a provider callback.

        SECURITY: a real provider addon MUST verify provider authenticity
        (signature, mTLS, HMAC, JWT, or the provider-specific mechanism)
        before mutating any transaction.
        """
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        external_id = payload.get("external_id")
        state = payload.get("state")
        transaction = self.env["sign.oca.provider.transaction"].search(
            [
                ("provider_id", "=", self.id),
                ("external_id", "=", external_id),
            ],
            limit=1,
        )
        if transaction and state in dict(transaction._fields["state"].selection):
            transaction.write({"state": state, "status_payload": payload})
        return transaction

    def _provider_download_signed_document(self, transaction):
        """Return raw PDF bytes or False."""
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        return False

    def _provider_download_evidence(self, transaction):
        """Return evidence bytes or False."""
        self.ensure_one()
        if self.provider_type != "dummy":
            raise NotImplementedError()
        return False

    # -------------------------------------------------------------------------
    # Generic signer synchronization helpers
    # -------------------------------------------------------------------------

    def _provider_build_signer_sync_values(
        self,
        signer,
        transaction,
        *,
        provider_signer_ref=None,
        provider_sign_state=None,
        state_updated_on=None,
        signed_on=None,
        identity_status=None,
        identity_method=None,
        identity_verified_on=None,
    ):
        """Build common signer synchronization values.

        Provider connectors can reuse this helper and only provide provider-
        specific mapping logic for state/ref/date extraction.
        """
        self.ensure_one()
        signer.ensure_one()
        transaction.ensure_one()

        vals = {}

        if "provider_transaction_id" in signer._fields:
            vals["provider_transaction_id"] = transaction.id

        if provider_signer_ref is not None and "provider_signer_ref" in signer._fields:
            vals["provider_signer_ref"] = provider_signer_ref

        if provider_sign_state is not None and "provider_sign_state" in signer._fields:
            vals["provider_sign_state"] = provider_sign_state

        if (
            state_updated_on is not None
            and "provider_sign_state_updated_on" in signer._fields
        ):
            vals["provider_sign_state_updated_on"] = state_updated_on

        if signed_on and "signed_on" in signer._fields and not signer.signed_on:
            vals["signed_on"] = signed_on

        if identity_status is not None and "identity_status" in signer._fields:
            vals["identity_status"] = identity_status

        if (
            identity_method is not None
            and "identity_method" in signer._fields
            and not signer._fields["identity_method"].related
        ):
            vals["identity_method"] = identity_method

        if (
            identity_verified_on
            and "identity_verified_on" in signer._fields
            and not signer.identity_verified_on
        ):
            vals["identity_verified_on"] = identity_verified_on

        return vals
