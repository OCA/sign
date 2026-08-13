# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Hr Personal Equipment Request Sign Oca",
    "summary": "Create a Signature Request for Personal Equipment Request",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "PyTech SRL, Odoo Community Association (OCA)",
    "maintainers": [
        "HekkiMelody",
        "SirPyTech",
    ],
    "website": "https://github.com/OCA/sign",
    "depends": [
        "hr_employee_ppe",
        "hr_personal_equipment_request",
        "sign_oca",
    ],
    "data": [
        "data/sign_oca_role.xml",
        "data/sign_oca_template.xml",
        "reports/ppe_sign_report.xml",
        "reports/ppe_sign_report_template.xml",
        "views/hr_personal_equipment_request.xml",
        "views/res_config_settings.xml",
        "views/sign_oca_request.xml",
    ],
}
