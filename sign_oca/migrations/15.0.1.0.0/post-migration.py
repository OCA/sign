# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE sign_oca_role
        SET expression_partner = REPLACE(expression_partner, '${%}', '{{%}}' )
        """,
    )
