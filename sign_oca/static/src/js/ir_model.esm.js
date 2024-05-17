/** @odoo-module */

import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";


export class IRModelRequest extends Component {
    setup() {
        super.setup();
    }
}
IRModelRequest.props = {
    ...standardWidgetProps,
};
IRModelRequest.template = "sign_oca.IrModelRequest";

export const irModelRequest = {
    component: IRModelRequest,
};
registry.category("view_widgets").add("sign_oca_ir_model_request", irModelRequest);
