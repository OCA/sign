# Copyright 2025 Kencove - Mohamed Alkobrosli  <https://kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE sign_oca_request
        SET state = CASE
            WHEN state = 'sent' THEN '0_sent'
            WHEN state = 'draft' THEN '1_draft'
            WHEN state = 'signed' THEN '2_signed'
            WHEN state = 'cancel' THEN '3_cancel'
            ELSE state
        END
        """,
    )
