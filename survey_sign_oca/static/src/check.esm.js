/** @odoo-module **/
/** Copyright 2025 Kencove - Mohamed Alkobrosli
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). **/

import core from "web.core";
import {registry} from "@web/core/registry";

function patchSignOca() {
    const SignRegistry = registry.category("sign_oca");
    const textSignOca = registry.category("sign_oca").get("check");
    const patchedCheckSignOca = Object.assign({}, textSignOca);

    patchedCheckSignOca.generate = function (parent, item, signatureItem) {
        const input = $(
            core.qweb.render("sign_oca.sign_iframe_field_check", {
                item: item,
                role_id: parent.info.role_id,
            })
        )[0];
        // Apply default values immediately after creating inputs for survey related requests specifically.
        if (parent.info.partner.survey) {
            if (item.default_value === "survey") {
                const surveyValue =
                    parent.info.partner.survey?.[item.placeholder] || null;
                if (surveyValue && surveyValue !== "Skipped") {
                    if (surveyValue === true) {
                        this.change(
                            parent.info.partner[item.default_value],
                            parent,
                            item,
                            signatureItem
                        );
                        input.value = surveyValue;
                        input.checked = surveyValue;
                    }
                }
            }
        }
        signatureItem[0].addEventListener("focus_signature", () => {
            input.focus();
        });
        // Update the value of the focused input to the default
        input.addEventListener("focus", (ev) => {
            if (
                item.default_value &&
                !item.value &&
                parent.info.partner[item.default_value]
            ) {
                this.change(
                    parent.info.partner[item.default_value],
                    parent,
                    item,
                    signatureItem
                );
                ev.target.value = parent.info.partner[item.default_value];
            }
        });
        input.addEventListener("change", (ev) => {
            this.change(ev.srcElement.checked, parent, item, signatureItem);
        });
        input.addEventListener("keydown", (ev) => {
            if ((ev.keyCode || ev.which) !== 9) {
                return true;
            }
            ev.preventDefault();
            var next_items = _.filter(
                parent.info.items,
                (i) => i.tabindex > item.tabindex && i.role_id === parent.info.role_id
            ).sort((a, b) => a.tabindex - b.tabindex);
            if (next_items.length > 0) {
                ev.currentTarget.blur();
                const nextItem = next_items[0];
                if (nextItem && parent.items && parent.items[nextItem.id]) {
                    parent.items[nextItem.id].dispatchEvent(
                        new Event("focus_signature")
                    );
                } else {
                    console.warn("Missing next item or dispatch target", nextItem);
                }
            }
        });
        return input;
    };
    // Re-add the registry
    SignRegistry.remove("check");
    SignRegistry.add("check", patchedCheckSignOca);
}

const interval = setInterval(() => {
    const signOca = registry.category("sign_oca");
    const content = signOca.content;
    if (content && content.check) {
        clearInterval(interval);
        patchSignOca();
    }
}, 100);
