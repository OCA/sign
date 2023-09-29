# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaRole(models.Model):
    _name = "sign.oca.role"
    _description = "Sign Role"

    name = fields.Char(required=True)
    domain = fields.Char(required=True, default=[])
    partner_type = fields.Selection(
        selection=[
            ("empty", "Empty"),
            ("default", "Default"),
            ("expression", "Expression"),
        ],
        string="Partner type",
        required=True,
        default="empty",
    )
    default_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Default partner"
    )
    expression_partner = fields.Char(
        string="Expression", help="Example: ${object.partner_id.id}"
    )

    @api.onchange("partner_type")
    def _onchange_partner_type(self):
        for item in self:
            if item.partner_type == "empty":
                item.default_partner_id = False
                item.expression_partner = False
            elif item.partner_type == "default":
                item.expression_partner = False
            elif item.partner_type == "expression":
                item.default_partner_id = False

    def _get_partner_from_record(self, record):
        partner = self.default_partner_id or False
        if self.partner_type == "expression" and record:
            # TODO: In 15.0 change to _render_template() inline-template
            res = self.env["mail.render.mixin"]._render_template_jinja(
                self.expression_partner, record._name, record.ids
            )[record.id]
            partner = int(res) if res else False
        return partner
