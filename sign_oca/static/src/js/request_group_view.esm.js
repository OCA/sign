/* @odoo-module */

import {Component, onWillUpdateProps, useEffect, useRef, useState} from "@odoo/owl";


/**
 * @typedef {Object} Props
 * @property {number} threadId
 * @property {string} threadModel
 * @extends {Component<Props, Env>}
 */
export class RequestGroupView extends Component {
    static template = "sign_oca.RequestGroupView";
    static components = {};
    static props = [];

    setup() {}

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
    }
}
