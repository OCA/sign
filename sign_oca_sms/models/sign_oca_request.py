# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models, fields, _
from odoo.exceptions import ValidationError
# from odoo.addons.website.tools import text_from_html  #for v16



class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    def get_sms_message(self, signer,  message, link):
        message = "Hello %s, %s has requested your signature on the following documents: %s. %s" %(signer.display_name, self.create_uid.name, link, message)
        return message

    def action_send_sms(self, sign_now=False, message=""):
        self.ensure_one()
        if self.state != "draft":
            return
        self._set_action_log("validate")
        self.state = "sent"
        if any(not signer.phone_field for signer in self.signer_ids):
            raise ValidationError(_(
                "Please Select the Signer's Phone"
                ))
        for signer in self.signer_ids:
            signer._portal_ensure_token()
            if sign_now and signer.partner_id == self.env.user.partner_id:
                continue
            
            link = self.get_base_url()+signer.access_url
            message = self.env["ir.fields.converter"].text_from_html(message)
            message = self.get_sms_message(signer, message, link)

            composer = self.env['sms.composer'].with_context(
                default_composition_mode='comment',
                default_res_id=signer.partner_id.id,
                default_res_model='res.partner',
                default_template_id=False

            ).create({
                'body': message,
                'number_field_name': signer.phone_field,

            })
            
            composer.action_send_sms()

class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    phone_field = fields.Char()