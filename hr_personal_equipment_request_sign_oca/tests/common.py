# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.mail.tests.common import mail_new_test_user


class Common(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_id = cls.env.company
        cls.template = cls.env.ref(
            "hr_personal_equipment_request_sign_oca"
            ".sign_oca_template_personal_equipment_request_demo"
        )

        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Test Partner 1",
            }
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        cls.ppe_product = cls.env["product.product"].create(
            {
                "name": "Test PPE Product",
                "is_ppe": True,
            }
        )

        cls.user_1 = mail_new_test_user(
            cls.env,
            login="user1@test.com",
            groups=",".join(("hr.group_hr_user",)),
            partner_id=cls.partner_1.id,
        )
        cls.user_2 = mail_new_test_user(
            cls.env,
            login="user2@test.com",
            groups=",".join(("hr.group_hr_user",)),
            partner_id=cls.partner_2.id,
        )

        cls.employee_1 = cls.env["hr.employee"].create(
            {
                "name": "Employee Test 1",
                "user_id": cls.user_1.id,
            }
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {
                "name": "Employee Test 2",
                "user_id": cls.user_2.id,
            }
        )

        ppe_request_1_form = Form(
            cls.env["hr.personal.equipment.request"].with_user(cls.user_1.id)
        )
        ppe_request_1_form.employee_id = cls.employee_1
        with ppe_request_1_form.line_ids.new() as line:
            line.product_id = cls.ppe_product
        cls.ppe_request_1 = ppe_request_1_form.save()
        ppe_request_2_form = Form(
            cls.env["hr.personal.equipment.request"].with_user(cls.user_2.id)
        )
        ppe_request_2_form.employee_id = cls.employee_2
        with ppe_request_2_form.line_ids.new() as line:
            line.product_id = cls.ppe_product
        cls.ppe_request_2 = ppe_request_2_form.save()
