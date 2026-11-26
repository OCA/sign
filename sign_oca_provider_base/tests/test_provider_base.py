# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.exceptions import ValidationError

from .common import SignOcaProviderCommon


class TestProviderBase(SignOcaProviderCommon):
    def test_prepare_request_creates_transaction(self):
        transaction = self.provider.prepare_request(self.request)

        self.assertEqual(
            transaction.provider_id,
            self.provider,
        )
        self.assertEqual(
            transaction.request_id,
            self.request,
        )
        self.assertEqual(
            transaction.state,
            "prepared",
        )

    def test_start_transaction_calls_provider_hook(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "prepared",
            }
        )

        with patch.object(
            type(self.provider),
            "_provider_start_transaction",
            autospec=True,
        ) as mocked_start:
            mocked_start.return_value = transaction

            result = self.provider.start_transaction(transaction)

        mocked_start.assert_called_once_with(
            self.provider,
            transaction,
        )

        self.assertEqual(
            result,
            transaction,
        )

    def test_refresh_transaction_calls_provider_hook(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-123",
            }
        )

        with patch.object(
            type(self.provider),
            "_provider_refresh_transaction",
            autospec=True,
        ) as mocked_refresh:
            mocked_refresh.return_value = transaction

            result = self.provider.refresh_transaction(transaction)

        mocked_refresh.assert_called_once_with(
            self.provider,
            transaction,
        )

        self.assertEqual(
            result,
            transaction,
        )

    def test_cancel_transaction_calls_provider_hook(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
                "external_id": "remote-123",
            }
        )

        with patch.object(
            type(self.provider),
            "_provider_cancel_transaction",
            autospec=True,
        ) as mocked_cancel:
            mocked_cancel.return_value = transaction

            result = self.provider.cancel_transaction(transaction)

        mocked_cancel.assert_called_once_with(
            self.provider,
            transaction,
        )

        self.assertEqual(
            result,
            transaction,
        )

    def test_download_signed_document_calls_provider_hook(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
                "external_id": "remote-123",
            }
        )

        expected = b"%PDF-1.4 signed"

        with patch.object(
            type(self.provider),
            "_provider_download_signed_document",
            autospec=True,
            return_value=expected,
        ) as mocked_download:
            result = self.provider.download_signed_document(transaction)

        mocked_download.assert_called_once_with(
            self.provider,
            transaction,
        )

        self.assertEqual(
            result,
            expected,
        )

    def test_download_evidence_calls_provider_hook(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "signed",
                "external_id": "remote-123",
            }
        )

        expected = b"ZIP-CONTENT"

        with patch.object(
            type(self.provider),
            "_provider_download_evidence",
            autospec=True,
            return_value=expected,
        ) as mocked_download:
            result = self.provider.download_evidence(transaction)

        mocked_download.assert_called_once_with(
            self.provider,
            transaction,
        )

        self.assertEqual(
            result,
            expected,
        )

    def test_invalid_provider_transaction_relation(self):
        other_provider = self.env["sign.oca.provider"].create(
            {
                "name": "Other Provider",
                "code": "other-provider",
                "provider_type": "dummy",
                "credential_ref": "test.provider.token",
            }
        )

        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": other_provider.id,
                "request_id": self.request.id,
                "state": "prepared",
            }
        )

        with self.assertRaises(ValidationError):
            self.provider.start_transaction(transaction)
