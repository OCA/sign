# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    signing_order = fields.Integer(
        default=10,
        help=(
            "Order in which this signer signs. Lower values go first. "
            "Signers with the same value sign in parallel."
        ),
    )
    signer_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("waiting", "Waiting"),
            ("sent", "Sent"),
            ("signed", "Signed"),
        ],
        default="draft",
        copy=False,
        readonly=True,
    )

    def action_sign(self, items, access_token=False, latitude=False, longitude=False):
        """Validate sequential signing order before allowing signature.

        When the request uses sequential signing mode, a signer whose state
        is still 'waiting' is not yet allowed to sign -- previous signers
        must complete first.
        """
        if (
            self.request_id.signing_mode == "sequential"
            and self.signer_state == "waiting"
        ):
            raise UserError(
                self.env._(
                    "It is not your turn to sign this document yet. "
                    "Please wait for the previous signers to complete."
                )
            )
        return super().action_sign(
            items,
            access_token=access_token,
            latitude=latitude,
            longitude=longitude,
        )
