# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import json
from unittest import mock

from odoo.tests import tagged
from odoo.tests.common import HttpCase

API = "odoo.addons.sign_docuseal.models.docuseal_api.DocusealApi"
SECRET = "s3cr3t-for-tests"


@tagged("post_install", "-at_install")
class TestDocusealControllers(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        params = cls.env["ir.config_parameter"].sudo()
        params.set_param("docuseal.base_url", "https://sign.example.com")
        params.set_param("docuseal.api_key", "test-token")
        params.set_param("docuseal.webhook_secret", SECRET)
        cls.submission = cls.env["docuseal.submission"].create(
            {
                "name": "Contract under test",
                "docuseal_id": "55",
                "state": "pending",
                "submitter_ids": [
                    (
                        0,
                        0,
                        {
                            "docuseal_submitter_id": "101",
                            "role": "First Party",
                            "name": "Jane Doe",
                            "slug": "abc123",
                            "embed_src": "https://sign.example.com/s/abc123",
                            "status": "sent",
                        },
                    )
                ],
            }
        )
        cls.submitter = cls.submission.submitter_ids

    def _post(self, payload, secret=SECRET, url="/docuseal/webhook"):
        headers = {"Content-Type": "application/json"}
        if secret is not None:
            headers["X-Odoo-Webhook-Secret"] = secret
        return self.url_open(url, data=json.dumps(payload), headers=headers)

    # -- authentication ---------------------------------------------------
    def test_wrong_secret_is_rejected(self):
        response = self._post({"event_type": "form.viewed"}, secret="wrong")
        self.assertEqual(response.status_code, 403)

    def test_missing_secret_is_rejected(self):
        response = self._post({"event_type": "form.viewed"}, secret=None)
        self.assertEqual(response.status_code, 403)

    def test_everything_is_rejected_when_no_secret_is_configured(self):
        self.env["ir.config_parameter"].sudo().set_param("docuseal.webhook_secret", "")
        response = self._post({"event_type": "form.viewed"}, secret="")
        self.assertEqual(response.status_code, 403)

    def test_secret_in_the_path_still_works(self):
        response = self._post(
            {"event_type": "form.viewed", "data": {"submission_id": "55", "id": 101}},
            secret=None,
            url="/docuseal/webhook/%s" % SECRET,
        )
        self.assertEqual(response.status_code, 200)

    # -- payload handling --------------------------------------------------
    def test_invalid_json_is_a_bad_request(self):
        response = self.url_open(
            "/docuseal/webhook",
            data="not json",
            headers={
                "Content-Type": "application/json",
                "X-Odoo-Webhook-Secret": SECRET,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_submission_is_acknowledged(self):
        """Answering 200 stops DocuSeal from retrying an event we cannot map."""
        response = self._post(
            {"event_type": "submission.completed", "data": {"id": "does-not-exist"}}
        )
        self.assertEqual(response.status_code, 200)

    def test_form_viewed_marks_the_signer_as_opened(self):
        response = self._post(
            {
                "event_type": "form.viewed",
                "data": {"submission_id": "55", "id": 101},
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submitter.status, "opened")

    def test_form_declined_declines_the_submission(self):
        response = self._post(
            {"event_type": "form.declined", "data": {"submission_id": "55"}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submission.state, "declined")

    def test_form_completed_completes_only_that_signer(self):
        response = self._post(
            {
                "event_type": "form.completed",
                "data": {"submission_id": "55", "id": 101},
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submitter.status, "completed")
        self.assertEqual(self.submission.state, "pending")

    def test_submission_completed_stores_the_document(self):
        with mock.patch(
            API + ".download_documents",
            return_value=[{"name": "contract", "url": "https://x/c.pdf"}],
        ), mock.patch(API + ".fetch_url_content", return_value=b"PDFDATA"):
            response = self._post(
                {"event_type": "submission.completed", "data": {"id": "55"}}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submission.state, "completed")
        self.assertTrue(self.submission.signed_document)

    def test_submission_expired_expires_a_pending_request(self):
        response = self._post(
            {"event_type": "submission.expired", "data": {"id": "55"}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submission.state, "expired")

    def test_expiry_does_not_override_a_completed_request(self):
        self.submission.write({"state": "completed"})
        self._post({"event_type": "submission.expired", "data": {"id": "55"}})
        self.assertEqual(self.submission.state, "completed")

    def test_unknown_event_is_acknowledged_without_change(self):
        response = self._post(
            {"event_type": "submission.archived", "data": {"id": "55"}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submission.state, "pending")

    def test_handler_failure_asks_docuseal_to_retry(self):
        with mock.patch(API + ".download_documents", side_effect=ValueError("boom")):
            response = self._post(
                {"event_type": "submission.completed", "data": {"id": "55"}}
            )
        self.assertEqual(response.status_code, 500)

    # -- signing page -------------------------------------------------------
    def test_signing_page_renders_the_embedded_form(self):
        response = self.url_open(
            "/docuseal/sign/%s/%s" % (self.submitter.id, self.submitter.access_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.submitter.embed_src, response.text)

    def test_signing_page_rejects_a_wrong_token(self):
        response = self.url_open("/docuseal/sign/%s/%s" % (self.submitter.id, "0" * 32))
        self.assertEqual(response.status_code, 404)

    def test_signing_page_rejects_an_unknown_signer(self):
        response = self.url_open("/docuseal/sign/999999/whatever")
        self.assertEqual(response.status_code, 404)

    def test_signing_page_confirms_an_already_signed_request(self):
        self.submitter.write({"status": "completed"})
        response = self.url_open(
            "/docuseal/sign/%s/%s" % (self.submitter.id, self.submitter.access_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.submitter.embed_src, response.text)
