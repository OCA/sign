# Copyright 2024 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Change partner_type field to partner_selection_policy.")
    query = (
        "ALTER TABLE sign_oca_role RENAME COLUMN"
        " 'partner_type' TO 'partner_selection_policy'"
    )
    cr.execute(query)
