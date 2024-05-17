/** @odoo-module **/

import {Component} from "@odoo/owl";
import {FormRenderer} from "@web/views/form/form_renderer";
import SignOcaPdf from "./sign_oca_pdf.esm.js";
import {registry} from "@web/core/registry";

export class SignOcaPdfAction extends Component {
    init(parent, action) {
        this._super.apply(this, arguments);
        this.model =
            (action.params.res_model !== undefined && action.params.res_model) ||
            action.context.params.res_model;
        this.res_id =
            (action.params.res_id !== undefined && action.params.res_id) ||
            action.context.params.id;
    }
    async start() {
        await this._super(...arguments);
        this.component = new FormRenderer(this, SignOcaPdf, {
            model: this.model,
            res_id: this.res_id,
            updateControlPanel: this.updateControlPanel.bind(this),
            trigger: this.trigger_up.bind(this),
        });
        return this.component.mount(this.$(".o_content")[0]);
    }
    getState() {
        var result = this._super(...arguments);
        result = _.extend({}, result, {
            res_model: this.model,
            res_id: this.res_id,
        });
        return result;
    }
}
registry.category("actions").add("sign_oca", SignOcaPdfAction);
