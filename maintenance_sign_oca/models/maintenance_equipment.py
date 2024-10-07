# Copyright 2023-2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    # This field is stored as a help to filter by.
    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="maintenance_equipment_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        compute_sudo=True,
        store=True,
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        request_data = self.env["sign.oca.request"].read_group(
            [("maintenance_equipment_id", "in", self.ids)],
            ["maintenance_equipment_id"],
            ["maintenance_equipment_id"],
        )
        mapped_data = {
            x["maintenance_equipment_id"][0]: x["maintenance_equipment_id_count"]
            for x in request_data
        }
        for item in self:
            item.sign_request_count = mapped_data.get(item.id, 0)

    def action_view_sign_requests(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        ctx = dict(self.env.context)
        ctx.update(
            {
                "default_maintenance_equipment_id": self.id,
                "search_default_maintenance_equipment_id": self.id,
            }
        )
        result["context"] = ctx
        return result

    def _process_generate_sign_oca_request(self, data):
        """Generate request from template if owner has changed."""
        request_model = self.env["sign.oca.request"].sudo()
        for item in self.filtered("owner_user_id"):
            sign_template = item.company_id.maintenance_equipment_sign_oca_template_id
            old_owner_user_id = data[item.id] if item.id in data else False
            if sign_template and item.owner_user_id != old_owner_user_id:
                # Apply sudo because the user who creates the record may not have
                # permissions on sign.oca.template
                sign_template = sign_template.sudo()
                request_model.create(
                    sign_template._prepare_sign_oca_request_vals_from_record(item)
                )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if any(item.owner_user_id for item in res):
            res._process_generate_sign_oca_request({})
        return res

    def write(self, vals):
        owners = {}
        for item in self:
            owners[item.id] = item.owner_user_id
        res = super().write(vals)
        # Fields to be taken into account when trying to create a sign request.
        # We don't need to take into account only the owner_user_id field because
        # if you have installed hr_maintenance module is a compute field and the
        # employee_id field will be taken into account.
        if any(vals.get(fname) for fname in ["owner_user_id", "employee_id"]):
            self._process_generate_sign_oca_request(owners)
        return res
