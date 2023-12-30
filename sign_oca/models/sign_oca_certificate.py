# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SignOcaCertificate(models.Model):
    """
    This certificate will allow us to encrypt sensitive data
    We will not be able to decrypt it without the private key
    """

    _name = "sign.oca.certificate"
    _description = "Sign Public Certificate"
    _order = "id desc"

    name = fields.Char(required=True)
    data = fields.Char()
    active = fields.Boolean(default=True)
