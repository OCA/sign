# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Crm Sign Oca",
    "summary": """CRM Sign OCA""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": [
        "sign_oca",
        "crm",
    ],
    "data": [
        "views/crm_lead_views.xml",
        "views/res_config_settings_view.xml",
        "views/sign_oca_request.xml",
    ],
    "demo": ["demo/sign_oca_role.xml", "demo/sign_oca_template.xml"],
}
