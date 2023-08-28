# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    lexpersona_wkf = fields.Char(string="Workflow")
