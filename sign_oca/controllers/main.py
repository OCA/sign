import base64
import io

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.base.models.assetsbundle import AssetsBundle
from odoo.addons.portal.controllers.portal import CustomerPortal


class SignController(http.Controller):
    @http.route("/sign_oca/get_assets.<any(css,js):ext>", type="http", auth="public")
    def get_sign_resources(self, ext):
        xmlid = "sign_oca.sign_assets"
        files, _remains = request.env["ir.qweb"]._get_asset_content(
            xmlid, options=request.context
        )
        asset = AssetsBundle(xmlid, files)
        mock_attachment = getattr(asset, ext)()
        if isinstance(
            mock_attachment, list
        ):  # suppose that CSS asset will not required to be split in pages
            mock_attachment = mock_attachment[0]
        _status, headers, content = request.env["ir.http"].binary_content(
            id=mock_attachment.id, unique=asset.checksum
        )
        content_base64 = base64.b64decode(content) if content else ""
        headers.append(("Content-Length", len(content_base64)))
        return request.make_response(content_base64, headers)


class PortalSign(CustomerPortal):
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
        if signer_sudo.signed_on:
            return request.render(
                "sign_oca.portal_sign_document_signed",
                {
                    "signer": signer_sudo,
                    "company": signer_sudo.request_id.company_id,
                },
            )
        return request.render(
            "sign_oca.portal_sign_document",
            {
                "doc": signer_sudo.request_id,
                "partner": signer_sudo.partner_id,
                "signer": signer_sudo,
                "access_token": access_token,
            },
        )

    @http.route(
        ["/sign_oca/content/<int:signer_id>/<string:access_token>"],
        type="http",
        auth="public",
        website=True,
    )
    def get_sign_oca_content_access(self, signer_id, access_token):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        data = io.BytesIO(base64.standard_b64decode(signer_sudo.request_id.data))
        return http.send_file(data)

    @http.route(
        ["/sign_oca/info/<int:signer_id>/<string:access_token>"],
        type="json",
        auth="public",
        website=True,
    )
    def get_sign_oca_info_access(self, signer_id, access_token):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        return signer_sudo.get_info(access_token=access_token)

    @http.route(
        ["/sign_oca/sign/<int:signer_id>/<string:access_token>"],
        type="json",
        auth="public",
        website=True,
    )
    def get_sign_oca_sign_access(self, signer_id, access_token, items):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        signer_sudo.action_sign(items, access_token=access_token)
        return True
