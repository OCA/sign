# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sign Oca Sms",
    "version": "18.0.1.0.0",
    "category": "Sales/Sign",
    "summary": "Kencove Sign Customizations",
    "author": "Kencove, ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "license": "AGPL-3",
    "depends": [
        "sms",
        "sign_oca",
        "html_text",
    ],
    "data": [
        "wizards/sign_oca_generate.xml",
        "security/ir.model.access.csv",
        "data/sms_template.xml",
    ],
    "installable": True,
}
