# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sign OCA Sequential Signing & CC",
    "version": "18.0.1.0.0",
    "category": "Sign",
    "summary": "Sequential/ordered signing with CC recipients for OCA Sign",
    "author": "Keboola, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "license": "AGPL-3",
    "depends": ["sign_oca", "sign_oca_reminder"],
    "development_status": "Beta",
    "data": [
        "data/mail_template_data.xml",
        "views/sign_oca_request_views.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
