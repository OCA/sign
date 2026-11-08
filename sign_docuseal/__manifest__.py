# Copyright 2026 PopSolutions
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Sign DocuSeal",
    "summary": "Send documents for electronic signature through DocuSeal and "
    "track them from Odoo",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/docuseal_submission_views.xml",
        "views/res_config_settings_views.xml",
        "views/signing_page_templates.xml",
    ],
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["marcos-mendez"],
}
