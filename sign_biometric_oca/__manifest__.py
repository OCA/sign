# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sign Biometric Oca",
    "summary": """
        Add a new widget in order to store biometric information""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": [
        "sign_oca",
    ],
    "data": [
        "data/data.xml",
    ],
    "demo": [],
    "external_dependencies": {"python": ["svglib"]},
    "assets": {
        "web.assets_backend": [
            "sign_biometric_oca/static/src/lib/perfect-freehand.esm.js",
            "sign_biometric_oca/static/src/components/biometric_signature_dialog.xml",
            "sign_biometric_oca/static/src/components/biometric_signature_dialog.esm.js",
            "sign_biometric_oca/static/src/components/biometric.esm.js",
            "sign_biometric_oca/static/src/components/biometric.scss",
        ],
        "web.assets_frontend": [
            "sign_biometric_oca/static/src/lib/perfect-freehand.esm.js",
            "sign_biometric_oca/static/src/components/biometric_signature_dialog.xml",
            "sign_biometric_oca/static/src/components/biometric_signature_dialog.esm.js",
            "sign_biometric_oca/static/src/components/biometric.esm.js",
            "sign_biometric_oca/static/src/components/biometric.scss",
        ],
    },
}
