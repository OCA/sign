# Copyright 2026 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from base64 import b64encode

from odoo.tests.common import TransactionCase


class SignOcaProviderCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_signer_1 = cls.env["res.partner"].create(
            {
                "name": "Signer One",
                "email": "signer1@example.com",
                "mobile": "+34600000001",
            }
        )

        cls.partner_signer_2 = cls.env["res.partner"].create(
            {
                "name": "Signer Two",
                "email": "signer2@example.com",
                "mobile": "+34600000002",
            }
        )

        cls.provider = cls.env["sign.oca.provider"].create(
            {
                "name": "Test Provider",
                "code": "test-provider",
                "provider_type": "dummy",
                "credential_ref": "test.provider.token",
            }
        )

        cls.env["ir.config_parameter"].sudo().set_param(
            "test.provider.token",
            "dummy-token",
        )

        cls.request = cls.env["sign.oca.request"].create(
            {
                "name": "Test Contract",
                "data": b64encode(b"%PDF-1.4\nTest document\n%%EOF"),
                "provider_id": cls.provider.id,
            }
        )

        cls.signer_1 = cls.env["sign.oca.request.signer"].create(
            {
                "request_id": cls.request.id,
                "partner_id": cls.partner_signer_1.id,
                "role_id": cls.env.ref("sign_oca.sign_role_employee").id,
            }
        )

        cls.signer_2 = cls.env["sign.oca.request.signer"].create(
            {
                "request_id": cls.request.id,
                "partner_id": cls.partner_signer_2.id,
                "role_id": cls.env.ref("sign_oca.sign_role_customer").id,
            }
        )
