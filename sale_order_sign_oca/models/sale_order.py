# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="sale_order_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        compute_sudo=True,
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        for sale_order in self:
            sale_order.sign_request_count = len(sale_order.sign_request_ids)

    def action_view_sign_requests(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        return result

    def _generate_sign_oca_request(self):
        sign_request_obj = self.env["sign.oca.request"].sudo()
        for sale_order in self:
            sign_template = sale_order.company_id.sale_order_sign_oca_template_id
            if sign_template:
                sign_template = sign_template.sudo()
                request = sign_request_obj.create(
                    sign_template._prepare_sign_oca_request_vals_from_record(sale_order)
                )
                request.action_send()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if self.env.user.has_group("sale_order_sign_oca.group_sale_order_sign_oca"):
            for sale_order in res:
                if (
                    sale_order.partner_id
                    and sale_order.company_id.sale_order_sign_oca_template_id
                    and sale_order.company_id.sale_order_sign_oca_state == "draft"
                ):
                    sale_order._generate_sign_oca_request()
        return res

    def write(self, vals):
        old_partner_id = self.partner_id
        new_partner_id = vals.get("partner_id")
        old_state = self.state
        new_state = vals.get("state")
        res = super().write(vals)
        if self.env.user.has_group("sale_order_sign_oca.group_sale_order_sign_oca"):
            if (
                new_state
                and new_state != old_state
                and self.company_id.sale_order_sign_oca_template_id
                and self.company_id.sale_order_sign_oca_state == new_state
            ):
                self._generate_sign_oca_request()
                return res

            if (
                new_partner_id
                and new_partner_id != old_partner_id
                and self.company_id.sale_order_sign_oca_template_id
                and self.company_id.sale_order_sign_oca_state == self.state
            ):
                self._generate_sign_oca_request()
                return res
