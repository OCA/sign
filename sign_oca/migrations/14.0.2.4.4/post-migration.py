# Copyright 2024 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Set signatory data from old format to the new one.")
    env = api.Environment(cr, SUPERUSER_ID, {})
    requests = env["sign.oca.request"].search([])
    for request in requests:
        items = request.signatory_data
        for key in items:
            item = items[key]
            if item.get("role", False):
                item["role_id"] = item["role"]
                del item["role"]
        request.write({"signatory_data": items})
