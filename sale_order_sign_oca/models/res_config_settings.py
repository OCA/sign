# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    group_sale_order_sign_oca = fields.Boolean(
        "Sale Order Sign Template",
        implied_group="sale_order_sign_oca.group_sale_order_sign_oca",
    )

    sale_order_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        related="company_id.sale_order_sign_oca_template_id",
        string="Sale Order Sign Oca Template",
        readonly=False,
    )

    sale_order_sign_oca_state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sale Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Sales Order Status For Sign Request",
        default=lambda self: self.env["res.company"]
        .browse(self.env.user.company_id.id)
        .sale_order_sign_oca_state,
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env["res.company"].browse(self.env.user.company_id.id)
        company.sale_order_sign_oca_state = self.sale_order_sign_oca_state
