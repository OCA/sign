# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.mail.tests.common import mail_new_test_user


class Common(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.template = cls.env.ref(
            "hr_personal_equipment_request_sign_oca"
            ".sign_oca_template_personal_equipment_request_demo"
        )
        cls.company.personal_equipment_request_sign_oca_template_id = cls.template
        cls.warehouse = cls.env.ref("stock.warehouse0")

        cls.user = mail_new_test_user(
            cls.env,
            login="user_hr_personal_equipment_request_stock_sign_oca@test.com",
            groups=",".join(
                (
                    "hr.group_hr_user",
                    "stock.group_stock_user",
                )
            ),
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "user_id": cls.user.id,
            }
        )

        cls.personal_equipment_location = cls.env["stock.location"].create(
            {
                "name": "Employee Personal Equipment Virtual Location",
                "location_id": cls.warehouse.view_location_id.id,
                "usage": "transit",
                "is_personal_equipment_location": True,
            }
        )
        cls.resupply_location = cls.env["stock.location"].create(
            {
                "name": "Warehouse Test",
                "location_id": cls.warehouse.view_location_id.id,
            }
        )

        cls.route = cls.env["stock.route"].create(
            {
                "name": "Employee Personal Equipment Route",
                "product_categ_selectable": False,
                "product_selectable": True,
                "company_id": cls.company.id,
                "sequence": 10,
            }
        )

        cls.env["stock.rule"].create(
            {
                "name": "Employee Personal Equipment Rule",
                "route_id": cls.route.id,
                "location_src_id": cls.resupply_location.id,
                "location_dest_id": cls.personal_equipment_location.id,
                "action": "pull",
                "picking_type_id": cls.warehouse.int_type_id.id,
                "procure_method": "make_to_stock",
                "warehouse_id": cls.warehouse.id,
                "company_id": cls.company.id,
                "propagate_cancel": False,
            }
        )

        cls.ppe_product = cls.env["product.product"].create(
            {
                "name": "Test PPE Product",
                "is_ppe": True,
                "route_ids": [
                    fields.Command.set(cls.route.ids),
                ],
                "qty_available": 100,
                "is_storable": True,
            }
        )

        ppe_request_form = Form(
            cls.env["hr.personal.equipment.request"].with_user(cls.user.id)
        )
        ppe_request_form.employee_id = cls.employee
        ppe_request_form.location_id = cls.personal_equipment_location
        with ppe_request_form.line_ids.new() as line:
            line.product_id = cls.ppe_product
        cls.ppe_request = ppe_request_form.save()
