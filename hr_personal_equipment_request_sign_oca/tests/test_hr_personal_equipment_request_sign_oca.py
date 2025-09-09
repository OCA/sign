# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from .common import Common


class TestHrPersonalEquipmentRequestSignOca(Common):
    def test_template_generate_multi_equipment_request(self):
        ppe_requests = self.ppe_request_1 + self.ppe_request_2
        wizard_form = Form(
            self.env["sign.oca.template.generate.multi"].with_context(
                default_model="hr.personal.equipment.request",
                active_ids=ppe_requests.ids,
            )
        )
        wizard_form.template_id = self.template
        action = wizard_form.save().generate()
        requests = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(requests), 2)

        sign_request_1 = requests.filtered(
            lambda x: x.personal_equipment_request_id == self.ppe_request_1
        )
        sign_request_2 = requests.filtered(
            lambda x: x.personal_equipment_request_id == self.ppe_request_2
        )
        self.assertEqual(self.partner_1, sign_request_1.mapped("signer_ids.partner_id"))
        self.assertEqual(self.partner_2, sign_request_2.mapped("signer_ids.partner_id"))

    def test_personal_equipment_request_create(self):
        self.company_id.personal_equipment_request_sign_oca_template_id = self.template
        request_3_form = Form(self.env["hr.personal.equipment.request"])
        request_3_form.employee_id = self.employee_1
        with request_3_form.line_ids.new() as line:
            line.product_id = self.ppe_product
        request_3 = request_3_form.save()

        self.assertEqual(
            self.partner_1,
            request_3.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(request_3.sign_request_count, 1)

    def test_personal_equipment_request_write(self):
        self.company_id.personal_equipment_request_sign_oca_template_id = self.template
        self.ppe_request_1.employee_id = False
        self.assertFalse(self.ppe_request_1.sign_request_ids)
        self.assertEqual(self.ppe_request_1.sign_request_count, 0)

        self.ppe_request_1.employee_id = self.employee_2.id
        self.assertEqual(
            self.partner_2,
            self.ppe_request_1.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(self.ppe_request_1.sign_request_count, 1)
