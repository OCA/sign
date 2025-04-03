/** @odoo-module **/
/** Copyright 2025 Kencove - Mohamed Alkobrosli
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). **/

import core from "web.core";
import {registry} from "@web/core/registry";

function patchSignOca() {
    const SignRegistry = registry.category("sign_oca");
    const textSignOca = registry.category("sign_oca").get("text");
    const patchedTextSignOca = Object.assign({}, textSignOca);

    function applyDefaultValue({input, parent, item, signatureItem, changeFn}) {
        if (
            item.default_value &&
            !item.value &&
            parent.info.partner[item.default_value]
        ) {
            let val = null;
            if (item.default_value === "survey") {
                const surveyValue =
                    parent.info.partner.survey?.[item.placeholder] || null;
                if (surveyValue && surveyValue !== "Skipped") {
                    val = surveyValue;
                }
            } else {
                val = parent.info.partner[item.default_value];
            }
            if (val) {
                changeFn(val, parent, item, signatureItem);
                input.value = val;
            }
        }
    }

    patchedTextSignOca.generate = function (parent, item, signatureItem) {
        const input = $(
            core.qweb.render("sign_oca.sign_iframe_field_text", {
                item,
                role_id: parent.info.role_id,
            })
        )[0];
        // Apply default values immediately after creating inputs for survey related requests specifically.
        if (parent.info.partner.survey) {
            applyDefaultValue({
                input,
                parent,
                item,
                signatureItem,
                changeFn: this.change.bind(this),
            });
        }
        signatureItem[0].addEventListener("focus_signature", () => {
            input.focus();
        });
        // Update the value of the focused input to the default
        input.addEventListener("focus", (ev) => {
            applyDefaultValue({
                input: ev.target,
                parent,
                item,
                signatureItem,
                changeFn: this.change.bind(this),
            });
        });

        input.addEventListener("change", (ev) => {
            this.change(ev.target.value, parent, item, signatureItem);
        });
        input.addEventListener("keydown", (ev) => {
            if ((ev.keyCode || ev.which) !== 9) {
                return true;
            }
            ev.preventDefault();
            const next_items = _.filter(
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
    SignRegistry.remove("text");
    SignRegistry.add("text", patchedTextSignOca);
}

const interval = setInterval(() => {
    const signOca = registry.category("sign_oca");
    const content = signOca.content;
    if (content && content.text) {
        clearInterval(interval);
        patchSignOca();
    }
}, 100);
