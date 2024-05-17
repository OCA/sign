# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    maintenance_equipment_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.maintenance_equipment_sign_oca_template_id",
        string="Sign Oca Template",
        readonly=False,
    )
