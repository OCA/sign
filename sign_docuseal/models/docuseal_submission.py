# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

VALID_SUBMITTER_STATUS = ("awaiting", "sent", "opened", "completed", "declined")


class DocusealSubmission(models.Model):
    _name = "docuseal.submission"
    _description = "DocuSeal Submission"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(
        required=True, default=lambda s: _("New submission"), tracking=True
    )
    docuseal_id = fields.Char("DocuSeal ID", index=True, copy=False, tracking=True)
    template_id = fields.Char("Template ID")
    # Generic link to the source business record (e.g. a sale.order).
    res_model = fields.Char("Source Model", index=True)
    res_id = fields.Integer("Source ID", index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("pending", "Awaiting Signature"),
            ("completed", "Completed"),
            ("declined", "Declined"),
            ("expired", "Expired"),
        ],
        default="draft",
        tracking=True,
        index=True,
    )
    submitter_ids = fields.One2many(
        "docuseal.submitter", "submission_id", string="Signers"
    )
    signed_document = fields.Binary(attachment=True, copy=False)
    signed_filename = fields.Char(copy=False)
    audit_log_url = fields.Char("Audit Trail URL", copy=False)
    audit_log_file = fields.Binary("Audit Trail (PDF)", attachment=True, copy=False)
    audit_log_filename = fields.Char(copy=False)
    completed_date = fields.Datetime("Completed On", copy=False)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    # ------------------------------------------------------------------
    def _get_source_record(self):
        self.ensure_one()
        if self.res_model and self.res_id and self.res_model in self.env:
            return self.env[self.res_model].browse(self.res_id).exists()
        return None

    @api.model
    def create_and_send(
        self,
        template_id,
        submitters,
        source=None,
        name=False,
        send_email=True,
        order="preserved",
    ):
        """Create a DocuSeal submission from an existing template."""
        response = self.env["docuseal.api"].create_submission(
            template_id, submitters, send_email=send_email, order=order
        )
        return self._build_tracking(
            response, source=source, name=name, template_id=template_id
        )

    @api.model
    def create_from_html(
        self,
        html,
        submitters,
        source=None,
        name=False,
        send_email=True,
        order="preserved",
    ):
        """Create a DocuSeal submission directly from rendered HTML."""
        response = self.env["docuseal.api"].create_submission_from_html(
            html, submitters, name=name, send_email=send_email, order=order
        )
        return self._build_tracking(response, source=source, name=name)

    @api.model
    def _build_tracking(self, response, source=None, name=False, template_id=False):
        """Create the tracking record from a DocuSeal API response.

        Handles both response shapes: a list of submitters (POST /submissions)
        or an object with ``id`` plus ``submitters`` (POST /submissions/html).
        """
        if isinstance(response, dict):
            docuseal_id = response.get("id")
            rows = response.get("submitters", []) or []
        else:
            rows = response or []
            docuseal_id = rows[0].get("submission_id") if rows else False

        submitter_cmds = []
        for row in rows:
            status = row.get("status")
            if status not in VALID_SUBMITTER_STATUS:
                status = "awaiting"
            submitter_cmds.append(
                (
                    0,
                    0,
                    {
                        "docuseal_submitter_id": str(row.get("id") or ""),
                        "role": row.get("role"),
                        "name": row.get("name"),
                        "email": row.get("email"),
                        "slug": row.get("slug"),
                        "embed_src": row.get("embed_src"),
                        "status": status,
                    },
                )
            )

        vals = {
            "name": name
            or (source.display_name if source else _("DocuSeal submission")),
            "template_id": str(template_id or ""),
            "docuseal_id": str(docuseal_id or ""),
            "state": "pending",
            "submitter_ids": submitter_cmds,
        }
        if source is not None and source:
            vals["res_model"] = source._name
            vals["res_id"] = source.id
        submission = self.create(vals)
        submission.message_post(body=_("Signature request sent to DocuSeal."))
        return submission

    # -- Webhook-driven state transitions (idempotent) ------------------
    def mark_completed(self, data=None):
        self.ensure_one()
        if self.state == "completed":
            return self  # idempotent: the webhook may fire more than once

        data = data or {}
        if self.docuseal_id:
            documents = self.env["docuseal.api"].download_documents(self.docuseal_id)
            if documents:
                doc = documents[0]
                content = self.env["docuseal.api"].fetch_url_content(doc.get("url"))
                self.write(
                    {
                        "signed_document": base64.b64encode(content),
                        "signed_filename": "%s.pdf"
                        % (doc.get("name") or "signed_document"),
                    }
                )

        audit_url = data.get("audit_log_url") or self.audit_log_url
        vals = {
            "state": "completed",
            "completed_date": fields.Datetime.now(),
            "audit_log_url": audit_url,
        }
        if audit_url and not self.audit_log_file:
            try:
                content = self.env["docuseal.api"].fetch_url_content(audit_url)
                vals.update(
                    {
                        "audit_log_file": base64.b64encode(content),
                        "audit_log_filename": "audit_trail_%s.pdf"
                        % (self.docuseal_id or self.id),
                    }
                )
            except UserError:
                # The trail stays reachable through its URL: a download
                # failure must not block the completion of the signature.
                _logger.exception(
                    "DocuSeal: could not download the audit log at %s", audit_url
                )
        self.write(vals)
        self.submitter_ids.write({"status": "completed"})

        source = self._get_source_record()
        if source is not None and hasattr(source, "_on_docuseal_completed"):
            source._on_docuseal_completed(self)
        self.message_post(body=_("Signature completed on DocuSeal."))
        return self

    def mark_declined(self, data=None):
        self.ensure_one()
        if self.state in ("completed", "declined"):
            return self
        self.write({"state": "declined"})
        self.message_post(body=_("Signature declined on DocuSeal."))
        return self

    @api.model
    def _cron_reconcile(self, min_age_hours=1, batch=50):
        """Missed-webhook fallback.

        For submissions still pending after ``min_age_hours``, ask DocuSeal
        for the current state and apply it locally. Each submission is
        committed on its own so that one unreachable record does not undo the
        progress made on the others.
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), hours=min_age_hours)
        pending = self.search(
            [
                ("state", "in", ("sent", "pending")),
                ("docuseal_id", "!=", False),
                ("create_date", "<=", cutoff),
            ],
            limit=batch,
        )
        for submission in pending:
            try:
                remote = self.env["docuseal.api"].get_submission(submission.docuseal_id)
            except UserError:
                _logger.exception(
                    "DocuSeal reconcile: could not read submission %s",
                    submission.docuseal_id,
                )
                continue
            status = (remote or {}).get("status") or ""
            for row in (remote or {}).get("submitters", []) or []:
                row_status = row.get("status")
                if row_status in VALID_SUBMITTER_STATUS:
                    submission.update_submitter_status(row.get("id"), row_status)
            if status == "completed":
                submission.mark_completed(remote)
            elif status == "declined":
                submission.mark_declined(remote)
            elif status == "expired" and submission.state not in (
                "completed",
                "declined",
            ):
                submission.write({"state": "expired"})
            # pylint: disable=invalid-commit
            # Deliberate: a cron batch must keep the submissions it already
            # reconciled even if a later one raises.
            self.env.cr.commit()
        return True

    def update_submitter_status(self, docuseal_submitter_id, status):
        self.ensure_one()
        submitter = self.submitter_ids.filtered(
            lambda s: s.docuseal_submitter_id == str(docuseal_submitter_id)
        )
        if submitter and status:
            submitter.write({"status": status})
            if status == "completed":
                submitter.write({"completed_at": fields.Datetime.now()})
        return submitter
