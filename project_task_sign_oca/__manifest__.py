# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Project Task Sign Oca",
    "summary": """
        Project Task Sign Oca""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca", "project"],
    "data": [
        "views/project_task.xml",
        "views/res_config_settings.xml",
        "views/sign_oca_request.xml",
    ],
    "demo": [
        "demo/sign_oca_role.xml",
        "demo/sign_oca_template.xml",
    ],
}
