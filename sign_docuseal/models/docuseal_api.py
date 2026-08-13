# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

import requests

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class DocusealApi(models.AbstractModel):
    """Thin, stateless DocuSeal REST client.

    Configuration lives in ``ir.config_parameter``, never in source:

    - ``docuseal.base_url``       the DocuSeal instance, without trailing slash
    - ``docuseal.api_key``        the ``X-Auth-Token`` value
    - ``docuseal.webhook_secret`` shared secret for the inbound webhook

    Some endpoints used here belong to the paid DocuSeal tier. They are
    documented as such on each method: against a community instance they
    answer 404 and this client turns that into a plain user error.
    """

    _name = "docuseal.api"
    _description = "DocuSeal API Client"

    @api.model
    def _get_config(self):
        params = self.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("docuseal.base_url") or "").rstrip("/")
        api_key = params.get_param("docuseal.api_key") or ""
        if not base_url or not api_key:
            raise UserError(
                _(
                    "DocuSeal is not configured. Set the base URL and the API "
                    "key under Settings > DocuSeal."
                )
            )
        return base_url, api_key

    @api.model
    def _request(
        self, method, endpoint, payload=None, params=None, timeout=DEFAULT_TIMEOUT
    ):
        base_url, api_key = self._get_config()
        url = "{}/api/{}".format(base_url, endpoint.lstrip("/"))
        headers = {
            "X-Auth-Token": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.request(
                method,
                url,
                json=payload,
                params=params,
                headers=headers,
                timeout=timeout,
            )
        except requests.exceptions.RequestException as error:
            _logger.exception("DocuSeal request failed: %s %s", method, url)
            raise UserError(_("Could not reach DocuSeal: %s") % error) from error

        if response.status_code >= 400:
            _logger.error(
                "DocuSeal API error %s on %s %s: %s",
                response.status_code,
                method,
                url,
                response.text[:500],
            )
            raise UserError(
                _(
                    "DocuSeal returned error %(code)s: %(body)s",
                    code=response.status_code,
                    body=response.text[:300],
                )
            )

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return response.content

    # -- High level helpers ------------------------------------------------

    @api.model
    def create_submission(
        self, template_id, submitters, send_email=True, order="preserved"
    ):
        """Create a submission from an existing DocuSeal template.

        :param submitters: list of dicts, e.g.
            ``[{"role": "First Party", "name": .., "email": .., "values": {}}]``
        :return: parsed JSON. DocuSeal returns the list of created submitters,
            each carrying ``submission_id``, ``slug`` and ``embed_src``.
        """
        if not template_id:
            raise UserError(_("No DocuSeal template id was given."))
        if not submitters:
            raise UserError(_("No signer was given for the signature request."))
        payload = {
            "template_id": int(template_id),
            "send_email": bool(send_email),
            "order": order,
            "submitters": submitters,
        }
        return self._request("POST", "submissions", payload=payload)

    @api.model
    def create_submission_from_html(
        self, html, submitters, name=False, send_email=True, order="preserved"
    ):
        """Create a submission directly from rendered HTML.

        The HTML may embed DocuSeal field text tags such as
        ``{{Signature;role=First Party;type=signature}}``, mapped to submitters
        by their ``role``. No persistent template is created.

        Requires a paid DocuSeal plan: ``POST /api/submissions/html`` answers
        404 on a community instance.
        """
        if not html:
            raise UserError(_("The contract HTML is empty."))
        if not submitters:
            raise UserError(_("No signer was given for the signature request."))
        payload = {
            "html": html,
            "submitters": submitters,
            "send_email": bool(send_email),
            "order": order,
        }
        if name:
            payload["name"] = name
        return self._request("POST", "submissions/html", payload=payload)

    @api.model
    def create_template_from_pdf(self, name, pdf_b64, fields, folder_name=False):
        """Create a template out of a PDF, with fields anchored by page
        fraction. A ``page`` of -1 places the field on the last page, which is
        the usual spot for a standardised signature page.

        Requires a paid DocuSeal plan: ``POST /api/templates/pdf`` answers 404
        on a community instance.
        """
        if not pdf_b64:
            raise UserError(_("The contract PDF is empty."))
        payload = {
            "name": name or "Odoo contract",
            "file": pdf_b64.decode() if isinstance(pdf_b64, bytes) else pdf_b64,
            "fields": fields or [],
        }
        if folder_name:
            payload["folder_name"] = folder_name
        return self._request("POST", "templates/pdf", payload=payload)

    @api.model
    def get_submission(self, submission_id):
        return self._request("GET", "submissions/%s" % submission_id)

    @api.model
    def download_documents(self, submission_id):
        """Return the list of completed documents, as ``{name, url}`` dicts."""
        result = self._request(
            "GET",
            "submissions/%s/documents" % submission_id,
            params={"merge": "true"},
        )
        if isinstance(result, dict):
            return result.get("documents", [])
        return result or []

    @api.model
    def fetch_url_content(self, url, timeout=DEFAULT_TIMEOUT):
        """Download a signed document file from a DocuSeal URL."""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            _logger.exception("DocuSeal document download failed: %s", url)
            raise UserError(
                _("Could not download the signed document: %s") % error
            ) from error
        return response.content
