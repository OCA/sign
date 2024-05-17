/** @odoo-module **/

import {one} from "@mail/model/model_field";
import {registerModel} from "@mail/model/model_core";
import {session} from "@web/session";

registerModel({
    name: "RequestGroupView",
    recordMethods: {
        /**
         * @param {MouseEvent} ev
         */
        onClickFilterButton(ev) {
            this.requestMenuViewOwner.update({isOpen: false});
            // Fetch the data from the button otherwise fetch the ones from the parent (.o_ActivityMenuView_activityGroup).
            const data = _.extend({}, $(ev.currentTarget).data(), $(ev.target).data());
            const context = {};
            console.log(data);

            this.env.services.action.doAction(
                {
                    context,
                    name: data.model_name,
                    res_model: "sign.oca.request.signer",
                    search_view_id: [false],
                    type: "ir.actions.act_window",
                    domain: [
                        ["request_id.state", "=", "sent"],
                        ["partner_id", "child_of", [session.partner_id]],
                        ["signed_on", "=", false],
                    ],
                    views: [
                        [false, "list"],
                        [false, "form"],
                    ],
                },
                {
                    clearBreadcrumbs: true,
                }
            );
        },
    },
    fields: {
        requestGroup: one("RequestGroup", {
            identifying: true,
            inverse: "requestGroupViews",
        }),
        requestMenuViewOwner: one("SignerMenuView", {
            identifying: true,
            inverse: "requestGroupViews",
        }),
    },
});
