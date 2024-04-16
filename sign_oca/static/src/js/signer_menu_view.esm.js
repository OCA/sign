/** @odoo-module **/

import {registerMessagingComponent} from "@mail/utils/messaging_component";
import {useComponentToModel} from "@mail/component_hooks/use_component_to_model";

const {Component} = owl;

export class SignerMenuView extends Component {
    /**
     * @override
     */
    setup() {
        super.setup();
        useComponentToModel({fieldName: "component"});
    }
    /**
     * @returns {SignerMenuView}
     */
    get signerMenuView() {
        return this.props.record;
    }
}

Object.assign(SignerMenuView, {
    props: {record: Object},
    template: "sign_oca.SignerMenuView",
});

registerMessagingComponent(SignerMenuView);
