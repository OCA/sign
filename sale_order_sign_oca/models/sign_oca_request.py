# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        compute="_compute_sale_order_id",
        readonly=True,
        store=True,
    )

    @api.depends("record_ref")
    def _compute_sale_order_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "sale.order"
        ):
            item.sale_order_id = item.record_ref.id
