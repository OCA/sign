# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sign Oca",
    "summary": """
        Allow to sign documents inside Odoo CE""",
    "version": "14.0.2.3.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["web_editor", "portal", "base_sparse_field"],
    "data": [
        "security/security.xml",
        "views/menu.xml",
        "data/data.xml",
        "wizards/sign_oca_template_generate.xml",
        "wizards/sign_oca_template_generate_multi.xml",
        "views/res_partner_views.xml",
        "views/sign_oca_request_log.xml",
        "views/sign_oca_request.xml",
        "security/ir.model.access.csv",
        "views/sign_oca_field.xml",
        "views/sign_oca_role.xml",
        "views/sign_oca_template.xml",
        "templates/assets.xml",
    ],
    "demo": [
        "demo/sign_oca_template.xml",
    ],
    "qweb": [
        "static/src/components/sign_oca_pdf_common/sign_oca_pdf_common.xml",
        "static/src/components/sign_oca_configure/sign_oca_configure.xml",
        "static/src/components/sign_oca_pdf/sign_oca_pdf.xml",
        "static/src/components/sign_oca_pdf_portal/sign_oca_pdf_portal.xml",
        "static/src/elements/elements.xml",
        "static/src/elements/systray.xml",
    ],
    "maintainers": ["etobella"],
}
