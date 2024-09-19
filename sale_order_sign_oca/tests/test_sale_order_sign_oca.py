# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestSaleOrderSignOca(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_id = cls.env.company
        cls.template = cls.env.ref(
            "sale_order_sign_oca.sign_oca_template_sale_order_demo"
        )
        cls.customer_a = cls.env["res.partner"].create(
            {
                "name": "Test Customer A",
            }
        )
        cls.customer_b = cls.env["res.partner"].create(
            {
                "name": "Test Customer B",
            }
        )
        cls.sale_order_a = cls.env["sale.order"].create(
            {
                "name": "Test Sale Order A",
                "partner_id": cls.customer_a.id,
                "company_id": cls.company_id.id,
            }
        )
        cls.sale_order_b = cls.env["sale.order"].create(
            {
                "name": "Test Sale Order B",
                "partner_id": cls.customer_b.id,
                "company_id": cls.company_id.id,
            }
        )
        cls.ConfigSettings = cls.env["res.config.settings"]
        config = cls.ConfigSettings.create({})
        config.sale_order_sign_oca_template_id = cls.template
        config.sale_order_sign_oca_state = "draft"
        config.group_sale_order_sign_oca = True
        config.set_values()

    def test_sale_order_create(self):
        sale_order_c = self.env["sale.order"].create(
            {
                "name": "Test Sale Order C",
                "partner_id": self.customer_a.id,
                "company_id": self.company_id.id,
            }
        )
        self.assertIn(
            self.customer_a,
            sale_order_c.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(sale_order_c.sign_request_count, 1)
        self.assertEqual(sale_order_c.sign_request_ids[0].sale_order_id, sale_order_c)

    def test_sale_order_write(self):
        customer_c = self.env["res.partner"].create(
            {
                "name": "Test Customer C",
            }
        )

        sale_order_d = self.env["sale.order"].create(
            {
                "name": "Test Sale Order D",
                "partner_id": customer_c.id,
                "company_id": self.company_id.id,
            }
        )
        self.assertTrue(sale_order_d.sign_request_ids)
        self.assertEqual(sale_order_d.sign_request_count, 1)
        sale_order_d.write({"partner_id": self.customer_a.id})
        self.assertIn(
            self.customer_a,
            sale_order_d.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(sale_order_d.sign_request_count, 2)
        sale_order_d.write({"partner_id": self.customer_b.id})
        self.assertIn(
            self.customer_b,
            sale_order_d.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(sale_order_d.sign_request_count, 3)
