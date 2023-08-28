# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LexPersonaApi(models.Model):
    _name = "lexpersona.api"
    _description = "Lex Persona Web Service"

    def get_headers(self):
        user = self.env.user
        if not user.lexpersona_token:
            raise UserError(
                _(
                    "You are not allowed to launch a Signature Workflow. \
                  Ask an administrator for an API token."
                )
            )
        token = "Bearer " + user.lexpersona_token
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        return headers

    def api_post(self, url, data):
        url_request = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lexpersona_connector.lexpersona_base_url")
            + url
        )
        headers = self.get_headers()
        if self.env.context.get("content-type"):
            headers.update({"Content-Type": self.env.context.get("content-type")})
        try:
            if self.env.context.get("post_param") == "data":
                r = requests.post(url_request, data=data, headers=headers)
            else:
                r = requests.post(url_request, json=data, headers=headers)
            if r.status_code == 500:
                raise UserError(
                    _(
                        "Erreur Internal Server Error 500 sur %s : Contactez le support !"
                    )
                    % (url_request)
                )
            elif r.status_code != 200:
                raise UserError(
                    _(
                        "Message %s - Detail %s - Error %s sur %s : Contactez le support !"
                    )
                    % (
                        r.json().get("code"),
                        r.json().get("message"),
                        r.status_code,
                        url_request,
                    )
                )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception(e)
            raise UserError(
                _(
                    "We had trouble to create your data, please retry later or \
                    contact your support if the problem persists - Network Error sur %s"
                )
                % (url_request)
            )
        return r

    def api_put(self, url, data):
        url_request = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lexpersona_connector.lexpersona_base_url")
            + url
        )
        headers = self.get_headers()
        try:
            r = requests.put(url_request, json=data, headers=headers)
            if r.status_code == 500:
                raise UserError(
                    _(
                        "Erreur Internal Server Error 500 sur %s : Contactez le support !"
                    )
                    % (url_request)
                )
            elif r.status_code != 200:
                raise UserError(
                    _(
                        "Message %s - Detail %s - Error %s sur %s : Contactez le support !"
                    )
                    % (
                        r.json().get("code"),
                        r.json().get("message"),
                        r.status_code,
                        url_request,
                    )
                )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception(e)
            raise UserError(
                _(
                    "We had trouble to create your data, please retry later or \
                    contact your support if the problem persists - Network Error sur %s"
                )
                % (url_request)
            )
        return r

    def api_patch(self, url, data):
        url_request = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lexpersona_connector.lexpersona_base_url")
            + url
        )
        headers = self.get_headers()
        try:
            r = requests.patch(url_request, json=data, headers=headers)
            if r.status_code == 500:
                raise UserError(
                    _(
                        "Erreur Internal Server Error 500 sur %s : Contactez le support !"
                    )
                    % (url_request)
                )
            elif r.status_code != 200:
                raise UserError(
                    _(
                        "Message %s - Detail %s - Error %s sur %s : Contactez le support !"
                    )
                    % (
                        r.json().get("code"),
                        r.json().get("message"),
                        r.status_code,
                        url_request,
                    )
                )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception(e)
            raise UserError(
                _(
                    "We had trouble to create your data, please retry later or \
                    contact your support if the problem persists - Network Error sur %s"
                )
                % (url_request)
            )
        return r

    def api_get(self, url):
        url_request = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lexpersona_connector.lexpersona_base_url")
            + url
        )
        headers = self.get_headers()
        try:
            r = requests.get(url_request, headers=headers)
            if r.status_code == 500:
                raise UserError(
                    _(
                        "Erreur Internal Server Error 500 sur %s : Contactez le support !"
                    )
                    % (url_request)
                )
            elif r.status_code != 200:
                raise UserError(
                    _(
                        "Message %s - Detail %s - Error %s sur %s : Contactez le support !"
                    )
                    % (
                        r.json().get("code"),
                        r.json().get("message"),
                        r.status_code,
                        url_request,
                    )
                )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception(e)
            raise UserError(
                _(
                    "We had trouble to create your data, please retry later or \
                    contact your support if the problem persists - Network Error sur %s"
                )
                % (url_request)
            )
        return r
