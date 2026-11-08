# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import uuid

from odoo import api, fields, models


class DocusealSubmitter(models.Model):
    _name = "docuseal.submitter"
    _description = "DocuSeal Submitter"
    _order = "id"

    submission_id = fields.Many2one(
        "docuseal.submission", required=True, ondelete="cascade", index=True
    )
    docuseal_submitter_id = fields.Char("DocuSeal Submitter ID", index=True)
    role = fields.Char()
    name = fields.Char()
    email = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Contact")
    status = fields.Selection(
        [
            ("awaiting", "Awaiting"),
            ("sent", "Sent"),
            ("opened", "Opened"),
            ("completed", "Completed"),
            ("declined", "Declined"),
        ],
        default="awaiting",
    )
    slug = fields.Char(index=True, help="DocuSeal identifier used in the /s/<slug> URL")
    embed_src = fields.Char("Signing URL (DocuSeal)")
    completed_at = fields.Datetime("Signed On")
    # Signing happens on an ODOO page: the signer never browses DocuSeal.
    # The widget is embedded in /docuseal/sign/<id>/<token>, a public route
    # protected by a random token of our own, one per signer.
    access_token = fields.Char(
        copy=False, index=True, default=lambda self: uuid.uuid4().hex
    )
    signing_url = fields.Char("Signing Page (Odoo)", compute="_compute_signing_url")

    @api.depends("access_token")
    def _compute_signing_url(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        for submitter in self:
            submitter.signing_url = (
                "%s/docuseal/sign/%s/%s"
                % (base, submitter.id, submitter.access_token or "")
                if submitter.id and submitter.access_token
                else False
            )
