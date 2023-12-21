# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Kencove Sign",
    "version": "14.0.1.0.0",
    "category": "Sales/Sign",
    "summary": "Kencove Sign Customizations",
    "author": "ForgeFlow",
    "website": "https://gitlab.com/kencove/odoo/addons/ken",
    "license": "AGPL-3",
    "depends": [
        "sign_oca",
        "html_text",  # in v16 not needed. tool added in Odoo core
    ],
    "data": [
        "wizards/sign_oca_generate.xml",
        "security/ir.model.access.csv",
        "data/sms_template.xml",
    ],
    "installable": True,
}
