# Copyright 2022 Cyril VINH-TUNG - INVITU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Lex Persona Base",
    "version": "14.0.1.0.0",
    "summary": "Base to Lex Persona API",
    "sequence": 30,
    "category": "Customization",
    "author": "INVITU, " "Odoo Community Association (OCA)",
    "maintainers": ["invitu"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/sign",
    "images": [],
    "depends": [
        "base",
        "mail",
        "partner_firstname",
        "partner_contact_nationality",
        "lexpersona_connector",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/lexpersona_base_data.xml",
        "data/cron.xml",
        "views/ir_attachment_views.xml",
        "wizard/wizard_create_workflow_views.xml",
    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
