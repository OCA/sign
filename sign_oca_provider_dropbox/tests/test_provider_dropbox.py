# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import hashlib
import hmac
from unittest.mock import patch

from odoo.exceptions import ValidationError

from odoo.addons.sign_oca_provider_base.tests.common import (
    SignOcaProviderCommon,
)


class TestDropboxProvider(SignOcaProviderCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.provider = cls.env["sign.oca.provider"].create(
            {
                "name": "Dropbox Provider",
                "code": "dropbox-provider-test",
                "provider_type": "dropbox_sign",
                "credential_ref": "dropbox.provider.key",
                "dropbox_test_mode": True,
                "dropbox_use_eid": False,
            }
        )

        cls.env["ir.config_parameter"].sudo().set_param(
            "dropbox.provider.key",
            "dropbox-test-api-key",
        )

        cls.request.provider_id = cls.provider

        cls.transaction = cls.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": cls.provider.id,
                "request_id": cls.request.id,
                "state": "prepared",
            }
        )

    def test_check_configuration_rejects_eid_in_test_mode(self):
        self.provider.dropbox_use_eid = True
        self.provider.dropbox_test_mode = True

        with self.assertRaises(ValidationError):
            self.provider._provider_check_configuration()

    def test_check_configuration_calls_account_endpoint(self):
        self.provider.dropbox_use_eid = False
        self.provider.dropbox_test_mode = True

        with patch.object(
            type(self.provider),
            "_dropbox_request",
            autospec=True,
            return_value={},
        ) as mocked_request:
            self.provider._provider_check_configuration()

        mocked_request.assert_called_once_with(
            self.provider,
            "GET",
            "/account",
        )

    def test_start_transaction_sets_external_id_and_waiting_state(self):
        payload = {
            "signature_request": {
                "signature_request_id": "req-123",
                "signing_url": "https://example.com/sign/req-123",
                "signatures": [
                    {
                        "signer_email_address": self.partner_signer_1.email,
                        "signature_id": "sig-1",
                        "status_code": "awaiting_signature",
                    }
                ],
            }
        }

        with patch.object(
            type(self.provider),
            "_dropbox_request",
            autospec=True,
            return_value=payload,
        ) as mocked_request:
            self.provider._provider_start_transaction(self.transaction)

        self.assertEqual(self.transaction.external_id, "req-123")
        self.assertEqual(self.transaction.state, "waiting")
        self.assertEqual(
            self.transaction.sign_url,
            "https://example.com/sign/req-123",
        )

        self.assertEqual(mocked_request.call_count, 1)
        _, _, path = mocked_request.call_args.args[:3]
        self.assertEqual(path, "/signature_request/send")

    def test_start_transaction_sends_is_eid_when_enabled(self):
        self.provider.dropbox_use_eid = True
        self.provider.dropbox_test_mode = False

        request = self.env["sign.oca.request"].create(
            {
                "name": "Dropbox eID Contract",
                "data": self.request.data,
                "provider_id": self.provider.id,
            }
        )
        self.env["sign.oca.request.signer"].create(
            {
                "request_id": request.id,
                "partner_id": self.partner_signer_1.id,
                "role_id": self.signer_1.role_id.id,
            }
        )
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": request.id,
                "state": "prepared",
            }
        )

        payload = {
            "signature_request": {
                "signature_request_id": "req-eid-1",
                "signatures": [
                    {
                        "signer_email_address": self.partner_signer_1.email,
                        "signature_id": "sig-eid-1",
                        "status_code": "awaiting_signature",
                    }
                ],
            }
        }

        with patch.object(
            type(self.provider),
            "_dropbox_request",
            autospec=True,
            return_value=payload,
        ) as mocked_request:
            self.provider._provider_start_transaction(transaction)

        sent_data = mocked_request.call_args.kwargs.get("data") or {}
        self.assertEqual(sent_data.get("is_eid"), "1")

    def test_refresh_requires_external_id(self):
        transaction = self.env["sign.oca.provider.transaction"].create(
            {
                "provider_id": self.provider.id,
                "request_id": self.request.id,
                "state": "waiting",
            }
        )

        with self.assertRaises(ValidationError):
            self.provider._provider_refresh_transaction(transaction)

    def test_verify_event_hash_valid(self):
        self.env["ir.config_parameter"].sudo().set_param(
            self.provider.credential_ref,
            "dropbox-test-api-key",
        )

        event_time = "1720000000"
        event_type = "signature_request_signed"
        event_hash = hmac.new(
            b"dropbox-test-api-key",
            f"{event_time}{event_type}".encode(),
            hashlib.sha256,
        ).hexdigest()

        payload = {
            "event": {
                "event_time": event_time,
                "event_type": event_type,
                "event_hash": event_hash,
            }
        }

        self.assertTrue(self.provider._dropbox_verify_event_hash(payload))

    def test_verify_event_hash_invalid(self):
        payload = {
            "event": {
                "event_time": "1720000000",
                "event_type": "signature_request_signed",
                "event_hash": "invalid",
            }
        }

        with self.assertRaises(ValidationError):
            self.provider._dropbox_verify_event_hash(payload)

    def test_process_webhook_refreshes_matching_transaction(self):
        self.transaction.external_id = "req-123"

        payload = {
            "event": {
                "event_time": "1720000000",
                "event_type": "signature_request_signed",
                "event_hash": "hash",
            },
            "signature_request": {
                "signature_request_id": "req-123",
            },
        }

        with patch.object(
            type(self.provider),
            "_dropbox_verify_event_hash",
            autospec=True,
            return_value=True,
        ) as mocked_verify, patch.object(
            type(self.provider),
            "refresh_transaction",
            autospec=True,
            return_value=self.transaction,
        ) as mocked_refresh:
            transaction = self.provider._provider_process_webhook(payload)

        mocked_verify.assert_called_once_with(self.provider, payload)
        mocked_refresh.assert_called_once_with(self.provider, self.transaction)
        self.assertEqual(transaction, self.transaction)

    def test_dropbox_sync_signers_marks_eid_identity_when_signed(self):
        self.provider.dropbox_use_eid = True
        self.provider.dropbox_test_mode = False

        signature_request = {
            "signatures": [
                {
                    "signer_email_address": self.partner_signer_1.email,
                    "signature_id": "sig-1",
                    "status_code": "signed",
                    "signed_at": 1720000000,
                }
            ]
        }

        self.provider._dropbox_sync_signers(
            self.transaction,
            signature_request,
        )

        self.signer_1.invalidate_recordset(
            [
                "provider_sign_state",
                "identity_status",
                "identity_method",
                "provider_signer_ref",
                "provider_transaction_id",
                "signed_on",
            ]
        )

        self.assertEqual(self.signer_1.provider_sign_state, "signed")
        self.assertEqual(self.signer_1.identity_status, "verified")
        self.assertEqual(self.signer_1.identity_method, "eid")
        self.assertEqual(self.signer_1.provider_signer_ref, "sig-1")
        self.assertEqual(self.signer_1.provider_transaction_id, self.transaction)
        self.assertTrue(self.signer_1.signed_on)
