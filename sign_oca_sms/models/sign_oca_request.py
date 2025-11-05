# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models
from odoo.exceptions import ValidationError


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    def get_sms_message(self, signer, requested_by_user, message, link):
        message = self.env._(
            "Hello %(display_name)s, %(requested_by_user)s has requested "
            "your signature on the following documents: %(link)s . %(message)s",
            display_name=signer.display_name,
            requested_by_user=requested_by_user,
            link=link,
            message=message,
        )
        return message

    def _send_sign_sms(
        self, message, link, signer_partner, requested_by_user, partner_phone_field
    ):
        if not message:
            message = "<p></p>"
        message = self.env["ir.fields.converter"].text_from_html(message)
        template = self.env.ref(
            "sign_oca_sms.sign_oca_sms_template_notification"
        ).with_context(
            **{
                "requested_by_user": requested_by_user,
                "message": message,
                "link": link,
            }
        )
        body = template._render_field("body", signer_partner.ids, compute_lang=True)[
            signer_partner.id
        ]

        composer = (
            self.env["sms.composer"]
            .with_context(
                default_composition_mode="comment",
                default_res_id=signer_partner.id,
                default_res_model="res.partner",
                default_template_id=False,
            )
            .create(
                {
                    "body": body,
                    "number_field_name": partner_phone_field,
                }
            )
        )

        composer.action_send_sms()

    def action_send_sms(self, sign_now=False, message=""):
        self.ensure_one()
        if self.state != "1_draft":
            return
        self._set_action_log("validate")
        self.state = "2_signed"
        if any(not signer.phone_field for signer in self.signer_ids):
            raise ValidationError(self.env._("Please Select the Signer's Phone"))
        for signer in self.signer_ids:
            signer._portal_ensure_token()
            if sign_now and signer.partner_id == self.env.user.partner_id:
                continue

            link = self.get_base_url() + signer.access_url
            self._send_sign_sms(
                message,
                link,
                signer.partner_id,
                self.create_uid.name,
                signer.phone_field,
            )


class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    phone_field = fields.Char()
