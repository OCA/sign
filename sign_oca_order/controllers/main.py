# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.sign_oca.controllers.main import PortalSign


class PortalSignOrder(PortalSign):
    """Extend the portal sign controller to enforce sequential signing order.

    When a sign request uses ``signing_mode == 'sequential'``, signers whose
    ``signer_state`` is still ``'waiting'`` are shown a "please wait" page
    instead of the signing UI, and their JSON sign endpoint returns an error.
    """

    @http.route(
        ["/sign_oca/document/<int:signer_id>/<string:access_token>"],
        type="http",
        auth="public",
        website=True,
    )
    def get_sign_oca_access(self, signer_id, access_token, **kwargs):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        sign_request = signer_sudo.request_id
        if (
            sign_request.signing_mode == "sequential"
            and not signer_sudo.signed_on
            and signer_sudo.signer_state == "waiting"
        ):
            return request.render(
                "sign_oca_order.portal_sign_document_waiting",
                {
                    "signer": signer_sudo,
                    "company": sign_request.company_id,
                    "request_name": sign_request.name,
                },
            )
        return super().get_sign_oca_access(signer_id, access_token, **kwargs)

    @http.route(
        ["/sign_oca/sign/<int:signer_id>/<string:access_token>"],
        type="json",
        auth="public",
        website=True,
    )
    def get_sign_oca_sign_access(
        self, signer_id, access_token, items, latitude=False, longitude=False
    ):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if (
            signer_sudo.request_id.signing_mode == "sequential"
            and signer_sudo.signer_state == "waiting"
        ):
            return {"error": "It is not your turn to sign yet."}
        return super().get_sign_oca_sign_access(
            signer_id, access_token, items, latitude=latitude, longitude=longitude
        )
