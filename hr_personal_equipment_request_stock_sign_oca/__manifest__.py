# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Signature for Personal Equipment Request with Stock",
    "summary": "Request signature for personal equipment with moving stock",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "PyTech SRL, Odoo Community Association (OCA)",
    "maintainers": [
        "HekkiMelody",
        "SirPyTech",
    ],
    "website": "https://github.com/OCA/sign",
    "depends": [
        "hr_personal_equipment_request_sign_oca",
        "hr_personal_equipment_stock",
    ],
    "data": [
        "reports/ppe_sign_report_template.xml",
        "views/res_config_settings_views.xml",
    ],
}
