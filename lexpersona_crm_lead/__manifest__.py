# Copyright 2022 Cyril VINH-TUNG - INVITU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Lex Persona CRM Lead",
    "version": "14.0.1.0.0",
    "summary": "Add Lex Persona to CRM Leads",
    "sequence": 30,
    "category": "Customization",
    "author": "INVITU, " "Odoo Community Association (OCA)",
    "maintainers": ["invitu"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/sign",
    "images": [],
    "depends": [
        "base",
        "crm",
        "lexpersona_base",
    ],
    "data": [
        "wizard/wizard_create_workflow_views.xml",
    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": False,
    "auto_install": True,
}
