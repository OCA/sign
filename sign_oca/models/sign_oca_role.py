# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SignOcaRole(models.Model):
    _name = "sign.oca.role"
    _description = "Sign Role"

    name = fields.Char(required=True)
    domain = fields.Char(required=True, default=[])
