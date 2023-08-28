# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    lexpersona_ref = fields.Char(string="Lex Persona User ID", company_dependent=True)
    lexpersona_token = fields.Char(
        string="Lex Persona User API Token", company_dependent=True
    )
