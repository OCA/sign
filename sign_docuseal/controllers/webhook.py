# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import hmac
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DocusealWebhook(http.Controller):
    """Inbound webhook from DocuSeal.

    Two routes accept the same payload, both checking the shared secret held
    in ``ir.config_parameter`` under ``docuseal.webhook_secret``:

    - ``POST /docuseal/webhook`` with the secret in the
      ``X-Odoo-Webhook-Secret`` header. Prefer this one.
    - ``POST /docuseal/webhook/<secret>`` with the secret in the path. Kept
      for instances already configured that way, but a secret in a URL ends
      up in web-server logs, proxy logs and referrers, so it should be
      migrated to the header form.

    Handling is idempotent: DocuSeal may deliver the same event more than
    once, and a non-2xx answer makes it retry.
    """

    @http.route(
        "/docuseal/webhook",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def docuseal_webhook_header(self, **kwargs):
        secret = request.httprequest.headers.get("X-Odoo-Webhook-Secret", "")
        return self.docuseal_webhook(secret, **kwargs)

    @http.route(
        "/docuseal/webhook/<string:secret>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def docuseal_webhook(self, secret, **kwargs):
        expected = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("docuseal.webhook_secret")
            or ""
        )
        if not expected or not hmac.compare_digest(secret, expected):
            _logger.warning("DocuSeal webhook rejected: invalid secret")
            return request.make_response("forbidden", status=403)

        try:
            raw = request.httprequest.get_data() or b"{}"
            payload = json.loads(raw)
        except ValueError:
            _logger.warning("DocuSeal webhook: invalid JSON body")
            return request.make_response("bad request", status=400)

        event = payload.get("event_type") or ""
        data = payload.get("data") or {}
        submissions = request.env["docuseal.submission"].sudo()
        try:
            self._handle_event(submissions, event, data)
        except Exception:  # noqa: BLE001 - log and let DocuSeal retry
            _logger.exception("DocuSeal webhook handling failed for event %s", event)
            return request.make_response("error", status=500)
        return request.make_response("ok", status=200)

    def _handle_event(self, submissions, event, data):
        # submission.* events carry the submission id in data["id"];
        # form.* events carry it in data["submission_id"].
        submission_ref = data.get("submission_id") or data.get("id")
        submission = submissions.browse()
        if submission_ref:
            submission = submissions.search(
                [("docuseal_id", "=", str(submission_ref))], limit=1
            )
        if not submission:
            _logger.info(
                "DocuSeal webhook: no submission for ref %s (event %s)",
                submission_ref,
                event,
            )
            return

        if event == "submission.completed":
            submission.mark_completed(data)
        elif event == "form.completed":
            submission.update_submitter_status(data.get("id"), "completed")
        elif event in ("form.viewed", "form.started"):
            submission.update_submitter_status(data.get("id"), "opened")
        elif event == "form.declined":
            submission.mark_declined(data)
        elif event == "submission.expired":
            if submission.state not in ("completed", "declined"):
                submission.write({"state": "expired"})
