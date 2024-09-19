# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_order_sign_oca_template_id = fields.Many2one(
        comodel_name="sign.oca.template",
        domain="[('model_id.model', '=', 'sale.order')]",
        string="Sale Order Sign Oca Template",
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
    )
