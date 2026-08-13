# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

CLIENT = "odoo.addons.sign_docuseal.models.docuseal_api.requests"


def fake_response(status_code=200, json_body=None, content=b"", text=""):
    response = mock.Mock()
    response.status_code = status_code
    response.text = text
    response.content = content if content else b"{}"
    if json_body is None:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = json_body
    return response


class TestDocusealApi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = cls.env["docuseal.api"]
        cls.params = cls.env["ir.config_parameter"].sudo()
        cls.params.set_param("docuseal.base_url", "https://sign.example.com/")
        cls.params.set_param("docuseal.api_key", "test-token")

    # -- configuration --------------------------------------------------
    def test_missing_configuration_raises(self):
        self.params.set_param("docuseal.api_key", "")
        with self.assertRaises(UserError):
            self.api._get_config()

    def test_base_url_trailing_slash_is_stripped(self):
        base_url, api_key = self.api._get_config()
        self.assertEqual(base_url, "https://sign.example.com")
        self.assertEqual(api_key, "test-token")

    # -- transport ------------------------------------------------------
    def test_request_sends_auth_header_and_builds_url(self):
        with mock.patch(CLIENT) as client:
            client.request.return_value = fake_response(json_body={"id": 1})
            client.exceptions = requests.exceptions
            result = self.api._request("GET", "/submissions/7")
        self.assertEqual(result, {"id": 1})
        _args, kwargs = client.request.call_args
        self.assertEqual(
            client.request.call_args[0],
            ("GET", "https://sign.example.com/api/submissions/7"),
        )
        self.assertEqual(kwargs["headers"]["X-Auth-Token"], "test-token")
        self.assertTrue(kwargs["timeout"])

    def test_connection_error_becomes_user_error(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.side_effect = requests.exceptions.ConnectionError("boom")
            with self.assertRaises(UserError):
                self.api._request("GET", "submissions")

    def test_http_error_becomes_user_error(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(
                status_code=404, text="Not Found"
            )
            with self.assertRaises(UserError):
                self.api._request("GET", "submissions/999")

    def test_empty_body_returns_empty_dict(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            response = fake_response()
            response.content = b""
            client.request.return_value = response
            self.assertEqual(self.api._request("DELETE", "submissions/1"), {})

    def test_non_json_body_is_returned_raw(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(content=b"%PDF-1.4")
            self.assertEqual(self.api._request("GET", "documents/1"), b"%PDF-1.4")

    # -- high level helpers ---------------------------------------------
    def test_create_submission_payload(self):
        submitters = [{"role": "First Party", "email": "a@example.com"}]
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(json_body=[])
            self.api.create_submission("8", submitters, send_email=False)
        payload = client.request.call_args[1]["json"]
        self.assertEqual(payload["template_id"], 8)
        self.assertFalse(payload["send_email"])
        self.assertEqual(payload["order"], "preserved")
        self.assertEqual(payload["submitters"], submitters)

    def test_create_submission_requires_template_and_submitters(self):
        with self.assertRaises(UserError):
            self.api.create_submission(False, [{"role": "x"}])
        with self.assertRaises(UserError):
            self.api.create_submission("8", [])

    def test_create_submission_from_html_payload(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(json_body={"id": 3})
            self.api.create_submission_from_html(
                "<p>contract</p>", [{"role": "x"}], name="Contract 1"
            )
        payload = client.request.call_args[1]["json"]
        self.assertEqual(payload["html"], "<p>contract</p>")
        self.assertEqual(payload["name"], "Contract 1")

    def test_create_submission_from_html_validates_input(self):
        with self.assertRaises(UserError):
            self.api.create_submission_from_html("", [{"role": "x"}])
        with self.assertRaises(UserError):
            self.api.create_submission_from_html("<p>x</p>", [])

    def test_create_template_from_pdf_decodes_bytes(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(json_body={"id": 5})
            self.api.create_template_from_pdf(
                False, b"cGRm", [{"name": "sig"}], folder_name="Contracts"
            )
        payload = client.request.call_args[1]["json"]
        self.assertEqual(payload["file"], "cGRm")
        self.assertEqual(payload["name"], "Odoo contract")
        self.assertEqual(payload["folder_name"], "Contracts")

    def test_create_template_from_pdf_requires_a_file(self):
        with self.assertRaises(UserError):
            self.api.create_template_from_pdf("Contract", None, [])

    def test_get_submission_hits_the_right_endpoint(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(
                json_body={"id": 55, "status": "pending"}
            )
            result = self.api.get_submission("55")
        self.assertEqual(result["status"], "pending")
        self.assertEqual(
            client.request.call_args[0],
            ("GET", "https://sign.example.com/api/submissions/55"),
        )

    def test_download_documents_unwraps_both_shapes(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.request.return_value = fake_response(
                json_body={"documents": [{"name": "a", "url": "u"}]}
            )
            self.assertEqual(
                self.api.download_documents("1"), [{"name": "a", "url": "u"}]
            )
            client.request.return_value = fake_response(json_body=[])
            self.assertEqual(self.api.download_documents("1"), [])

    def test_fetch_url_content_returns_bytes(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.get.return_value = fake_response(content=b"PDFDATA")
            self.assertEqual(
                self.api.fetch_url_content("https://x/doc.pdf"), b"PDFDATA"
            )

    def test_fetch_url_content_failure_becomes_user_error(self):
        with mock.patch(CLIENT) as client:
            client.exceptions = requests.exceptions
            client.get.side_effect = requests.exceptions.Timeout("slow")
            with self.assertRaises(UserError):
                self.api.fetch_url_content("https://x/doc.pdf")
