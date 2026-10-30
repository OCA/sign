# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import HttpCase

try:
    import fitz
except ImportError:
    fitz = None


@tagged("post_install", "-at_install")
class TestSignGeneration(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.report = cls.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "sign_oca.test_report_template",
            }
        )
        cls.report_view = cls.env["ir.ui.view"].create(
            {
                "name": "Test Report Template",
                "type": "qweb",
                "key": "sign_oca.test_report_template",
                "arch": """<t t-name="sign_oca.test_report_template">
                <t t-call="web.html_container">
                    <t t-foreach="docs" t-as="doc">
                        <t t-call="web.external_layout">
                            <t t-foreach="docs" t-as="doc">
                                <div class="test_aux" style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);">
                                    ##SIGN_OCA##sign_oca.sign_field_name##sign_oca.sign_role_customer
                                </div>
                            </t>
                        </t>
                    </t>
                </t>
            </t>""",  # noqa: E501
            }
        )

    def setUp(self):
        super().setUp()
        if fitz is None:
            self.skipTest("PyMuPDF is not installed, skipping test.")

    def test_generate_signature_request(self):
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        request = self.env["sign.oca.request"]._generate_signature_request(
            self.partner,
            pdf,
            {self.env.ref("sign_oca.sign_role_customer").id: self.partner.id},
        )
        self.assertEqual(request.state, "0_sent")
        signer = request.signer_ids[0]
        self.assertEqual(signer.partner_id, self.partner)
        self.assertEqual(1, len(request.signatory_data))

    def test_generate_signature_request_no_send(self):
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        request = self.env["sign.oca.request"]._generate_signature_request(
            self.partner,
            pdf,
            {self.env.ref("sign_oca.sign_role_customer").id: self.partner.id},
            auto_send=False,
        )
        self.assertEqual(request.state, "1_draft")
        signer = request.signer_ids[0]
        self.assertEqual(signer.partner_id, self.partner)
        self.assertEqual(1, len(request.signatory_data))

    def test_generate_signature_request_with_2_fields(self):
        self.env["ir.ui.view"].create(
            {
                "name": "Test Report Template 2 Fields",
                "type": "qweb",
                "inherit_id": self.report_view.id,
                "arch": """<xpath expr="//div[hasclass('test_aux')]" position="after">
                <div class="test_aux" style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);">
                    ##SIGN_OCA##sign_oca.sign_field_email##sign_oca.sign_role_customer
                </div>
                </xpath>""",  # noqa: E501
            }
        )
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        request = self.env["sign.oca.request"]._generate_signature_request(
            self.partner,
            pdf,
            {self.env.ref("sign_oca.sign_role_customer").id: self.partner.id},
        )
        self.assertEqual(request.state, "0_sent")
        signer = request.signer_ids[0]
        self.assertEqual(signer.partner_id, self.partner)
        self.assertEqual(2, len(request.signatory_data))

    def test_generate_signature_request_with_wrong_role(self):
        self.env["ir.ui.view"].create(
            {
                "name": "Test Report Template 2 Fields",
                "type": "qweb",
                "inherit_id": self.report_view.id,
                "arch": """<xpath expr="//div[hasclass('test_aux')]" position="after">
                <div class="test_aux" style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);">
                    ##SIGN_OCA##base.group_no_one##sign_oca.sign_role_customer
                </div>
                </xpath>""",  # noqa: E501
            }
        )
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        with self.assertRaises(UserError):
            self.env["sign.oca.request"]._generate_signature_request(
                self.partner,
                pdf,
                {self.env.ref("sign_oca.sign_role_customer").id: self.partner.id},
            )

    def test_generate_signature_request_with_wrong_field(self):
        self.env["ir.ui.view"].create(
            {
                "name": "Test Report Template 2 Fields",
                "type": "qweb",
                "inherit_id": self.report_view.id,
                "arch": """<xpath expr="//div[hasclass('test_aux')]" position="after">
                <div class="test_aux" style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);">
                    ##SIGN_OCA##sign_oca.sign_field_email##base.group_no_one
                </div>
                </xpath>""",  # noqa: E501
            }
        )
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        with self.assertRaises(UserError):
            self.env["sign.oca.request"]._generate_signature_request(
                self.partner,
                pdf,
                {self.env.ref("sign_oca.sign_role_customer").id: self.partner.id},
            )

    def test_generate_signature_request_with_integer(self):
        self.env["ir.ui.view"].create(
            {
                "name": "Test Report Template 2 Fields",
                "type": "qweb",
                "inherit_id": self.report_view.id,
                "arch": f"""<xpath expr="//div[hasclass('test_aux')]" position="after">
                <div class="test_aux" style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);">
                    ##SIGN_OCA##{self.env.ref('sign_oca.sign_field_email').id}##{self.env.ref('sign_oca.sign_role_employee').id}
                </div>
                </xpath>""",  # noqa: E501
            }
        )
        pdf, _ = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render(self.report.report_name, [self.partner.id])
        )
        request = self.env["sign.oca.request"]._generate_signature_request(
            self.partner,
            pdf,
            {
                self.env.ref("sign_oca.sign_role_customer").id: self.partner.id,
                self.env.ref("sign_oca.sign_role_employee").id: self.partner.id,
            },
        )
        self.assertEqual(len(request.signer_ids), 2)
        self.assertTrue(
            any(
                request.signatory_data[field_data]["field_id"]
                == self.env.ref("sign_oca.sign_field_email").id
                for field_data in request.signatory_data
            )
        )
