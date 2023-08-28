# Copyright 2022 Cyril VINH-TUNG - INVITU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Lex Persona Connector",
    "version": "14.0.1.0.0",
    "summary": "Connector to Lex Persona API",
    "sequence": 30,
    "category": "Customization",
    "author": "INVITU, " "Odoo Community Association (OCA)",
    "maintainers": ["invitu"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/sign",
    "images": [],
    "depends": [
        "base",
    ],
    "data": [
        "views/res_users_views.xml",
        "data/res_config_settings_data.xml",
    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
