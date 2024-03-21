odoo.define("sign_oca.sign_oca", function (require) {
    "use strict";

    const ListController = require("web.ListController");
    const FormController = require("web.FormController");

    var core = require("web.core");
    var session = require("web.session");
    var _t = core._t;

    const SignOcaControllerExtension = {
        _showSignOcaTemplateGenerateMulti: async function () {
            var sign_oca_group_user = await session.user_has_group(
                "sign_oca.sign_oca_group_user"
            );
            if (sign_oca_group_user) {
                await this._rpc({
                    model: "sign.oca.template",
                    method: "search_count",
                    args: [
                        ["|", ["model", "=", false], ["model", "=", this.modelName]],
                    ],
                }).then((templateCount) => {
                    this.showSignOcaTemplateGenerateMulti = templateCount !== 0;
                });
            } else {
                this.showSignOcaTemplateGenerateMulti = false;
            }
        },
        willStart: function () {
            return Promise.all([
                this._super.apply(this, arguments),
                this._showSignOcaTemplateGenerateMulti(),
            ]);
        },
        _getActionMenuItems: function () {
            var menuItems = this._super.apply(this, arguments);
            if (menuItems && this.showSignOcaTemplateGenerateMulti) {
                menuItems.items.other.push({
                    description: _t("Sign from template"),
                    callback: () => this._actionSignOcaTemplateGenerateMulti(),
                });
            }
            return menuItems;
        },
    };
    ListController.include(SignOcaControllerExtension);
    FormController.include(SignOcaControllerExtension);

    ListController.include({
        async _actionSignOcaTemplateGenerateMulti() {
            const state = this.model.get(this.handle);
            const resIds = await this.getSelectedIdsWithDomain();
            this.do_action("sign_oca.sign_oca_template_generate_multi_act_window", {
                additional_context: {
                    default_model: state.model,
                    active_ids: resIds,
                },
                on_close: () => {
                    this.update({}, {reload: false});
                },
            });
        },
    });
    FormController.include({
        async _actionSignOcaTemplateGenerateMulti() {
            this.do_action("sign_oca.sign_oca_template_generate_multi_act_window", {
                additional_context: {
                    default_model: this.modelName,
                    active_ids: this.model.localIdsToResIds([this.handle]),
                },
                on_close: () => {
                    this.update({}, {reload: false});
                },
            });
        },
    });
});
