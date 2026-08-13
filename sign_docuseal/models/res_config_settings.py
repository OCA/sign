# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    docuseal_base_url = fields.Char(
        string="DocuSeal URL",
        config_parameter="docuseal.base_url",
        help="Base URL of the DocuSeal instance, without a trailing slash.",
    )
    docuseal_api_key = fields.Char(
        string="API Key",
        config_parameter="docuseal.api_key",
        help="Value sent in the X-Auth-Token header of every API call.",
    )
    docuseal_webhook_secret = fields.Char(
        string="Webhook Secret",
        config_parameter="docuseal.webhook_secret",
        help="Shared secret DocuSeal must send back in the "
        "X-Odoo-Webhook-Secret header when calling /docuseal/webhook.",
    )
