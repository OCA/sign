# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sign OCA Reminders & Expiration",
    "version": "18.0.1.0.0",
    "category": "Sign",
    "summary": "Automatic reminders, manual resend, and expiration for sign requests",
    "author": "Keboola, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "license": "AGPL-3",
    "depends": ["sign_oca"],
    "development_status": "Beta",
    "data": [
        "data/cron_data.xml",
        "data/mail_template_data.xml",
        "views/sign_oca_request_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
