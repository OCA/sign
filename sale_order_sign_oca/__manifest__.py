# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Sign Oca",
    "summary": """
        KMEE""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca", "sale"],
    "data": [
        "security/sale_order_sign_oca_security.xml",
        "views/sale_order.xml",
        "views/sign_oca_request.xml",
        "views/res_config_settings.xml",
    ],
    "demo": [
        "demo/sign_oca_role.xml",
        "demo/sign_oca_template.xml",
    ],
}
