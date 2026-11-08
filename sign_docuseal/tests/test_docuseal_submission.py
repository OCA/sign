# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import base64
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

API = "odoo.addons.sign_docuseal.models.docuseal_api.DocusealApi"

SUBMITTER_ROWS = [
    {
        "id": 101,
        "submission_id": 55,
        "role": "First Party",
        "name": "ACME Ltd",
        "email": "legal@acme.example",
        "slug": "abc123",
        "embed_src": "https://sign.example.com/s/abc123",
        "status": "sent",
    },
    {
        "id": 102,
        "submission_id": 55,
        "role": "Second Party",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "slug": "def456",
        "embed_src": "https://sign.example.com/s/def456",
        "status": "awaiting",
    },
]


class TestDocusealSubmission(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Submission = cls.env["docuseal.submission"]
        cls.partner = cls.env["res.partner"].create({"name": "Source Partner"})
        cls.env["ir.config_parameter"].sudo().set_param(
            "docuseal.base_url", "https://sign.example.com"
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "docuseal.api_key", "test-token"
        )

    def _submission(self, rows=None, source=None):
        # `rows` may legitimately be an empty list, so test it against None.
        response = SUBMITTER_ROWS if rows is None else rows
        with mock.patch(API + ".create_submission", return_value=response):
            return self.Submission.create_and_send(
                "8", [{"role": "First Party"}], source=source
            )

    # -- building the tracking record -----------------------------------
    def test_list_response_creates_one_line_per_signer(self):
        submission = self._submission()
        self.assertEqual(submission.state, "pending")
        self.assertEqual(submission.docuseal_id, "55")
        self.assertEqual(submission.template_id, "8")
        self.assertEqual(len(submission.submitter_ids), 2)
        first = submission.submitter_ids[0]
        self.assertEqual(first.docuseal_submitter_id, "101")
        self.assertEqual(first.role, "First Party")
        self.assertEqual(first.status, "sent")

    def test_object_response_shape_is_supported(self):
        response = {"id": 77, "submitters": SUBMITTER_ROWS}
        with mock.patch(API + ".create_submission_from_html", return_value=response):
            submission = self.Submission.create_from_html(
                "<p>c</p>", [{"role": "First Party"}], name="From HTML"
            )
        self.assertEqual(submission.docuseal_id, "77")
        self.assertEqual(submission.name, "From HTML")
        self.assertEqual(len(submission.submitter_ids), 2)

    def test_unknown_submitter_status_falls_back_to_awaiting(self):
        rows = [dict(SUBMITTER_ROWS[0], status="something-else")]
        submission = self._submission(rows=rows)
        self.assertEqual(submission.submitter_ids.status, "awaiting")

    def test_source_record_is_linked_and_names_the_submission(self):
        submission = self._submission(source=self.partner)
        self.assertEqual(submission.res_model, "res.partner")
        self.assertEqual(submission.res_id, self.partner.id)
        self.assertEqual(submission.name, self.partner.display_name)
        self.assertEqual(submission._get_source_record(), self.partner)

    def test_source_record_gone_returns_empty(self):
        submission = self._submission(source=self.partner)
        self.partner.unlink()
        self.assertFalse(submission._get_source_record())

    def test_no_source_uses_a_default_name(self):
        submission = self._submission()
        self.assertTrue(submission.name)
        self.assertIsNone(submission._get_source_record())

    def test_empty_response_still_creates_a_record(self):
        submission = self._submission(rows=[])
        self.assertFalse(submission.submitter_ids)
        self.assertFalse(submission.docuseal_id)

    # -- signing url -----------------------------------------------------
    def test_signing_url_points_at_odoo_not_docuseal(self):
        submission = self._submission()
        submitter = submission.submitter_ids[0]
        self.assertTrue(submitter.access_token)
        self.assertIn(
            "/docuseal/sign/%s/%s" % (submitter.id, submitter.access_token),
            submitter.signing_url,
        )
        self.assertNotIn("/s/abc123", submitter.signing_url)

    # -- completion ------------------------------------------------------
    def test_mark_completed_stores_document_and_audit_trail(self):
        submission = self._submission()
        with mock.patch(
            API + ".download_documents",
            return_value=[{"name": "contract", "url": "https://x/c.pdf"}],
        ), mock.patch(API + ".fetch_url_content", return_value=b"PDFDATA"):
            submission.mark_completed({"audit_log_url": "https://x/audit.pdf"})
        self.assertEqual(submission.state, "completed")
        self.assertTrue(submission.completed_date)
        self.assertEqual(base64.b64decode(submission.signed_document), b"PDFDATA")
        self.assertEqual(submission.signed_filename, "contract.pdf")
        self.assertTrue(submission.audit_log_file)
        self.assertEqual(set(submission.submitter_ids.mapped("status")), {"completed"})

    def test_mark_completed_is_idempotent(self):
        submission = self._submission()
        with mock.patch(API + ".download_documents", return_value=[]):
            submission.mark_completed()
        with mock.patch(API + ".download_documents") as download:
            submission.mark_completed()
            download.assert_not_called()

    def test_audit_trail_download_failure_does_not_block_completion(self):
        submission = self._submission()
        with mock.patch(API + ".download_documents", return_value=[]), mock.patch(
            API + ".fetch_url_content", side_effect=UserError("nope")
        ):
            submission.mark_completed({"audit_log_url": "https://x/audit.pdf"})
        self.assertEqual(submission.state, "completed")
        self.assertFalse(submission.audit_log_file)
        self.assertEqual(submission.audit_log_url, "https://x/audit.pdf")

    def test_completion_calls_the_hook_on_the_source_record(self):
        submission = self._submission(source=self.partner)
        calls = []
        with mock.patch(API + ".download_documents", return_value=[]):
            with mock.patch.object(
                type(self.partner),
                "_on_docuseal_completed",
                create=True,
                side_effect=lambda sub: calls.append(sub),
            ):
                submission.mark_completed()
        self.assertEqual(calls, [submission])

    def test_mark_declined_and_its_idempotency(self):
        submission = self._submission()
        submission.mark_declined()
        self.assertEqual(submission.state, "declined")
        submission.mark_declined()
        self.assertEqual(submission.state, "declined")

    def test_declining_a_completed_submission_is_ignored(self):
        submission = self._submission()
        with mock.patch(API + ".download_documents", return_value=[]):
            submission.mark_completed()
        submission.mark_declined()
        self.assertEqual(submission.state, "completed")

    # -- submitter status -------------------------------------------------
    def test_update_submitter_status_sets_signed_on(self):
        submission = self._submission()
        submitter = submission.update_submitter_status(101, "completed")
        self.assertEqual(submitter.status, "completed")
        self.assertTrue(submitter.completed_at)

    def test_update_submitter_status_ignores_unknown_signer(self):
        submission = self._submission()
        self.assertFalse(submission.update_submitter_status(999, "opened"))

    # -- reconciliation cron ----------------------------------------------
    def _age_submission(self, submission):
        """Push create_date back so the cron cutoff selects the record."""
        self.env.cr.execute(
            "UPDATE docuseal_submission "
            "SET create_date = create_date - interval '2 hours' WHERE id = %s",
            (submission.id,),
        )
        submission.invalidate_recordset()

    def test_cron_completes_a_submission_seen_as_completed_upstream(self):
        submission = self._submission()
        self._age_submission(submission)
        remote = {
            "status": "completed",
            "submitters": [{"id": 101, "status": "completed"}],
        }
        with mock.patch(API + ".get_submission", return_value=remote), mock.patch(
            API + ".download_documents", return_value=[]
        ), mock.patch.object(self.env.cr, "commit"):
            self.Submission._cron_reconcile()
        self.assertEqual(submission.state, "completed")

    def test_cron_marks_declined_and_expired(self):
        for status, expected in (("declined", "declined"), ("expired", "expired")):
            submission = self._submission()
            self._age_submission(submission)
            with mock.patch(
                API + ".get_submission", return_value={"status": status}
            ), mock.patch.object(self.env.cr, "commit"):
                self.Submission._cron_reconcile()
            self.assertEqual(submission.state, expected)

    def test_cron_skips_unreachable_submissions(self):
        submission = self._submission()
        self._age_submission(submission)
        with mock.patch(
            API + ".get_submission", side_effect=UserError("unreachable")
        ), mock.patch.object(self.env.cr, "commit"):
            self.Submission._cron_reconcile()
        self.assertEqual(submission.state, "pending")

    def test_cron_ignores_submissions_younger_than_the_cutoff(self):
        self._submission()
        with mock.patch(API + ".get_submission") as remote, mock.patch.object(
            self.env.cr, "commit"
        ):
            self.Submission._cron_reconcile()
            remote.assert_not_called()
