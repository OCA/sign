# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sign OCA Font Support",
    "version": "16.0.1.0.0",
    "website": "https://github.com/OCA/sign",
    "author": "Kencove, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["sign_oca"],
    "external_dependencies": {
        "python": [
            "arabic-reshaper",
            "python-bidi",
            "reportlab",
        ],
    },
    "installable": True,
    "maintainers": ["Kencove"],
}
