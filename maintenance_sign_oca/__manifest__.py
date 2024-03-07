# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Maintenance Sign Oca",
    "version": "14.0.1.0.0",
    "category": "Maintenance",
    "website": "https://github.com/OCA/sign",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["sign_oca", "base_maintenance_config"],
    "data": [
        "views/maintenance_equipment_views.xml",
        "views/res_config_settings_view.xml",
        "views/sign_oca_request_views.xml",
    ],
    "demo": [
        "demo/sign_oca_role.xml",
        "demo/sign_oca_template.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
