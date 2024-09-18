/** @odoo-module **/

import {registry} from "@web/core/registry";
const {Component} = owl;

export class SignerMenuView extends Component {
    /**
     * @override
     */
    setup() {
        super.setup();
    }
    /**
     * @returns {SignerMenuView}
     */
    get signerMenuView() {
        return this.props.record;
    }
}

SignerMenuView.template = "sign_oca.SignerMenuView";
registry.category("menu").add("SignerMenuView", {
    Component: SignerMenuView,
    props: {record: Object},
});
