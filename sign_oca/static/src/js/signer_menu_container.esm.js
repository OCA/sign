/** @odoo-module **/

import {registry} from "@web/core/registry";
/* eslint-disable */
import SignerMenuView from "./signer_menu_view.esm";
/* eslint-enable */

const {Component} = owl;

export class SignerMenuContainer extends Component {
    /**
     * @override
     */
    setup() {
        super.setup();
        this.env.services.messaging.modelManager.messagingCreatedPromise.then(() => {
            this.signerMenuView =
                this.env.services.messaging.modelManager.messaging.models.SignerMenuView.insert();
            this.render();
        });
    }
}

SignerMenuContainer.template = "sign_oca.SignerMenuContainer";
registry.category("menu").add("SignerMenuContainer", {
    Component: SignerMenuView,
    props: {record: Object},
});
