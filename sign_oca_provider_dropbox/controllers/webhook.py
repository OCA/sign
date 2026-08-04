# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DropboxSignWebhookController(http.Controller):
    @http.route(
        "/sign_oca/dropbox/webhook/<string:provider_code>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def dropbox_sign_webhook(
        self,
        provider_code,
        **kwargs,
    ):
        provider = (
            request.env["sign.oca.provider"]
            .sudo()
            .search(
                [
                    ("code", "=", provider_code),
                    ("provider_type", "=", "dropbox_sign"),
                    ("active", "=", True),
                ],
                limit=1,
            )
        )

        if not provider:
            return request.make_response(
                "not found",
                status=404,
            )

        raw_json = request.httprequest.form.get("json")
        if not raw_json:
            return request.make_response(
                "missing json field",
                status=400,
            )

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return request.make_response(
                "invalid json",
                status=400,
            )

        try:
            provider.process_webhook(
                payload,
                headers=dict(request.httprequest.headers),
            )
        except Exception:
            _logger.exception("Error processing Dropbox Sign webhook")
            return request.make_response(
                "webhook error",
                status=400,
            )

        # Dropbox Sign requires this exact acknowledgement text in a 200 body.
        return request.make_response(
            "Hello API Event Received",
            headers=[("Content-Type", "text/plain")],
            status=200,
        )
