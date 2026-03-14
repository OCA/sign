# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sign_oca_reminder_enabled = fields.Boolean(
        related="company_id.sign_oca_reminder_enabled",
        readonly=False,
    )
    sign_oca_reminder_interval_days = fields.Integer(
        related="company_id.sign_oca_reminder_interval_days",
        readonly=False,
    )
    sign_oca_validity_days = fields.Integer(
        related="company_id.sign_oca_validity_days",
        readonly=False,
    )
