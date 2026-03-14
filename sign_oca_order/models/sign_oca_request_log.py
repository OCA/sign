# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SignOcaRequestLog(models.Model):
    _inherit = "sign.oca.request.log"

    action = fields.Selection(
        selection_add=[
            ("cc_notify", "CC Notification"),
            ("advance_step", "Advance Step"),
        ],
        ondelete={
            "cc_notify": "cascade",
            "advance_step": "cascade",
        },
    )
