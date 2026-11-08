# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sign OCA Provider - Dropbox Sign",
    "summary": "Dropbox Sign provider for OCA Sign",
    "version": "17.0.1.0.0",
    "category": "Productivity/Documents",
    "license": "AGPL-3",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca_provider_base"],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "views/sign_oca_provider_views.xml",
    ],
    "maintainers": ["BernatObrador"],
    "installable": True,
    "application": False,
}
