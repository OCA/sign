# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Signing page served by Odoo.

Signers never browse DocuSeal: each one gets a link to an Odoo page,
``/docuseal/sign/<submitter>/<token>``, which embeds the DocuSeal signing
form (an iframe on ``/s/<slug>``). The token belongs to Odoo -- one uuid4
per signer -- so the DocuSeal slug is never exposed in a link we send out.
"""
import hmac
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DocusealSigningPage(http.Controller):
    @http.route(
        "/docuseal/sign/<int:submitter_id>/<string:token>",
        type="http",
        auth="public",
        sitemap=False,
        website=True,
    )
    def docuseal_sign(self, submitter_id, token, **kwargs):
        submitter = (
            request.env["docuseal.submitter"].sudo().browse(submitter_id)
        ).exists()
        if (
            not submitter
            or not submitter.access_token
            or not hmac.compare_digest(submitter.access_token, token or "")
        ):
            _logger.info(
                "DocuSeal signing page: invalid token for submitter %s",
                submitter_id,
            )
            return request.not_found()
        return request.render(
            "sign_docuseal.signing_page",
            {
                "submitter": submitter,
                "submission": submitter.submission_id,
            },
        )
