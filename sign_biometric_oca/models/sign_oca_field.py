# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SignOcaField(models.Model):
    _inherit = "sign.oca.field"

    field_type = fields.Selection(
        selection_add=[("biometric", "Biometric")],
        ondelete={"biometric": "set default"},
    )
