# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestProjectTaskSignOca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_id = cls.env.company
        cls.template = cls.env.ref(
            "project_task_sign_oca.sign_oca_template_project_task_demo"
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
        cls.project_a = cls.env["project.project"].create(
            {
                "name": "Test Project A",
            }
        )
        cls.project_b = cls.env["project.project"].create(
            {
                "name": "Test Project B",
            }
        )
        cls.task_a = cls.env["project.task"].create(
            {
                "name": "Test Task A",
                "project_id": cls.project_a.id,
                "partner_id": cls.customer_a.id,
                "company_id": cls.company_id.id,
            }
        )
        cls.task_b = cls.env["project.task"].create(
            {
                "name": "Test Task B",
                "project_id": cls.project_b.id,
                "partner_id": cls.customer_b.id,
                "company_id": cls.company_id.id,
            }
        )

    def test_template_generate_multi_project_task(self):
        tasks = self.task_a + self.task_b
        wizard_form = Form(
            self.env["sign.oca.template.generate.multi"].with_context(
                default_model="project.task", active_ids=tasks.ids
            )
        )
        wizard_form.template_id = self.template
        action = wizard_form.save().generate()
        requests = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(requests), 2)
        request_a = requests.filtered(lambda x: x.task_id == self.task_a)
        request_b = requests.filtered(lambda x: x.task_id == self.task_b)
        self.assertIn(self.customer_a, request_a.mapped("signer_ids.partner_id"))
        self.assertIn(self.customer_b, request_b.mapped("signer_ids.partner_id"))

    def test_project_task_create(self):
        self.company_id.project_task_sign_oca_template_id = self.template
        task_c = self.env["project.task"].create(
            {
                "name": "Test Task C",
                "project_id": self.project_a.id,
                "partner_id": self.customer_a.id,
                "company_id": self.company_id.id,
            }
        )
        self.assertIn(
            self.customer_a,
            task_c.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(task_c.sign_request_count, 1)
        self.assertEqual(task_c.sign_request_ids[0].task_id, task_c)
        self.assertEqual(task_c.sign_request_ids[0].project_id, self.project_a)

    def test_project_task_write(self):
        self.company_id.project_task_sign_oca_template_id = self.template
        task_d = self.env["project.task"].create(
            {
                "name": "Test Task D",
                "project_id": self.project_a.id,
                "partner_id": False,
                "company_id": self.company_id.id,
            }
        )
        self.assertFalse(task_d.sign_request_ids)
        self.assertEqual(task_d.sign_request_count, 0)
        task_d.write({"partner_id": self.customer_a.id})
        self.assertIn(
            self.customer_a,
            task_d.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(task_d.sign_request_count, 1)
        task_d.write({"partner_id": self.customer_b.id})
        self.assertIn(
            self.customer_b,
            task_d.sign_request_ids.mapped("signer_ids.partner_id"),
        )
        self.assertEqual(task_d.sign_request_count, 2)
