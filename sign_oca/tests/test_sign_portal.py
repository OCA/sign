# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.modules.module import get_module_resource
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestSign(HttpCase):
    def setUp(self):
        super().setUp()
        self.data = base64.b64encode(
            open(
                get_module_resource("sign_oca", "tests", "empty.pdf"),
                "rb",
            ).read()
        )
        self.signer = self.env["res.partner"].create({"name": "Signer"})
        self.request = self.env["sign.oca.request"].create(
            {
                "data": self.data,
                "name": "Demo template",
                "signer_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.signer.id,
                            "role_id": self.env.ref("sign_oca.sign_role_customer").id,
                        },
                    )
                ],
            }
        )
        self.item = self.request.add_item(
            {
                "role_id": self.env.ref("sign_oca.sign_role_customer").id,
                "field_id": self.env.ref("sign_oca.sign_field_name").id,
                "page": 1,
                "position_x": 10,
                "position_y": 10,
                "width": 10,
                "height": 10,
            }
        )

    def test_portal(self):
        self.authenticate("portal", "portal")
        self.request.action_send()
        self.url_open(self.request.signer_ids.access_url).raise_for_status()
        self.assertEqual(
            base64.b64decode(self.data),
            self.url_open(
                "/sign_oca/content/%s/%s"
                % (self.request.signer_ids.id, self.request.signer_ids.access_token)
            ).content,
        )
        self.assertEqual(
            self.url_open(
                "/sign_oca/info/%s/%s"
                % (self.request.signer_ids.id, self.request.signer_ids.access_token),
                data="{}",
                headers={"Content-Type": "application/json"},
            ).json()["result"]["items"][str(self.item["id"])],
            self.item,
        )
        data = {}
        for key in self.request.signer_ids.get_info()["items"]:
            val = self.request.signer_ids.get_info()["items"][key].copy()
            val["value"] = "My Name"
            data[key] = val
