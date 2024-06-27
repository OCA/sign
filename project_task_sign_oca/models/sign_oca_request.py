# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Task",
        compute="_compute_task_id",
        readonly=True,
        store=True,
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        compute="_compute_project_id",
        compute_sudo=True,
        readonly=True,
        store=True,
    )

    @api.depends("record_ref")
    def _compute_task_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "project.task"
        ):
            item.task_id = item.record_ref.id

    @api.depends("record_ref")
    def _compute_project_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "project.task"
        ):
            task = self.env["project.task"].browse(item.record_ref.id)
            item.project_id = task.project_id
