odoo.define(
    "sign_oca/static/src/components/sign_oca_pdf_common/sign_oca_pdf_common_action.js",
    function (require) {
        "use strict";

        const {ComponentWrapper} = require("web.OwlCompatibility");
        const AbstractAction = require("web.AbstractAction");
        const core = require("web.core");
        const SignOcaPdfCommon = require("sign_oca/static/src/components/sign_oca_pdf_common/sign_oca_pdf_common.js");

        const SignOcaPdfCommonAction = AbstractAction.extend({
            hasControlPanel: true,
            init: function (parent, action) {
                this._super.apply(this, arguments);
                this.model =
                    (action.params.res_model !== undefined &&
                        action.params.res_model) ||
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

        return {
            SignOcaPdfCommonAction,
        };
    }
);
