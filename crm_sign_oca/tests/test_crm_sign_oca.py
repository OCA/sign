# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.base.tests.common import BaseCommon


class TestCRMSignOca(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.template = cls.env.ref("crm_sign_oca.sign_oca_template_crm_lead_demo")
        cls.crm_a = (
            cls.env["crm.lead"]
            .with_user(cls.env.uid)
            .create({"name": "Test CRM A", "user_id": cls.env.uid})
        )

    def test_action_send_signed_request(self):
        """Test that when a request is signed"""

        crm_role = self.env.ref("crm_sign_oca.role_crm_signer")

        sign_request = self.env["sign.oca.request"].create(
            {
                "name": "Signed CRM A.pdf",
                "record_ref": f"crm.lead,{self.crm_a.id}",
                "state": "0_sent",
                "signer_ids": [
                    (
                        0,
                        0,
                        {
                            "role_id": crm_role.id,
                            "partner_id": self.env.user.partner_id.id,
                        },
                    ),
                ],
            }
        )

        # Simulate signing
        for signer in sign_request.signer_ids:
            signer.signed_on = "2025-01-01 12:00:00"
        sign_request.state = "2_signed"

        sign_request.action_send_signed_request()

        self.assertEqual(
            sign_request.signer_id.partner_id.id, self.env.user.partner_id.id
        )
        self.assertEqual(sign_request.state, "2_signed")
        self.assertEqual(
            f"{sign_request.record_ref._name},{sign_request.record_ref.id}",
            f"crm.lead,{self.crm_a.id}",
        )

    def test_action_send_signed_request_state_not_signed(self):
        """Test that crm is not updated if request is not signed."""
        sign_request = self.env["sign.oca.request"].create(
            {
                "name": "Test.pdf",
                "record_ref": f"crm.lead,{self.crm_a.id}",
                "state": "0_sent",  # Not signed
            }
        )
        sign_request.action_send_signed_request()

        self.assertFalse(sign_request.signer_id)
