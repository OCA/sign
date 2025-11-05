# Copyright 2023 CreuBlana
# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaTemplateGenerate(models.TransientModel):
    _inherit = "sign.oca.template.generate"
    _description = "Generate a signature request"

    send_method = fields.Selection(
        selection=[("sms", "SMS"), ("email", "Email"), ("both", "Email & SMS")],
        default="email",
    )

    def generate(self):
        send_method = self.env.context.get("send_method")
        send_methods = dict(self._fields["send_method"].selection)
        if not send_method or send_method not in send_methods:
            return super().generate()

        self.send_method = send_method
        send_method_msg = send_methods[send_method]
        request = self._generate()
        if send_method == "email" or self.sign_now:
            request.action_send(sign_now=self.sign_now, message=self.message)
        elif send_method == "sms":
            request.action_send_sms(sign_now=self.sign_now, message=self.message)
        else:
            request.action_send(sign_now=self.sign_now, message=self.message)
            request.state = "1_draft"
            request.action_send_sms(sign_now=self.sign_now, message=self.message)
        request.message_post(body=f"Sign request sent via {send_method_msg}")
        return request.sign()

    def _generate_vals(self):
        res = super()._generate_vals()
        for signer in res["signer_ids"]:
            signer_dict = signer[2]
            partner_id = signer_dict.get("partner_id")
            signer_id = self.signer_ids.filtered(
                lambda x, pid=partner_id: x.partner_id.id == pid
            )
            signer_dict["phone_field"] = (
                signer_id.phone_id.phone_field if signer_id.phone_id else ""
            )
        return res


class SignSignerPhone(models.TransientModel):
    _name = "sign.oca.signer.phone"
    _description = "Sign Signer Phone"
    _rec_names_search = ["number"]

    display_name = fields.Char(
        compute="_compute_display_name", search="_search_display_name"
    )
    number = fields.Char()
    partner_id = fields.Many2one("res.partner")
    phone_field = fields.Selection(selection=[("mobile", "Mobile"), ("phone", "Phone")])

    @api.depends("phone_field", "number")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.phone_field + ": " + rec.number

    def _create_or_update_number(self, partner_id):
        phone_fields = ["mobile", "phone"]
        for phone_field in phone_fields:
            record = self.search(
                [
                    ("partner_id", "=", partner_id.id),
                    ("phone_field", "=", phone_field),
                ]
            )
            partner_num = getattr(partner_id, phone_field)
            if not record and partner_num:
                self.create(
                    {
                        "partner_id": partner_id.id,
                        "number": partner_num,
                        "phone_field": phone_field,
                    }
                )
            elif record.number != partner_num:
                record.number = partner_num
            elif record.number and not partner_num:
                record.unlink()


class SignOcaTemplateGenerateSigner(models.TransientModel):
    _inherit = "sign.oca.template.generate.signer"

    phone_id = fields.Many2one("sign.oca.signer.phone")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if rec.partner_id:
                signer_phone = self.env["sign.oca.signer.phone"]
                signer_phone._create_or_update_number(rec.partner_id)
        return res

    @api.onchange("partner_id")
    def _get_phones(self):
        signer_phone = self.env["sign.oca.signer.phone"]
        if self.partner_id:
            signer_phone._create_or_update_number(self.partner_id)
