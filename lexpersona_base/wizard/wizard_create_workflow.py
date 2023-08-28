# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardSignatureType(models.TransientModel):
    _name = "wizard.signature.type"
    _description = "Signature Types available"

    name = fields.Char(string="Name", readonly=True)
    lexpersona_cop = fields.Char("Consent Page ID", readonly=True)


class WizardSignatureProfile(models.TransientModel):
    _name = "wizard.signature.profile"
    _description = "Signature Profiles available"

    name = fields.Char(string="Name", readonly=True)
    lexpersona_sip = fields.Char("Signature Profile ID", readonly=True)


class WizardContact(models.TransientModel):
    _name = "wizard.contact"
    _description = "Contact who will sign, validate or observe the documents"

    wizard_id = fields.Many2one(
        "wizard.create.workflow",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    email = fields.Char("Email", readonly=True)
    mobile = fields.Char("mobile", readonly=True)
    lexpersona_ref = fields.Char("LexPersona ID", readonly=True)
    action = fields.Selection(
        selection=[
            ("signature", "Signer"),
            ("approval", "Approbator"),
            ("watch", "Watcher"),
        ],
        string="Action to do",
        help="Choose what you want for that contact to be",
    )
    signature_type_id = fields.Many2one(
        "wizard.signature.type",
        string="Signature Type",
    )
    sequence = fields.Integer(string="Sequence", default=10)


class WizardDocument(models.TransientModel):
    _name = "wizard.document"
    _description = "Document to be signed or attached"

    wizard_id = fields.Many2one(
        "wizard.create.workflow",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Document",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    action = fields.Selection(
        selection=[
            ("tobesigned", "To be Signed/Approved"),
            ("attachment", "Attachment"),
        ],
        string="Action",
        help="Choose what you want for that document. \
        Attachments will not be signed.",
    )
    signature_profile_id = fields.Many2one(
        "wizard.signature.profile",
        string="Signature Profile",
    )


class WizardCreateWorkflow(models.TransientModel):
    _name = "wizard.create.workflow"
    _description = "Wizard to create Lex Persona workflows"

    # TODO
    # """ Check some preconditions before the wizard executes. """
    # """ If the active_model already has a lexpersona_wkf, \
    # we should warn the user that a workflow has already been launched \
    # and this will erase previous workflow. """
    # raise Warning(_('A workflow has already been launched for this record. \
    # If you confirm, this will overwrite the previously signed documents.'))

    def _get_signature_info(self):
        # Fill up wizard_signature_type
        url = "/consentPages"
        cop_response = self.env["lexpersona.api"].api_get(url)
        if cop_response.json()["items"]:
            self.env["wizard.signature.type"].search([]).unlink()
            for item in cop_response.json()["items"]:
                if item["stepType"] == "signature":
                    self.env["wizard.signature.type"].create(
                        {"name": item["name"], "lexpersona_cop": item["id"]}
                    )
        # Fill up wizard_signature_profile
        url = "/signatureProfiles"
        sip_response = self.env["lexpersona.api"].api_get(url)
        if sip_response.json()["items"]:
            self.env["wizard.signature.profile"].search([]).unlink()
            for item in sip_response.json()["items"]:
                if item["documentType"] == "pdf":
                    self.env["wizard.signature.profile"].create(
                        {"name": item["name"], "lexpersona_sip": item["id"]}
                    )

    def _default_document_ids(self):
        # We have to take all the pdf documents attached to the active record
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id", [])
        document_changes = []
        documents = self.env["ir.attachment"].search(
            [
                ("res_model", "=", active_model),
                ("res_id", "=", active_id),
                ("type", "=", "binary"),
                ("mimetype", "=", "application/pdf"),
            ]
        )
        for document in documents:
            document_changes.append(
                (
                    0,
                    0,
                    {
                        "attachment_id": document.id,
                    },
                )
            )

        return document_changes

    def _default_contact_ids(self):
        self._get_signature_info()
        # We have to take the active object followers and the env user
        active_model = self.env.context.get("active_model")
        object_id = self.env[active_model].browse(self.env.context.get("active_id", []))
        # First we put the user in the list of dicts
        user_dict = {
            "partner_id": self.env.user.partner_id.id,
            "email": self.env.user.partner_id.email or "",
            "mobile": self.env.user.partner_id.mobile or "",
            "lexpersona_ref": self.env.user.lexpersona_ref,
        }
        contact_changes = [(0, 0, user_dict)]
        # Then we add followers if not already in the list of dicts
        followers = object_id.message_follower_ids
        for follower in followers:
            partner_dict = {
                "partner_id": follower.partner_id.id,
                "email": follower.partner_id.email or "",
                "mobile": follower.partner_id.mobile or "",
                "lexpersona_ref": (
                    follower.partner_id.user_ids
                    and (
                        self.env.ref("base.group_user")
                        in follower.partner_id.user_ids[0].groups_id
                    )
                )
                and follower.partner_id.user_ids[0].lexpersona_ref
                or "",
            }
            # We add contact if not already in the list
            if (0, 0, partner_dict) not in contact_changes:
                contact_changes.append((0, 0, partner_dict))
        return contact_changes

    document_ids = fields.One2many(
        "wizard.document",
        inverse_name="wizard_id",
        string="Documents",
        help="Tick if documents has to be signed or just attached",
        default=_default_document_ids,
    )
    contact_ids = fields.One2many(
        "wizard.contact",
        inverse_name="wizard_id",
        string="Contacts",
        help="Tick if contacts has to sign, validate or just be notified",
        default=_default_contact_ids,
    )

    def get_steps(self):
        # Add steps
        steps = []
        contacts = self.contact_ids.filtered(lambda c: c.action is not False).sorted(
            key=lambda c: c.sequence
        )
        for contact in contacts:
            recipients = []
            if contact.action == "approval":
                if contact.lexpersona_ref:
                    recipients.append({"userId": contact.lexpersona_ref})
                else:
                    recipients.append(
                        {
                            "email": contact.email,
                            "firstName": contact.partner_id.firstname or "",
                            "lastName": contact.partner_id.lastname or "",
                            "country": contact.partner_id.country_id.code or "",
                        }
                    )
                steps.append(
                    {"stepType": "approval", "maxInvites": 5, "recipients": recipients}
                )

            if contact.action == "signature":
                if contact.lexpersona_ref:
                    recipients.append(
                        {
                            "consentPageId": contact.signature_type_id.lexpersona_cop,
                            "userId": contact.lexpersona_ref,
                        }
                    )
                else:
                    recipients.append(
                        {
                            "consentPageId": contact.signature_type_id.lexpersona_cop,
                            "email": contact.email,
                            "firstName": contact.partner_id.firstname or "",
                            "lastName": contact.partner_id.lastname or "",
                            "phoneNumber": contact.mobile or "",
                            "country": contact.partner_id.nationality_id
                            and contact.partner_id.nationality_id.code
                            or contact.partner_id.country_id.code
                            or "",
                        }
                    )
                steps.append(
                    {
                        "stepType": "signature",
                        "maxInvites": 5,
                        "recipients": recipients,
                    }
                )
        return steps

    def get_watchers(self):
        # Add watchers
        user_watchers = self.contact_ids.filtered(
            lambda c: c.action == "watch" and c.lexpersona_ref
        )
        guest_watchers = self.contact_ids.filtered(
            lambda c: c.action == "watch" and not c.lexpersona_ref
        )
        watchers = []
        for guest in guest_watchers:
            watchers.append(
                {
                    "email": guest.email,
                    "firstName": guest.partner_id.firstname or "",
                    "lastName": guest.partner_id.lastname or "",
                    "country": guest.partner_id.country_id.code or "",
                    "notifiedEvents": [
                        "recipientRefused",
                        "recipientFinished",
                        "workflowStarted",
                        "workflowStopped",
                        "workflowFinished",
                        "workflowFinishedDownloadLink",
                    ],
                }
            )
        for user in user_watchers:
            watchers.append(
                {
                    "userId": user.lexpersona_ref,
                    "notifiedEvents": [
                        "recipientRefused",
                        "recipientFinished",
                        "workflowStarted",
                        "workflowStopped",
                        "workflowFinished",
                        "workflowFinishedDownloadLink",
                    ],
                }
            )
        return watchers

    def open_viewer(self, url):
        if url:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": "%s" % url,
            }
        else:
            raise UserError(_("There is no URL for the viewer."))

    def get_layout(self):
        return []

    def get_payload_parts(self, doc, blob):
        payload = {
            "parts": [
                {
                    "filename": doc.attachment_id.name,
                    "contentType": doc.attachment_id.mimetype,
                    "blobs": [blob],
                }
            ]
        }
        return payload

    def post_document(self, doc, url_blob):
        # This function can be inherited in order to place the signature fields
        payload_blob = doc.attachment_id.raw
        blob_response = (
            self.env["lexpersona.api"]
            .with_context({"content-type": "application/pdf", "post_param": "data"})
            .api_post(url_blob, payload_blob)
        )
        blob_id = blob_response.json()["id"]
        params = (
            "?createDocuments=true&ignoreAttachments=false&\
            unzip=false&signatureProfileId="
            + (
                doc.signature_profile_id.lexpersona_sip
                and doc.signature_profile_id.lexpersona_sip
                or ""
            )
        )
        url_parts = url_blob + "/parts" + params
        payload_parts = self.get_payload_parts(doc, blob_id)
        parts_response = self.env["lexpersona.api"].api_post(url_parts, payload_parts)
        doc.attachment_id.lexpersona_ref = parts_response.json()["documents"][0]["id"]
        doc.attachment_id.state = "tobesigned"

    def create_workflow(self):
        self.ensure_one()
        if not self.document_ids.filtered(lambda c: c.action == "tobesigned"):
            raise UserError(
                _(
                    "You must have at least one document to be approved or \
                to be signed."
                )
            )
        if not self.contact_ids.filtered(
            lambda c: c.action in ("approval", "signature")
        ):
            raise UserError(_("You must have at least one contact to approve or sign."))
        if self.contact_ids.filtered(lambda c: c.action and not c.email):
            raise UserError(_("You must have an email address for your contacts."))

        # Create Workflow
        url = "/users/" + self.env.user.lexpersona_ref + "/workflows"
        active_model = self.env.context.get("active_model")
        payload = {
            "name": self.env[active_model]._description
            + "-"
            + self.env[active_model].browse(self.env.context.get("active_id", [])).name,
            "layoutId": self.get_layout(),
            "steps": self.get_steps(),
            "watchers": self.get_watchers(),
        }
        wkf_response = self.env["lexpersona.api"].api_post(url, payload)
        url_wkf = "/workflows/" + wkf_response.json()["id"]
        # We save the workflow id in the active record
        object_id = self.env[active_model].browse(self.env.context.get("active_id", []))
        object_id.lexpersona_wkf = wkf_response.json()["id"]

        # Add documents with blob and parts
        for doc in self.document_ids.filtered(lambda c: c.action is not False):
            self.post_document(doc, url_wkf + "/blobs")
        # Open Workflow page
        fenuasign_url = "https://sign.fenuasign.com/#" + url_wkf
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": "%s" % fenuasign_url,
        }
