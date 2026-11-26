# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SignOcaWebhookController(http.Controller):
    @http.route(
        "/sign_oca/webhook/<string:provider_code>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def provider_webhook(self, provider_code, **kwargs):
        provider = (
            request.env["sign.oca.provider"]
            .sudo()
            .search([("code", "=", provider_code), ("active", "=", True)], limit=1)
        )
        if not provider:
            return request.make_response("not found", status=404)

        raw = request.httprequest.get_data(cache=False, as_text=True)
        try:
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return request.make_response("invalid json", status=400)

        headers = dict(request.httprequest.headers)
        try:
            provider.process_webhook(payload, headers=headers)
        except Exception:
            _logger.exception("Error processing signature provider webhook")
            return request.make_response("webhook error", status=500)

        return request.make_response(
            json.dumps({"ok": True}),
            headers=[("Content-Type", "application/json")],
            status=200,
        )
