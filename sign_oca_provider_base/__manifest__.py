# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sign OCA Provider Base",
    "summary": "Provider abstraction layer for electronic signature backends",
    "version": "17.0.1.1.0",
    "category": "Productivity/Documents",
    "license": "AGPL-3",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca"],
    "data": [
        "data/cron.xml",
        "security/ir.model.access.csv",
        "views/sign_oca_provider_views.xml",
        "views/sign_oca_request_views.xml",
        "views/menu.xml",
    ],
    "maintainers": ["BernatObrador"],
    "installable": True,
    "application": False,
}
