# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import io
import zipfile
from base64 import b64decode, b64encode
from unittest.mock import patch

from .common import SignOcaProviderCommon


class TestProviderTransaction(SignOcaProviderCommon):
    def test_action_start(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "prepared",
            }
        )

        with patch.object(
            type(self.provider),
            "start_transaction",
            autospec=True,
            return_value=transaction,
        ) as mocked_start:
            transaction.action_start()

        mocked_start.assert_called_once_with(
            self.provider,
            transaction,
        )

    def test_action_refresh(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(self.provider),
            "refresh_transaction",
            autospec=True,
            return_value=transaction,
        ) as mocked_refresh:
            transaction.action_refresh()

        mocked_refresh.assert_called_once_with(
            self.provider,
            transaction,
        )

    def test_action_cancel(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(self.provider),
            "cancel_transaction",
            autospec=True,
            return_value=transaction,
        ) as mocked_cancel:
            transaction.action_cancel()

        mocked_cancel.assert_called_once_with(
            self.provider,
            transaction,
        )

    def test_fetch_artifacts_creates_attachments(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
                "external_id": "remote-1",
            }
        )

        signed_pdf = b"%PDF-1.4\nSIGNED\n%%EOF"
        evidence = b"ZIP-EVIDENCE"

        with patch.object(
            type(self.provider),
            "download_signed_document",
            autospec=True,
            return_value=signed_pdf,
        ), patch.object(
            type(self.provider),
            "download_evidence",
            autospec=True,
            return_value=evidence,
        ):
            transaction.action_fetch_artifacts()

        self.assertTrue(transaction.signed_document_attachment_id)
        self.assertTrue(transaction.evidence_attachment_id)

        self.assertEqual(
            b64decode(transaction.signed_document_attachment_id.datas),
            signed_pdf,
        )

        self.assertEqual(
            b64decode(transaction.evidence_attachment_id.datas),
            evidence,
        )

    def test_fetch_artifacts_is_idempotent(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(self.provider),
            "download_signed_document",
            autospec=True,
            return_value=b"%PDF-1.4\nSIGNED\n%%EOF",
        ), patch.object(
            type(self.provider),
            "download_evidence",
            autospec=True,
            return_value=b"EVIDENCE",
        ):
            transaction.action_fetch_artifacts()

        # After first call both attachments must be stored.
        self.assertTrue(transaction.signed_document_attachment_id)
        self.assertTrue(transaction.evidence_attachment_id)

        # Second call must short-circuit because attachments already exist.
        with patch.object(
            type(self.provider),
            "download_signed_document",
            autospec=True,
            return_value=b"%PDF-1.4\nSIGNED\n%%EOF",
        ) as mocked_signed2, patch.object(
            type(self.provider),
            "download_evidence",
            autospec=True,
            return_value=b"EVIDENCE",
        ) as mocked_evidence2:
            transaction.action_fetch_artifacts()

        mocked_signed2.assert_not_called()
        mocked_evidence2.assert_not_called()

    def test_signed_transition_triggers_finalization(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(transaction),
            "_on_provider_signed",
            autospec=True,
        ) as mocked_finalize:
            transaction.write(
                {
                    "state": "signed",
                }
            )

        mocked_finalize.assert_called_once_with(transaction)

    def test_on_provider_signed_updates_request_and_flags_sync(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(transaction),
            "action_fetch_artifacts",
            autospec=True,
        ) as mocked_fetch, patch.object(
            type(transaction),
            "_mirror_artifacts_to_request",
            autospec=True,
        ) as mocked_mirror, patch.object(
            type(self.request),
            "_provider_mark_request_signed",
            autospec=True,
        ) as mocked_mark_signed, patch.object(
            type(transaction),
            "_on_request_signed_post_message",
            autospec=True,
        ) as mocked_message:
            result = transaction._on_provider_signed()

        mocked_fetch.assert_called_once_with(transaction)
        mocked_mirror.assert_called_once_with(transaction)
        mocked_mark_signed.assert_called_once_with(
            self.request,
            transaction,
        )
        mocked_message.assert_called_once_with(transaction)
        self.assertTrue(transaction.synced_documents_with_request)
        self.assertTrue(result)

    def test_non_terminal_transition_does_not_finalize(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(transaction),
            "_on_provider_signed",
            autospec=True,
        ) as mocked_finalize:
            transaction.write(
                {
                    "state": "processing",
                }
            )

        mocked_finalize.assert_not_called()

    def test_provider_state_uses_latest_transaction(self):
        older = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "error",
            }
        )

        newer = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
            }
        )

        newer.write(
            {
                "create_date": newer.create_date,
            }
        )

        self.request.invalidate_recordset(["provider_state"])

        self.assertEqual(
            self.request.provider_state,
            "in_progress",
        )

        older.unlink()

    def test_mark_request_signed_only_for_latest_transaction(self):
        old_transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
            }
        )

        new_transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
            }
        )

        result = self.request._provider_mark_request_signed(old_transaction)

        self.assertFalse(result)
        self.assertNotEqual(
            self.request.state,
            "2_signed",
        )

        new_transaction.write(
            {
                "state": "signed",
            }
        )

        result = self.request._provider_mark_request_signed(new_transaction)

        self.assertTrue(result)
        self.assertEqual(
            self.request.state,
            "2_signed",
        )

    def test_cron_refreshes_pending_transactions(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-1",
            }
        )

        with patch.object(
            type(self.provider),
            "refresh_transaction",
            autospec=True,
        ) as mocked_refresh:
            self.env["sign.oca.provider.transaction"]._cron_refresh_transactions()

        mocked_refresh.assert_called_once_with(
            self.provider,
            transaction,
        )

    def test_extract_evidence_to_request_creates_request_attachments(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
            }
        )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("nested/audit_trail.pdf", b"PDF-AUDIT")
            archive.writestr("status.json", b'{"ok": true}')
            archive.writestr("empty_dir/", b"")

        attachment = self.env["ir.attachment"].create(
            {
                "name": "evidence.zip",
                "datas": b64encode(zip_buffer.getvalue()),
                "mimetype": "application/zip",
                "res_model": transaction._name,
                "res_id": transaction.id,
            }
        )

        transaction._extract_evidence_to_request(attachment)

        created = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.request._name),
                ("res_id", "=", self.request.id),
                ("name", "in", ["audit_trail.pdf", "status.json"]),
            ]
        )

        self.assertEqual(len(created), 2)
        by_name = {record.name: record for record in created}
        self.assertEqual(b64decode(by_name["audit_trail.pdf"].datas), b"PDF-AUDIT")
        self.assertEqual(b64decode(by_name["status.json"].datas), b'{"ok": true}')

    def test_extract_evidence_to_request_skips_existing_filenames(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
            }
        )

        existing = self.env["ir.attachment"].create(
            {
                "name": "audit_trail.pdf",
                "datas": b64encode(b"EXISTING"),
                "mimetype": "application/pdf",
                "res_model": self.request._name,
                "res_id": self.request.id,
            }
        )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("audit_trail.pdf", b"NEW-CONTENT")

        attachment = self.env["ir.attachment"].create(
            {
                "name": "evidence.zip",
                "datas": b64encode(zip_buffer.getvalue()),
                "mimetype": "application/zip",
                "res_model": transaction._name,
                "res_id": transaction.id,
            }
        )

        transaction._extract_evidence_to_request(attachment)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.request._name),
                ("res_id", "=", self.request.id),
                ("name", "=", "audit_trail.pdf"),
            ]
        )

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments, existing)
        self.assertEqual(b64decode(existing.datas), b"EXISTING")
