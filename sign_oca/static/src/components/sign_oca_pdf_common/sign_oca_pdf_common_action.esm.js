/** @odoo-module **/

import AbstractAction from "web.AbstractAction";
import {ComponentWrapper} from "web.OwlCompatibility";
import SignOcaPdfCommon from "./sign_oca_pdf_common.esm.js";
import core from "web.core";

export const SignOcaPdfCommonAction = AbstractAction.extend({
    hasControlPanel: true,
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.model =
            (action.params.res_model !== undefined && action.params.res_model) ||
            action.context.params.res_model;
        this.res_id =
            (action.params.res_id !== undefined && action.params.res_id) ||
            action.context.params.id;
    },
    async start() {
        await this._super(...arguments);
        this.component = new ComponentWrapper(this, SignOcaPdfCommon, {
            model: this.model,
            res_id: this.res_id,
        });
        this.$el.addClass("o_sign_oca_action");
        return this.component.mount(this.$(".o_content")[0]);
    },
    getState: function () {
        var result = this._super(...arguments);
        result = _.extend({}, result, {
            res_model: this.model,
            res_id: this.res_id,
        });
        return result;
    },
});
core.action_registry.add("sign_oca_preview", SignOcaPdfCommonAction);
