# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sign_oca_reminder_enabled = fields.Boolean(
        string="Enable Automatic Reminders",
        default=False,
        help="Enable automatic email reminders for pending sign requests.",
    )
    sign_oca_reminder_interval_days = fields.Integer(
        string="Reminder Interval (Days)",
        default=3,
        help="Number of days between automatic reminders for pending sign requests.",
    )
    sign_oca_validity_days = fields.Integer(
        string="Default Validity (Days)",
        default=0,
        help="Default number of days before a sign request expires. "
        "0 means no expiration.",
    )
