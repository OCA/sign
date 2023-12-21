# Copyright 2023 CreuBlana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaTemplateGenerate(models.TransientModel):

    _inherit = "sign.oca.template.generate"
    _description = "Generate a signature request"

    send_method = fields.Selection(
        selection=[("sms", "SMS"), ("email", "Email")], default="email"
    )

    def generate(self):
        if self.env.context.get("send_method", "") == "sms":
            request = self._generate()
            request.action_send_sms(sign_now=self.sign_now, message=self.message)
            return request.sign()
        return super().generate()

    def _generate_vals(self):
        res = super()._generate_vals()
        signers = res["signer_ids"]
        for signer in signers:
            signer_dict = signer[2]
            signer_id = self.signer_ids.filtered(
                lambda x: x.partner_id.id == signer_dict["partner_id"]
            )
            signer_dict["phone_field"] = (
                signer_id.phone.phone_field if signer_id.phone else ""
            )
        return res


class SignSignerPhone(models.TransientModel):
    _name = "sign.oca.signer.phone"

    number = fields.Char()
    partner_id = fields.Many2one("res.partner")
    phone_field = fields.Selection(selection=[("mobile", "Mobile"), ("phone", "Phone")])

    def name_get(self):
        result = []
        for rec in self:
            name = rec.phone_field + ": " + rec.number
            result.append((rec.id, name))
        return result

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

    phone = fields.Many2one("sign.oca.signer.phone")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.partner_id:
            signer_phone = self.env["sign.oca.signer.phone"]
            signer_phone._create_or_update_number(res.partner_id)
        return res

    @api.onchange("partner_id")
    def _get_phones(self):
        signer_phone = self.env["sign.oca.signer.phone"]
        if self.partner_id:
            signer_phone._create_or_update_number(self.partner_id)
