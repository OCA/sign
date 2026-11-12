/** @odoo-module QWeb **/

import {registry} from "@web/core/registry";
import {renderToString} from "@web/core/utils/render";

const dateSignOca = {
    change: function (value, parent, item) {
        // Store the date as a locale-formatted string for PDF rendering
        if (value) {
            const dateObj = new Date(value + "T00:00:00");
            item.value = dateObj.toLocaleDateString("en-US", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
            });
        } else {
            item.value = value;
        }
        // Keep the raw ISO value for the input element
        item._raw_date = value;
        parent.checkFilledAll();
    },
    generate: function (parent, item, signatureItem) {
        var input = $(
            renderToString("sign_oca.sign_iframe_field_date", {
                item: item,
                role_id: parent.info.role_id,
            })
        )[0];
        signatureItem[0].addEventListener("focus_signature", () => {
            input.focus();
        });
        input.addEventListener("focus", (ev) => {
            // Auto-fill with today's date when focused if empty
            if (!item.value) {
                const today = new Date();
                const isoDate = today.toISOString().split("T")[0];
                ev.target.value = isoDate;
                this.change(isoDate, parent, item, signatureItem);
            }
        });
        input.addEventListener("change", (ev) => {
            this.change(ev.srcElement.value, parent, item, signatureItem);
        });
        input.addEventListener("keydown", (ev) => {
            if ((ev.keyCode || ev.which) !== 9) {
                return true;
            }
            ev.preventDefault();
            var next_items = Object.values(parent.info.items)
                .filter(
                    (i) =>
                        i.tabindex > item.tabindex && i.role_id === parent.info.role_id
                )
                .sort((a, b) => a.tabindex - b.tabindex);
            if (next_items.length > 0) {
                ev.currentTarget.blur();
                const nextItem = next_items[0];
                if (nextItem && parent.items && parent.items[nextItem.id]) {
                    parent.items[nextItem.id].dispatchEvent(
                        new Event("focus_signature")
                    );
                }
            }
        });
        return input;
    },
    check: function (item) {
        return Boolean(item.value);
    },
};
registry.category("sign_oca").add("date", dateSignOca);
export default dateSignOca;
