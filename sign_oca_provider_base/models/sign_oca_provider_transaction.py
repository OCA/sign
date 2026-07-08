# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import hashlib
import io
import logging
import mimetypes
import zipfile
from base64 import b64decode, b64encode
from pathlib import PurePosixPath

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SignOcaProviderTransaction(models.Model):
    _name = "sign.oca.provider.transaction"
    _description = "Electronic Signature Provider Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    provider_id = fields.Many2one(
        comodel_name="sign.oca.provider",
        required=True,
        ondelete="restrict",
        index=True,
    )
    request_id = fields.Many2one(
        comodel_name="sign.oca.request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    signer_id = fields.Many2one(
        comodel_name="sign.oca.request.signer",
        ondelete="cascade",
        index=True,
        help="Optional. Leave empty for envelope/request-level providers.",
    )
    company_id = fields.Many2one(
        related="request_id.company_id",
        store=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("prepared", "Prepared"),
            ("waiting", "Waiting for signer/provider"),
            ("processing", "Processing"),
            ("signed", "Signed"),
            ("validated", "Validated"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    external_id = fields.Char(
        copy=False,
        index=True,
    )
    sign_url = fields.Char(
        copy=False,
    )
    original_document_hash = fields.Char(
        copy=False,
        readonly=True,
    )
    signed_document_hash = fields.Char(
        copy=False,
        readonly=True,
    )
    status_payload = fields.Json(
        copy=False,
    )
    last_error = fields.Text(
        copy=False,
    )
    signed_document_attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        copy=False,
        readonly=True,
        ondelete="set null",
    )
    evidence_attachment_id = fields.Many2one(
        "ir.attachment",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    synced_documents_with_request = fields.Boolean()

    def write(self, vals):
        previous_states = {transaction.id: transaction.state for transaction in self}

        result = super().write(vals)

        if "state" in vals:
            for transaction in self:
                previous_state = previous_states.get(transaction.id)
                if (
                    previous_state not in ("signed", "validated")
                    and transaction.state in ("signed", "validated")
                    and not transaction.synced_documents_with_request
                ):
                    transaction._on_provider_signed()

        return result

    def _on_provider_signed(self):
        self.ensure_one()

        self.action_fetch_artifacts()

        self._mirror_artifacts_to_request()

        self.request_id._provider_mark_request_signed(self)
        self.synced_documents_with_request = True
        self._on_request_signed_post_message()

        return True

    def _mirror_artifacts_to_request(self):
        self.ensure_one()

        if self.signed_document_attachment_id:
            self._copy_attachment_if_missing(self.signed_document_attachment_id)

        if self.evidence_attachment_id:
            self._extract_evidence_to_request(self.evidence_attachment_id)

        return True

    def _on_request_signed_post_message(self):
        self.ensure_one()

        self.message_post(
            subject=_("Request signed"),
            body=_("The request has been completed and signed."),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )

        return True

    def _copy_attachment_if_missing(
        self,
        attachment,
    ):
        self.ensure_one()

        existing = self.env["ir.attachment"].search(
            [
                (
                    "res_model",
                    "=",
                    self.request_id._name,
                ),
                (
                    "res_id",
                    "=",
                    self.request_id.id,
                ),
                (
                    "checksum",
                    "=",
                    attachment.checksum,
                ),
            ],
            limit=1,
        )

        if existing:
            return existing

        return attachment.copy(
            {
                "res_model": self.request_id._name,
                "res_id": self.request_id.id,
            }
        )

    def _compute_name(self):
        for tx in self:
            tx.name = (
                f"{tx.request_id.name or _('Signature request')} / "
                f"{tx.external_id or tx.id or _('New')}"
            )

    def action_start(self):
        for tx in self:
            if tx.state not in ("draft", "prepared", "error"):
                raise ValidationError(
                    _("Only draft, prepared, or error transactions can be started.")
                )
            tx.provider_id.start_transaction(tx)
        return True

    def action_refresh(self):
        refreshable_states = ("waiting", "processing", "signed")
        for tx in self.filtered(lambda record: record.state in refreshable_states):
            tx.provider_id.refresh_transaction(tx)
        return True

    def action_cancel(self):
        for tx in self:
            tx.provider_id.cancel_transaction(tx)
        return True

    def action_fetch_artifacts(self):
        for tx in self:
            if tx.signed_document_attachment_id and tx.evidence_attachment_id:
                continue

            signed_pdf = tx.provider_id.download_signed_document(tx)
            evidence = tx.provider_id.download_evidence(tx)
            vals = {}
            if signed_pdf:
                attachment = tx._create_attachment(
                    signed_pdf,
                    f"{tx.request_id.name or 'document'}-signed.pdf",
                    "application/pdf",
                )
                vals.update(
                    {
                        "signed_document_attachment_id": attachment.id,
                        "signed_document_hash": hashlib.sha256(signed_pdf).hexdigest(),
                    }
                )
            if evidence:
                attachment = tx._create_attachment(
                    evidence,
                    f"{tx.request_id.name}-evidence.bin",
                    "application/octet-stream",
                )
                vals["evidence_attachment_id"] = attachment.id
            if vals:
                tx.write(vals)
        return True

    def _create_attachment(self, content, filename, mimetype):
        self.ensure_one()
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": b64encode(content),
                "mimetype": mimetype,
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def _cron_refresh_transactions(self, limit=200):
        transactions = self.search(
            [("state", "in", ["waiting", "processing"])],
            limit=limit,
        )
        for transaction in transactions:
            try:
                with self.env.cr.savepoint():
                    transaction.provider_id.refresh_transaction(transaction)
            except Exception as exc:
                transaction.last_error = str(exc)
                _logger.exception(
                    (
                        "Error refreshing provider transaction %s "
                        "(provider=%s, external_id=%s, request=%s)"
                    ),
                    transaction.id,
                    transaction.provider_id.id,
                    transaction.external_id,
                    transaction.request_id.id,
                )

    def _extract_evidence_to_request(
        self,
        attachment,
    ):
        self.ensure_one()

        zip_content = b64decode(attachment.datas)

        with zipfile.ZipFile(
            io.BytesIO(zip_content),
            "r",
        ) as zip_file:
            for zip_info in zip_file.infolist():
                if zip_info.is_dir():
                    continue

                filename = PurePosixPath(zip_info.filename).name

                if not filename:
                    continue

                content = zip_file.read(zip_info)

                mimetype = (
                    mimetypes.guess_type(filename)[0] or "application/octet-stream"
                )

                existing = self.env["ir.attachment"].search(
                    [
                        (
                            "res_model",
                            "=",
                            self.request_id._name,
                        ),
                        (
                            "res_id",
                            "=",
                            self.request_id.id,
                        ),
                        (
                            "name",
                            "=",
                            filename,
                        ),
                    ],
                    limit=1,
                )

                if existing:
                    continue

                self.env["ir.attachment"].create(
                    {
                        "name": filename,
                        "datas": b64encode(content),
                        "mimetype": mimetype,
                        "res_model": self.request_id._name,
                        "res_id": self.request_id.id,
                    }
                )

        return True
