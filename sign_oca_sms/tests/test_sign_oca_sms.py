# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.sign_oca.tests.test_sign import TestSign


class TestSignSms(TestSign):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.signer.write(
            {
                "phone": "+507 833 8744",
                "mobile": "+254711123456",
            }
        )
        cls.SMS = cls.env["sms.sms"]
        cls.Mail = cls.env["mail.mail"]
        # clear old data
        cls.SMS.search([]).unlink()
        cls.Mail.search([]).unlink()

    def _create_sms_wizard(self, send_method="sms", phone_field="mobile"):
        partner = self.signer
        self.configure_template()
        wizard_form = Form(
            self.env["sign.oca.template.generate"].with_context(
                default_template_id=self.template.id,
                send_method=send_method,
            )
        )
        # Create phone record if needed
        if send_method in ("sms", "both"):
            phone_record = self.env["sign.oca.signer.phone"].create(
                {
                    "partner_id": partner.id,
                    "number": partner.phone
                    if phone_field == "phone"
                    else partner.mobile,
                    "phone_field": phone_field,
                }
            )
            with wizard_form.signer_ids.edit(0) as signer_line:
                signer_line.partner_id = partner
                signer_line.phone_id = phone_record
        else:
            with wizard_form.signer_ids.edit(0) as signer_line:
                signer_line.partner_id = partner

        return wizard_form.save()

    def test_wizard_generate_send_sms_only(self):
        sent_sms = self.SMS.search([])
        self.assertEqual(len(sent_sms), 0)
        wizard = self._create_sms_wizard(send_method="sms")
        action = wizard.generate()
        request = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(len(request.signer_ids), 1)
        self.assertEqual(request.signer_ids.partner_id, self.signer)
        self.assertEqual(request.signer_ids.phone_field, "mobile")
        sent_sms = self.SMS.search([])
        self.assertEqual(len(sent_sms), 1)
        self.assertEqual(sent_sms.number, self.signer.mobile)
        self.assertIn(self.signer.name, sent_sms.body)

    def test_wizard_generate_send_email_only(self):
        sent_mail = self.Mail.search([])
        self.assertEqual(len(sent_mail), 0)
        wizard = self._create_sms_wizard(send_method="email")
        action = wizard.generate()
        request = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(len(request.signer_ids), 1)
        self.assertFalse(
            request.signer_ids.phone_field, "Phone field should be empty for email-only"
        )
        sent_mail = self.Mail.search([])
        self.assertEqual(len(sent_mail), 1)

    def test_wizard_generate_send_both(self):
        sent_sms = self.SMS.search([])
        sent_mail = self.Mail.search([])
        self.assertEqual(len(sent_sms), 0)
        self.assertEqual(len(sent_mail), 0)
        wizard = self._create_sms_wizard(send_method="both")
        action = wizard.generate()
        # Verify SMS and Email were sent
        request = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(request.signer_ids.phone_field, "mobile")
        sent_sms = self.SMS.search([])
        sent_mail = self.Mail.search([])
        self.assertEqual(len(sent_sms), 1)
        self.assertEqual(len(sent_mail), 1)
