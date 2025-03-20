# Copyright 2025 Kencove (https://kencove.com/)
# @author: dnplkndll <kendall@donkendall.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # Check if sequence already exists
    sequence_ref = env.ref("sign_oca.sign_inalterability_sequence", False)

    if not sequence_ref:
        sequence = env["ir.sequence"].create(
            {
                "name": "Securization of Signature",
                "code": "SECUR_SIGN",
                "implementation": "no_gap",
                "prefix": "",
                "suffix": "",
                "padding": 0,
                "company_id": False,
            }
        )

        # Create XML ID for the sequence
        env["ir.model.data"].create(
            {
                "name": "sign_inalterability_sequence",
                "module": "sign_oca",
                "model": "ir.sequence",
                "res_id": sequence.id,
                "noupdate": True,
            }
        )
        sequence_ref = env.ref("sign_oca.sign_inalterability_sequence", False)
        _logger.info(
            f"{sequence_ref} record is created with ID: {sequence.id}, "
            f"with ref: sign_oca.sign_inalterability_sequence"
        )
