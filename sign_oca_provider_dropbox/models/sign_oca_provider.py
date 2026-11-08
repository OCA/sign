# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import hashlib
import hmac
import io
import json
import logging
import time
import zipfile
from base64 import b64decode
from datetime import datetime, timezone

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SignOcaProvider(models.Model):
    _inherit = "sign.oca.provider"

    dropbox_test_mode = fields.Boolean(
        string="Test mode",
        default=True,
        help=(
            "Dropbox Sign test_mode requests are watermarked and are not "
            "legally binding. Disable this in production."
        ),
    )
    dropbox_client_id = fields.Char(
        string="API App Client ID",
        help=(
            "Optional Dropbox Sign API App client_id. When set, requests are "
            "associated with that API App and its callback URL."
        ),
    )
    dropbox_subject = fields.Char(
        string="Email subject",
        default="Document pending signature",
    )
    dropbox_message = fields.Text(
        string="Email message",
        default="Please review and sign the document.",
    )
    dropbox_allow_decline = fields.Boolean(
        string="Allow decline",
        default=True,
    )
    dropbox_expire_days = fields.Integer(
        string="Expiration (days)",
        default=30,
        help="Dropbox Sign supports an explicit expiration 1-90 days ahead.",
    )
    dropbox_sequential = fields.Boolean(
        string="Sequential signing",
        default=True,
        help="Send signer order values according to the OCA signer order.",
    )
    dropbox_use_eid = fields.Boolean(
        string="Require eID",
        default=False,
        help=(
            "Enable Dropbox Sign eID signing. This requires the corresponding "
            "Dropbox Sign add-on, one signer, and cannot be used in test mode."
        ),
    )
    dropbox_callback_url = fields.Char(
        string="Callback URL",
        compute="_compute_dropbox_callback_url",
    )

    @api.model
    def _selection_provider_type(self):
        return super()._selection_provider_type() + [
            ("dropbox_sign", "Dropbox Sign"),
        ]

    @api.depends("code")
    def _compute_dropbox_callback_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for provider in self:
            provider.dropbox_callback_url = (
                f"{base_url}/sign_oca/dropbox/webhook/{provider.code}"
                if base_url and provider.code
                else False
            )

    def _provider_check_configuration(self):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_check_configuration()

        if not self.credential_ref:
            raise ValidationError(
                _(
                    "Set Credential Reference to the ir.config_parameter key "
                    "that stores the Dropbox Sign API key."
                )
            )

        api_key = self._dropbox_get_api_key()
        if not api_key:
            raise ValidationError(
                _("The Dropbox Sign API key configuration parameter is empty.")
            )

        if not 1 <= self.dropbox_expire_days <= 90:
            raise ValidationError(
                _("Dropbox Sign expiration must be between 1 and 90 days.")
            )

        if self.dropbox_use_eid and self.dropbox_test_mode:
            raise ValidationError(_("Dropbox Sign eID cannot be used in test mode."))

        self._dropbox_request("GET", "/account")
        return True

    def _dropbox_get_api_key(self):
        self.ensure_one()
        return (
            self.env["ir.config_parameter"].sudo().get_param(self.credential_ref or "")
        )

    def _dropbox_base_url(self):
        return "https://api.hellosign.com/v3"

    def _dropbox_request(
        self,
        method,
        path,
        *,
        data=None,
        files=None,
        params=None,
        timeout=60,
        expect_binary=False,
    ):
        self.ensure_one()

        api_key = self._dropbox_get_api_key()
        if not api_key:
            raise UserError(_("Dropbox Sign API key is not configured."))

        url = (
            f"{self.api_base_url}{path}"
            if self.api_base_url
            else f"{self._dropbox_base_url()}{path}"
        )

        try:
            response = requests.request(
                method,
                url,
                auth=(api_key, ""),
                data=data,
                files=files,
                params=params,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise UserError(
                _("Could not connect to Dropbox Sign: %s") % str(exc)
            ) from exc

        if not response.ok:
            message = response.text[:1500]
            try:
                payload = response.json()
                error = payload.get("error") or {}
                message = error.get("error_msg") or error.get("error_name") or message
            except ValueError:
                _logger.debug(
                    "Dropbox error response did not contain valid JSON",
                    exc_info=True,
                )

            raise UserError(
                _("Dropbox Sign API error %(status)s: %(message)s")
                % {
                    "status": response.status_code,
                    "message": message,
                }
            )

        if expect_binary:
            return response.content

        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise UserError(
                _("Dropbox Sign returned an invalid JSON response.")
            ) from exc

    def _provider_prepare_request(self, request):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_prepare_request(request)

        self._dropbox_validate_request(request)

        return self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.id,
                "request_id": request.id,
                "state": "prepared",
            }
        )

    def _dropbox_validate_request(self, request):
        request.ensure_one()

        if not request.data:
            raise ValidationError(_("The signature request has no PDF document."))

        if not request.signer_ids:
            raise ValidationError(_("The signature request has no signers."))

        if self.dropbox_use_eid and len(request.signer_ids) != 1:
            raise ValidationError(
                _("Dropbox Sign eID currently requires exactly one signer.")
            )

        for signer in request.signer_ids:
            partner = signer.partner_id
            if not partner:
                raise ValidationError(_("Every signer must have a contact."))
            if not partner.email:
                raise ValidationError(
                    _("Signer '%s' has no email address.") % partner.display_name
                )

    def _provider_start_transaction(self, transaction):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_start_transaction(transaction)

        request = transaction.request_id
        self._dropbox_validate_request(request)

        data = {
            "title": request.name or _("Signature request"),
            "subject": (
                self.dropbox_subject or request.name or _("Document pending signature")
            ),
            "message": self.dropbox_message or "",
            "allow_decline": "1" if self.dropbox_allow_decline else "0",
            "test_mode": "1" if self.dropbox_test_mode else "0",
            "expires_at": str(int(time.time()) + (self.dropbox_expire_days * 86400)),
            "metadata[odoo_request_id]": str(request.id),
            "metadata[odoo_transaction_id]": str(transaction.id),
        }

        if self.dropbox_client_id:
            data["client_id"] = self.dropbox_client_id

        if self.dropbox_use_eid:
            data["is_eid"] = "1"

        for index, signer in enumerate(request.signer_ids):
            partner = signer.partner_id
            data[f"signers[{index}][email_address]"] = partner.email
            data[f"signers[{index}][name]"] = partner.name
            if self.dropbox_sequential:
                data[f"signers[{index}][order]"] = str(index)

        pdf_bytes = b64decode(request.data)
        filename = request.name or "document.pdf"
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"

        payload = self._dropbox_request(
            "POST",
            "/signature_request/send",
            data=data,
            files={
                "files[0]": (
                    filename,
                    pdf_bytes,
                    "application/pdf",
                )
            },
            timeout=120,
        )

        signature_request = payload.get("signature_request") or {}
        external_id = signature_request.get("signature_request_id")
        if not external_id:
            raise UserError(_("Dropbox Sign did not return a signature_request_id."))

        transaction.write(
            {
                "external_id": external_id,
                "sign_url": signature_request.get("signing_url"),
                "status_payload": signature_request,
                "state": self._dropbox_map_transaction_state(signature_request),
            }
        )

        self._dropbox_sync_signers(transaction, signature_request)
        return transaction

    def _provider_refresh_transaction(self, transaction):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_refresh_transaction(transaction)

        if not transaction.external_id:
            raise ValidationError(
                _("Transaction has no Dropbox Sign signature request ID.")
            )

        payload = self._dropbox_request(
            "GET",
            f"/signature_request/{transaction.external_id}",
        )
        signature_request = payload.get("signature_request") or {}

        transaction.write(
            {
                "status_payload": signature_request,
                "state": self._dropbox_map_transaction_state(signature_request),
                "last_error": False,
            }
        )

        self._dropbox_sync_signers(transaction, signature_request)
        return transaction

    def _provider_cancel_transaction(self, transaction):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_cancel_transaction(transaction)

        if transaction.external_id:
            self._dropbox_request(
                "POST",
                f"/signature_request/cancel/{transaction.external_id}",
            )

        # Cancellation is asynchronous at Dropbox Sign. Keep processing until
        # refresh/webhook confirms the terminal state.
        transaction.state = "processing"
        return transaction

    def _provider_process_webhook(self, payload, headers=None):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_process_webhook(
                payload,
                headers=headers,
            )

        self._dropbox_verify_event_hash(payload)

        signature_request = payload.get("signature_request") or {}
        external_id = signature_request.get("signature_request_id")
        if not external_id:
            return self.env["sign.oca.provider.transaction"]

        transaction = (
            self.env["sign.oca.provider.transaction"]
            .sudo()
            .search(
                [
                    ("provider_id", "=", self.id),
                    ("external_id", "=", external_id),
                ],
                limit=1,
            )
        )

        if transaction:
            # Treat callback only as authenticated notification; refresh the
            # canonical state from the Dropbox Sign API.
            self.refresh_transaction(transaction)

        return transaction

    def _dropbox_verify_event_hash(self, payload):
        self.ensure_one()

        event = payload.get("event") or {}
        event_time = str(event.get("event_time") or "")
        event_type = event.get("event_type") or ""
        event_hash = event.get("event_hash") or ""

        if not event_time or not event_type or not event_hash:
            raise ValidationError(
                _("Dropbox Sign webhook event hash data is incomplete.")
            )

        expected = hmac.new(
            self._dropbox_get_api_key().encode("utf-8"),
            f"{event_time}{event_type}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, event_hash):
            raise ValidationError(_("Invalid Dropbox Sign webhook event hash."))

        return True

    def _provider_download_signed_document(self, transaction):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_download_signed_document(transaction)

        return self._dropbox_request(
            "GET",
            f"/signature_request/files/{transaction.external_id}",
            params={"file_type": "pdf"},
            expect_binary=True,
            timeout=120,
        )

    def _provider_download_evidence(self, transaction):
        self.ensure_one()
        if self.provider_type != "dropbox_sign":
            return super()._provider_download_evidence(transaction)

        payload = self._dropbox_request(
            "GET",
            f"/signature_request/{transaction.external_id}",
        )

        output = io.BytesIO()
        with zipfile.ZipFile(
            output,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                "dropbox_sign_status.json",
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                ).encode("utf-8"),
            )

        return output.getvalue()

    def _dropbox_map_transaction_state(self, signature_request):
        signatures = signature_request.get("signatures") or []
        signer_states = {
            signature.get("status_code")
            for signature in signatures
            if signature.get("status_code")
        }

        if signature_request.get("has_error"):
            return "error"

        if signature_request.get("is_declined"):
            return "rejected"

        if signature_request.get("is_complete"):
            return "signed"

        if signer_states & {"declined"}:
            return "rejected"

        if signer_states & {"expired"}:
            return "cancelled"

        if signer_states and signer_states <= {"signed"}:
            return "signed"

        if signer_states & {"awaiting_signature"}:
            return "waiting"

        return "processing"

    def _dropbox_sync_signers(self, transaction, signature_request):
        signatures_by_email = {
            (item.get("signer_email_address") or "").strip().lower(): item
            for item in (signature_request.get("signatures") or [])
            if item.get("signer_email_address")
        }

        now = fields.Datetime.now()

        for signer in transaction.request_id.signer_ids:
            email = (signer.partner_id.email or "").strip().lower()
            remote = signatures_by_email.get(email)
            if not remote:
                continue

            status_code = remote.get("status_code")
            signer_state = self._dropbox_map_signer_state(remote)
            signed_on = False
            identity_status = None
            identity_method = None
            identity_verified_on = None

            if status_code == "signed":
                signed_on = (
                    self._dropbox_unix_to_datetime(remote.get("signed_at")) or now
                )
                identity_status = "verified"
                identity_method = "eid" if self.dropbox_use_eid else "provider_default"
                identity_verified_on = signed_on

            elif status_code == "declined":
                identity_status = "failed"

            vals = self._provider_build_signer_sync_values(
                signer,
                transaction,
                provider_signer_ref=remote.get("signature_id"),
                provider_sign_state=signer_state,
                state_updated_on=now,
                signed_on=signed_on,
                identity_status=identity_status,
                identity_method=identity_method,
                identity_verified_on=identity_verified_on,
            )

            signer.write(vals)

    def _dropbox_map_signer_state(self, remote_signature):
        status = remote_signature.get("status_code")

        if status == "signed":
            return "signed"
        if status == "declined":
            return "declined"
        if status == "expired":
            return "expired"

        if remote_signature.get("last_viewed_at"):
            return "opened"

        if status == "awaiting_signature":
            return "sent"

        return "pending"

    def _provider_normalize_logs(
        self,
        transaction,
        payload,
    ):
        if self.provider_type != "dropbox_sign":
            return super()._provider_normalize_logs(
                transaction,
                payload,
            )

        event = payload.get("event") or {}

        event_type = event.get("event_type")

        event_time = self._dropbox_unix_to_datetime(event.get("event_time"))

        external_ref = event.get("event_hash")

        return [
            {
                "external_ref": (f"dropbox:{external_ref}"),
                "event": event_type,
                "event_date": event_time,
                "description": (self._dropbox_event_description(event_type)),
                "payload": event,
            }
        ]

    def _dropbox_event_description(
        self,
        event_type,
    ):
        descriptions = {
            "signature_request_sent": ("Signature request sent"),
            "signature_request_viewed": ("Signature request viewed"),
            "signature_request_signed": ("Signer completed the signature"),
            "signature_request_all_signed": ("All signers completed the signature"),
            "signature_request_downloadable": ("Final signed document is available"),
            "signature_request_declined": ("Signature request declined"),
            "signature_request_canceled": ("Signature request cancelled"),
        }

        return descriptions.get(
            event_type,
            event_type,
        )

    def _dropbox_unix_to_datetime(self, value):
        if not value:
            return False
        try:
            return datetime.fromtimestamp(
                int(value),
                tz=timezone.utc,
            ).replace(tzinfo=None)
        except (TypeError, ValueError, OSError):
            return False
