/** @odoo-module **/

import {SignerMenuContainer} from "./signer_menu_container.esm";

import {registry} from "@web/core/registry";

const systrayRegistry = registry.category("systray");

export const systrayService = {
    start() {
        systrayRegistry.add(
            "sign_oca.SignerMenu",
            {Component: SignerMenuContainer},
            {sequence: 99}
        );
    },
};
