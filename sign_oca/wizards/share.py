# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SignRequestShareWizard(models.TransientModel):
    _name = "sign.request.share.wizard"
    _description = "Share Sign Request Wizard"

    request_id = fields.Many2one("sign.oca.request", required=True)
    signer_ids = fields.One2many(
        "sign.oca.request.signer",
        related="request_id.signer_ids",
        string="Signers",
    )
