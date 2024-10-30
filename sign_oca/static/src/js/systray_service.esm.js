/* @odoo-module */
import {Component, useState} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {useDiscussSystray} from "@mail/utils/common/hooks";
import {useService} from "@web/core/utils/hooks";
const systrayRegistry = registry.category("systray");
export class SignerMenuView extends Component {
    setup() {
        this.discussSystray = useDiscussSystray();
        this.orm = useService("orm");
        this.store = useState(useService("mail.store"));
        this.action = useService("action");
        this.fetchSystraySigner();
    }
    async fetchSystraySigner() {
        const groups = await this.orm.call("res.users", "sign_oca_request_user_count");
        let total = 0;
        for (const group of groups) {
            total += group.total_records || 0;
        }
        this.store.signerCounter = total;
        this.store.signerGroups = groups;
    }
    onBeforeOpen() {
        this.fetchSystraySigner();
    }
    availableViews() {
        return [
            [false, "kanban"],
            [false, "list"],
            [false, "form"],
            [false, "activity"],
        ];
    }
    onClickFilterButton(group) {
        document.body.click(); // Hack to close dropdown
        const context = {};
        const views = this.availableViews();
        var domain = [
            ["request_id.state", "=", "sent"],
            ["partner_id", "child_of", [session.partner_id]],
            ["signed_on", "=", false],
        ];
        this.action.doAction(
            {
                context,
                domain,
                name: group.name,
                res_model: "sign.oca.request.signer",
                search_view_id: [false],
                type: "ir.actions.act_window",
                views,
            },
            {
                clearBreadcrumbs: true,
            }
        );
    }
}

SignerMenuView.template = "sign_oca.SignerMenu";
SignerMenuView.components = {Dropdown, DropdownItem};
SignerMenuView.props = [];
export const systrayItem = {Component: SignerMenuView};
systrayRegistry.add("sign_oca.SignerMenuView", systrayItem, {sequence: 99});
