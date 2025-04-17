# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Survey Sign Oca",
    "version": "16.0.1.0.0",
    "category": "Surveys",
    "website": "https://github.com/OCA/sign",
    "author": "Kencove, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["sign_oca", "survey"],
    "data": [
        "views/survey_user_views.xml",
        "views/res_config_settings_view.xml",
        "views/sign_oca_request_views.xml",
        "views/survey_survey_views.xml",
        "views/survey_templates.xml",
        "data/sign_oca_role.xml",
    ],
    "installable": True,
    "maintainers": ["Kencove"],
}
