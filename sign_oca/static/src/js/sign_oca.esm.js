/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {_t} from "web.core";
import {useService} from "@web/core/utils/hooks";
import {ListController} from "@web/views/list/list_controller";
import {FormController} from "@web/views/form/form_controller";

const {onWillStart} = owl;

export const patchControllerSignOca = {
    setup() {
        this._super(...arguments);
        this.userService = useService("user");
        this.orm = useService("orm");
        this.action = useService("action");
        this.showSignOcaTemplateGenerateMulti = false;
        onWillStart(async () => {
            return Promise.all([this._showSignOcaTemplateGenerateMulti()]);
        });
    },

    async _showSignOcaTemplateGenerateMulti() {
        var sign_oca_group_user = await this.userService.hasGroup(
            "sign_oca.sign_oca_group_user"
        );
        if (sign_oca_group_user) {
            await this.orm
                .call("sign.oca.template", "search_count", [
                    [["model", "=", this.props.resModel]],
                ])
                .then((templateCount) => {
                    this.showSignOcaTemplateGenerateMulti = templateCount !== 0;
                });
        }
    },

    async _actionSignOcaTemplateGenerateMulti() {
        var resIds = undefined;
        if (this.getSelectedResIds !== undefined)
            resIds = await this.getSelectedResIds();
        else resIds = this.model.root.data.id;
        this.action.doAction("sign_oca.sign_oca_template_generate_multi_act_window", {
            additionalContext: {
                model: this.props.resModel,
                active_ids: resIds,
            },
            on_close: () => {
                this.update({}, {reload: false});
            },
        });
    },

    getActionMenuItems() {
        const menuItems = this._super.apply(this, arguments);
        const otherActionItems = menuItems.other;
        if (menuItems && this.showSignOcaTemplateGenerateMulti) {
            otherActionItems.push({
                key: "sign",
                description: _t("Sign from template"),
                callback: () => this._actionSignOcaTemplateGenerateMulti(),
            });
        }
        return Object.assign({}, this.props.info.actionMenus, {
            other: otherActionItems,
        });
    },
};

patch(ListController.prototype, "web.ListController", patchControllerSignOca);
patch(FormController.prototype, "web.ListController", patchControllerSignOca);
