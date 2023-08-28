# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import _, api, fields, models


class IrAttachment(models.Model):
    _inherit = ["ir.attachment"]

    state = fields.Selection(
        selection=[
            ("standard", "Standard"),
            ("tobesigned", "To be Signed"),
            ("signed", "Signed"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        tracking=3,
        default="standard",
    )
    lexpersona_ref = fields.Char(string="Lex Persona Doc ID")

    def _send_sign_notification(self, attachment):
        self.ensure_one()
        active_record = self.env[attachment.res_model].browse(attachment.res_id)
        note = self.env.ref("mail.mt_comment")
        template = self.env.ref("lexpersona_base.sign_notification_template", False)
        partners = active_record.message_follower_ids.partner_id
        active_record.with_context(force_send=True).message_post_with_view(
            template,
            values={"record": active_record},
            subject=_(
                "The documents have been signed in %s", active_record.display_name
            ),
            subtype_id=note.id,
            email_layout_xmlid="mail.mail_notification_light",
            partner_ids=[(6, 0, partners.ids)],
        )

    @api.model
    def _retrieve_documents(self):
        notified_workflows = []
        for attachment in (
            self.env["ir.attachment"]
            .search([])
            .filtered(lambda d: d.state == "tobesigned")
        ):
            url_doc = "/documents/" + attachment.lexpersona_ref
            doc_response = self.env["lexpersona.api"].api_get(url_doc)
            workflow = doc_response.json()["workflowId"]
            part_hash = bytes.hex(
                base64.b64decode(doc_response.json()["parts"][0]["hash"].encode())
            )
            url_wkf = "/workflows/" + workflow
            wkf_response = self.env["lexpersona.api"].api_get(url_wkf)
            if wkf_response.json()["workflowStatus"] == "finished":
                url_part = url_doc + "/parts/" + part_hash
                part_response = self.env["lexpersona.api"].api_get(url_part)
                attachment.raw = part_response.content
                attachment.state = "signed"
                attachment.name = "signed" + attachment.name
                # On notifie la signature dans l'objet
                if workflow not in notified_workflows:
                    attachment._send_sign_notification(attachment)
                    notified_workflows.append(workflow)
