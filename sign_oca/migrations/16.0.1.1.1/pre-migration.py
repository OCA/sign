# Copyright 2024 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    old_column_name = "partner_type"
    new_column_name = "partner_selection_policy"

    if not openupgrade.column_exists(
        env.cr, "sign_oca_role", new_column_name
    ) and openupgrade.column_exists(env.cr, "sign_oca_role", old_column_name):
        openupgrade.rename_columns(
            env.cr,
            {
                "sign_oca_role": [
                    (
                        old_column_name,
                        new_column_name,
                    ),
                ]
            },
        )
