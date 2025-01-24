from collections import OrderedDict
from urllib import parse

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv import expression

from odoo.addons.base.models.assetsbundle import AssetsBundle
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class SignController(http.Controller):
    @http.route("/sign_oca/get_assets.<any(css,js):ext>", type="http", auth="public")
    def get_sign_resources(self, ext):
        bundle = "sign_oca.sign_assets"
        files, _ = request.env["ir.qweb"]._get_asset_content(bundle)
        asset = AssetsBundle(bundle, files)
        mock_attachment = getattr(asset, ext)()
        if isinstance(
            mock_attachment, list
        ):  # suppose that CSS asset will not required to be split in pages
            mock_attachment = mock_attachment[0]
        stream = request.env["ir.binary"]._get_stream_from(mock_attachment)
        response = stream.get_response()
        return response


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
                "sign_oca_backend_info": {
                    "access_token": access_token,
                    "signer_id": signer_sudo.id,
                    "lang": signer_sudo.partner_id.lang,
                },
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
        return http.Stream.from_binary_field(
            signer_sudo.request_id, "data"
        ).get_response(mimetype="application/pdf")

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
    def get_sign_oca_sign_access(
        self, signer_id, access_token, items, latitude=False, longitude=False
    ):
        try:
            signer_sudo = self._document_check_access(
                "sign.oca.request.signer", signer_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        return signer_sudo.action_sign(
            items, access_token=access_token, latitude=latitude, longitude=longitude
        )

    def get_sign_requests_domain(self, request):
        domain = [
            ("request_id.state", "in", ("0_sent", "2_signed")),
            ("partner_id", "child_of", [request.env.user.partner_id.id]),
        ]
        return domain

    def _get_my_sign_requests_searchbar_filters(self):
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "sent": {
                "label": _("sent"),
                "domain": [("request_id.state", "=", "0_sent")],
            },
            "signed": {
                "label": _("Signed"),
                "domain": [("request_id.state", "=", "2_signed")],
            },
        }
        return searchbar_filters

    def _prepare_sign_portal_rendering_values(self, page=1, sign_page=False, **kwargs):
        # Sorting feature
        searchbar_sortings = {
            "state": {"label": _("Sent to Signed"), "order": "request_id"},
            "reverse_state": {"label": _("Signed to Sent"), "order": "request_id desc"},
            "date": {"label": _("Newest"), "order": "create_date desc"},
            "reverse_date": {"label": _("Oldest"), "order": "create_date"},
        }
        sortby = kwargs.get("sortby", "state")
        order = searchbar_sortings[sortby]["order"]
        # Filtering feature
        searchbar_filters = self._get_my_sign_requests_searchbar_filters()
        filterby = kwargs.get("filterby") or "all"
        domain = searchbar_filters.get(filterby, searchbar_filters["all"])["domain"]
        domain = expression.AND([domain, self.get_sign_requests_domain(request)])
        SignRequests = request.env["sign.oca.request.signer"].sudo()
        pager_values = portal_pager(
            url="/my/sign_requests",
            total=SignRequests.search_count(domain),
            page=page,
            step=self._items_per_page,
            url_args={},
        )
        sign_requests = SignRequests.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager_values["offset"],
        )
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "sign_requests": sign_requests.sudo() if sign_page else SignRequests,
                "page_name": "My Sign Requests",
                "pager": pager_values,
                "default_url": "/my/sign_requests",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "sortby": sortby,
                "filterby": filterby,
            }
        )
        return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "sign_oca_count" in counters:
            domain = self.get_sign_requests_domain(request)
            SignRequests = request.env["sign.oca.request.signer"].sudo()
            values["sign_oca_count"] = SignRequests.search_count(domain)
        return values

    @http.route(
        ["/my/sign_requests", "/my/sign_requests/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
    )
    def sign_requests(self, **kwargs):
        values = self._prepare_sign_portal_rendering_values(sign_page=True, **kwargs)
        return request.render(
            "sign_oca.sign_requests",
            values,
        )

    @http.route(
        ["/my/sign/<int:request_id>/download"], type="http", auth="user", website=True
    )
    def portal_download_signed(self, request_id, **kw):
        sign_request = request.env["sign.oca.request"].sudo().browse(request_id)
        if not sign_request.exists():
            return request.not_found()
        # find the signed document attachment
        attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "sign.oca.request"),
                    ("res_id", "=", sign_request.id),
                    ("res_field", "=", "data"),
                ],
                limit=1,
            )
        )
        if not attachment:
            return request.not_found()
        access_token = attachment.generate_access_token()[0]
        ascii_filename = "document.pdf"
        filename = sign_request.name or ascii_filename
        # Ensure .pdf extension
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
        utf8_filename = parse.quote(filename)
        params = {
            "download": "true",
            "filename": utf8_filename,
            "access_token": access_token,
        }
        url = f"/web/content/{attachment.id}?{parse.urlencode(params)}"
        return request.redirect(url)
